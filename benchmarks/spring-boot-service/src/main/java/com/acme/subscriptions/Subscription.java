package com.acme.subscriptions;

public record Subscription(
        String accountId,
        PlanType planType,
        boolean active,
        boolean trialUsed) {
}
