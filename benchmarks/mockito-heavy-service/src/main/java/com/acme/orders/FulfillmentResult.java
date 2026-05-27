package com.acme.orders;

public record FulfillmentResult(Status status, String orderId, String shipmentId, String reason) {
    public static FulfillmentResult shipped(String orderId, String shipmentId) {
        return new FulfillmentResult(Status.SHIPPED, orderId, shipmentId, null);
    }

    public static FulfillmentResult backordered(String orderId) {
        return new FulfillmentResult(Status.BACKORDERED, orderId, null, null);
    }

    public static FulfillmentResult rejected(String reason) {
        return new FulfillmentResult(Status.REJECTED, null, null, reason);
    }
}
