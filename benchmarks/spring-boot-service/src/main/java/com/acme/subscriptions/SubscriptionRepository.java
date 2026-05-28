package com.acme.subscriptions;

import java.util.Optional;

public interface SubscriptionRepository {
    Optional<Subscription> findByAccountId(String accountId);

    Subscription save(Subscription subscription);
}
