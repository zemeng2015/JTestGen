package com.acme.orders;

import java.util.Objects;

public class OrderFulfillmentService {
    private final InventoryClient inventoryClient;
    private final ShipmentRepository shipmentRepository;
    private final NotificationGateway notificationGateway;

    public OrderFulfillmentService(
            InventoryClient inventoryClient,
            ShipmentRepository shipmentRepository,
            NotificationGateway notificationGateway) {
        this.inventoryClient = Objects.requireNonNull(inventoryClient, "inventoryClient");
        this.shipmentRepository = Objects.requireNonNull(shipmentRepository, "shipmentRepository");
        this.notificationGateway = Objects.requireNonNull(notificationGateway, "notificationGateway");
    }

    public FulfillmentResult fulfill(Order order) {
        if (order == null) {
            return FulfillmentResult.rejected("order is required");
        }
        if (order.quantity() <= 0) {
            return FulfillmentResult.rejected("quantity must be positive");
        }
        if (order.customerEmail() == null || order.customerEmail().isBlank()) {
            return FulfillmentResult.rejected("customer email is required");
        }

        boolean reserved = inventoryClient.reserve(order.sku(), order.quantity());
        if (!reserved) {
            notificationGateway.sendBackorderNotice(order.customerEmail(), order.sku());
            return FulfillmentResult.backordered(order.id());
        }

        try {
            String shipmentId = shipmentRepository.createShipment(order.id(), order.sku(), order.quantity(), order.expedited());
            notificationGateway.sendConfirmation(order.customerEmail(), order.id());
            return FulfillmentResult.shipped(order.id(), shipmentId);
        } catch (RuntimeException ex) {
            inventoryClient.release(order.sku(), order.quantity());
            return FulfillmentResult.rejected("shipment failed: " + ex.getMessage());
        }
    }
}
