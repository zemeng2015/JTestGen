package com.acme.subscriptions;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class SubscriptionRenewalServiceTest {
    @Mock
    SubscriptionRepository subscriptionRepository;

    @Mock
    BillingClient billingClient;

    @InjectMocks
    SubscriptionRenewalService service;

    @Test
    void renewsActiveProSubscriptionWhenChargeSucceeds() {
        Subscription subscription = new Subscription("acct-1", PlanType.PRO, true, true);
        when(subscriptionRepository.findByAccountId("acct-1")).thenReturn(Optional.of(subscription));
        when(billingClient.charge("acct-1", 2900)).thenReturn(true);

        RenewalResult result = service.renew("acct-1");

        assertEquals(RenewalStatus.RENEWED, result.status());
        assertEquals("renewed", result.message());
        verify(subscriptionRepository).save(subscription);
    }
}
