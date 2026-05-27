package com.acme.orders;

public interface NotificationGateway {
    void sendConfirmation(String customerEmail, String orderId);

    void sendBackorderNotice(String customerEmail, String sku);
}
