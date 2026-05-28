package com.acme.subscriptions;

public interface BillingClient {
    boolean charge(String accountId, int amountCents);
}
