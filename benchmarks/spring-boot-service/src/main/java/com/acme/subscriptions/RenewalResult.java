package com.acme.subscriptions;

public record RenewalResult(RenewalStatus status, String accountId, String message) {
    public static RenewalResult renewed(String accountId) {
        return new RenewalResult(RenewalStatus.RENEWED, accountId, "renewed");
    }

    public static RenewalResult skipped(String accountId, String message) {
        return new RenewalResult(RenewalStatus.SKIPPED, accountId, message);
    }

    public static RenewalResult failed(String accountId, String message) {
        return new RenewalResult(RenewalStatus.FAILED, accountId, message);
    }
}
