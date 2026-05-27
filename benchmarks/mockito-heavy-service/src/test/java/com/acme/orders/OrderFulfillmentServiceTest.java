package com.acme.orders;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class OrderFulfillmentServiceTest {
    @Mock
    InventoryClient inventoryClient;

    @Mock
    ShipmentRepository shipmentRepository;

    @Mock
    NotificationGateway notificationGateway;

    @InjectMocks
    OrderFulfillmentService service;

    @Test
    void shipsOrderWhenInventoryCanBeReserved() {
        Order order = new Order("order-1", "SKU-1", 2, "buyer@example.com", false);
        when(inventoryClient.reserve("SKU-1", 2)).thenReturn(true);
        when(shipmentRepository.createShipment("order-1", "SKU-1", 2, false)).thenReturn("ship-1");

        FulfillmentResult result = service.fulfill(order);

        assertEquals(Status.SHIPPED, result.status());
        assertEquals("ship-1", result.shipmentId());
        verify(notificationGateway).sendConfirmation("buyer@example.com", "order-1");
    }
}
