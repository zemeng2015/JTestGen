package com.acme.subscriptions;

import java.util.Objects;

import org.springframework.stereotype.Service;

@Service
public class SubscriptionRenewalService {
    private final SubscriptionRepository subscriptionRepository;
    private final BillingClient billingClient;

    public SubscriptionRenewalService(SubscriptionRepository subscriptionRepository, BillingClient billingClient) {
        this.subscriptionRepository = Objects.requireNonNull(subscriptionRepository, "subscriptionRepository");
        this.billingClient = Objects.requireNonNull(billingClient, "billingClient");
    }

    public RenewalResult renew(String accountId) {
        if (accountId == null || accountId.isBlank()) {
            return RenewalResult.failed(accountId, "account id is required");
        }

        return subscriptionRepository.findByAccountId(accountId)
                .map(this::renewExisting)
                .orElseGet(() -> RenewalResult.failed(accountId, "subscription not found"));
    }

    private RenewalResult renewExisting(Subscription subscription) {
        if (!subscription.active()) {
            return RenewalResult.skipped(subscription.accountId(), "subscription is inactive");
        }
        if (subscription.planType() == PlanType.BASIC && !subscription.trialUsed()) {
            subscriptionRepository.save(new Subscription(subscription.accountId(), subscription.planType(), true, true));
            return RenewalResult.skipped(subscription.accountId(), "trial month applied");
        }

        int amount = amountFor(subscription.planType());
        boolean charged = billingClient.charge(subscription.accountId(), amount);
        if (!charged) {
            return RenewalResult.failed(subscription.accountId(), "payment declined");
        }
        subscriptionRepository.save(subscription);
        return RenewalResult.renewed(subscription.accountId());
    }

    private int amountFor(PlanType planType) {
        return switch (planType) {
            case BASIC -> 900;
            case PRO -> 2900;
            case ENTERPRISE -> 9900;
        };
    }
}
