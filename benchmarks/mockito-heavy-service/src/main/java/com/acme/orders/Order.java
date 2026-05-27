package com.acme.orders;

public record Order(
        String id,
        String sku,
        int quantity,
        String customerEmail,
        boolean expedited) {
}
