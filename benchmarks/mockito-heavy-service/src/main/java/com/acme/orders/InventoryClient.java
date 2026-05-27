package com.acme.orders;

public interface InventoryClient {
    boolean reserve(String sku, int quantity);

    void release(String sku, int quantity);
}
