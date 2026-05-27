package com.acme.billing;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.Objects;

public class InvoiceCalculator {
    private static final BigDecimal TAX_RATE = new BigDecimal("0.0825");

    public InvoiceSummary summarize(List<LineItem> items, CustomerType customerType) {
        if (items == null || items.isEmpty()) {
            return new InvoiceSummary(money(BigDecimal.ZERO), money(BigDecimal.ZERO), money(BigDecimal.ZERO), money(BigDecimal.ZERO));
        }

        BigDecimal subtotal = items.stream()
                .map(this::lineTotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        BigDecimal discount = discountFor(subtotal, customerType);
        BigDecimal taxable = subtotal.subtract(discount);
        BigDecimal tax = taxable.multiply(TAX_RATE);
        return new InvoiceSummary(money(subtotal), money(discount), money(tax), money(subtotal.subtract(discount).add(tax)));
    }

    BigDecimal lineTotal(LineItem item) {
        Objects.requireNonNull(item, "item");
        if (item.quantity() <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
        if (item.unitPrice().signum() < 0) {
            throw new IllegalArgumentException("unitPrice must not be negative");
        }
        return item.unitPrice().multiply(BigDecimal.valueOf(item.quantity()));
    }

    private BigDecimal discountFor(BigDecimal subtotal, CustomerType customerType) {
        if (customerType == CustomerType.ENTERPRISE) {
            return subtotal.multiply(new BigDecimal("0.15"));
        }
        if (customerType == CustomerType.NON_PROFIT) {
            return subtotal.multiply(new BigDecimal("0.10"));
        }
        if (subtotal.compareTo(new BigDecimal("250.00")) >= 0) {
            return subtotal.multiply(new BigDecimal("0.05"));
        }
        return BigDecimal.ZERO;
    }

    private BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }
}
