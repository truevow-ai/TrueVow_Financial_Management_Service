# ADDENDUM B — Reconciliation Matching Suggestions (MVP Algorithm)

**Date:** January 25, 2026  
**Status:** Required for MVP

If you don't implement suggestions, reconciliation becomes a manual swamp.

---

## B1) Matching Candidate Scoring

Given a bank transaction T, compute candidates from:
- AR receipts (Treasury settlements / billing payment refs)
- AP payments
- payroll payment batches
- transfers / FX conversions

### Score candidates:
- **Amount match (exact):** +60
- **Amount match (within tolerance, e.g., 0.01):** +40
- **Date proximity (<= 1 day):** +20, (<=3 days): +10
- **Reference match (payout_id/invoice_id substring):** +30
- **Counterparty fuzzy match (vendor/customer name):** +15

### Auto-match rules:
- Only auto-suggest top 3 candidates.
- Auto-match only if:
  - score >= 85 AND not ambiguous (gap >= 15 vs second best)

---

## B2) API Endpoint

- `POST /api/v1/fm/reconciliations/{rec_id}/suggest-matches`

### Input:
```json
{
  "bank_transaction_ids": ["uuid1", "uuid2", ...]
}
```

### Output:
```json
{
  "suggestions": [
    {
      "bank_transaction_id": "uuid1",
      "candidates": [
        {
          "match_type": "AR_RECEIPT",
          "match_id": "uuid",
          "match_object": {
            "type": "ar_payment",
            "id": "uuid",
            "invoice_number": "INV-123",
            "customer_name": "Acme Corp"
          },
          "score": 95,
          "reasons": [
            "Exact amount match",
            "Date within 1 day",
            "Reference match"
          ],
          "recommended_action": "AUTO_MATCH"
        },
        {
          "match_type": "AP_PAYMENT",
          "match_id": "uuid",
          "score": 45,
          "recommended_action": "MANUAL_REVIEW"
        }
      ]
    }
  ]
}
```

### UI:
- show suggestions inline in grid
- one-click accept suggestion

---

**END OF ADDENDUM B**
