package com.acme.orders;

public interface ShipmentRepository {
    String createShipment(String orderId, String sku, int quantity, boolean expedited);
}
