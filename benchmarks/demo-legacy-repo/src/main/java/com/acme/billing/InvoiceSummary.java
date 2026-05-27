package com.acme.billing;

import java.math.BigDecimal;

public record InvoiceSummary(
        BigDecimal subtotal,
        BigDecimal discount,
        BigDecimal tax,
        BigDecimal total) {
}
