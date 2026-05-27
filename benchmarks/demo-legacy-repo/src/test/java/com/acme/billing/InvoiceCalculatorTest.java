package com.acme.billing;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.math.BigDecimal;
import java.util.List;

import org.junit.jupiter.api.Test;

class InvoiceCalculatorTest {
    private final InvoiceCalculator calculator = new InvoiceCalculator();

    @Test
    void summarizesStandardSmallInvoice() {
        InvoiceSummary summary = calculator.summarize(
                List.of(new LineItem("A-100", 2, new BigDecimal("12.00"))),
                CustomerType.STANDARD);

        assertEquals(new BigDecimal("24.00"), summary.subtotal());
        assertEquals(new BigDecimal("0.00"), summary.discount());
        assertEquals(new BigDecimal("1.98"), summary.tax());
        assertEquals(new BigDecimal("25.98"), summary.total());
    }
}
