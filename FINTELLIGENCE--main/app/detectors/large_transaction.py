# import pandas as pd
# from scipy.stats import zscore
# from app.models.transaction import Transaction


# MIN_AMOUNT_THRESHOLD = 50000
# MULTIPLIER_THRESHOLD = 3.0


# def detect_large_transaction(case_id: str):
#     transactions = (
#         Transaction.query
#         .filter_by(case_id=case_id, is_failed=False)
#         .order_by(Transaction.date)
#         .all()
#     )

#     if not transactions:
#         return []

#     df = pd.DataFrame([
#         {
#             "txn_id": t.id,
#             "sender_account": t.sender_account,
#             "receiver_account": t.receiver_account,
#             "amount": float(t.amount),
#             "date": pd.to_datetime(t.date),
#             "type": t.type
#         }
#         for t in transactions
#     ])

#     if df.empty:
#         return []

#     df = df.sort_values(["type", "date"])

#     # --------------------------------------------------
#     # Historical rolling average (EXCLUDES current txn)
#     # --------------------------------------------------
#     df["rolling_avg"] = (
#         df.groupby("type")["amount"]
#         .transform(
#             lambda x: (
#                 x.shift(1)
#                  .rolling(window=20, min_periods=1)
#                  .mean()
#             )
#         )
#     )

#     # --------------------------------------------------
#     # Account-wise z-score
#     # --------------------------------------------------
#     df["zscore"] = (
#         df.groupby("type")["amount"]
#         .transform(
#             lambda x: pd.Series(
#                 zscore(x, nan_policy="omit"),
#                 index=x.index
#             )
#         )
#     )

#     df["zscore"] = df["zscore"].fillna(0)

#     # --------------------------------------------------
#     # Multiplier calculation
#     # --------------------------------------------------
#     df["multiplier"] = df["amount"] / df["rolling_avg"]

#     # Remove rows without historical baseline
#     df = df[df["rolling_avg"].notna()]

#     # --------------------------------------------------
#     # Detection criteria
#     # --------------------------------------------------
#     flagged = df[
#         (df["amount"] >= MIN_AMOUNT_THRESHOLD)
#         &
#         (df["multiplier"] >= MULTIPLIER_THRESHOLD)
#     ].copy()

#     if flagged.empty:
#         return []

#     # --------------------------------------------------
#     # Fraud score
#     # --------------------------------------------------
#     flagged["risk_score"] = flagged.apply(
#         lambda row: min(
#             100,
#             int(
#                 (row["multiplier"] * 15)
#                 +
#                 (max(row["zscore"], 0) * 10)
#             )
#         ),
#         axis=1
#     )

#     # Highest risk first
#     flagged = flagged.sort_values(
#         by=["risk_score", "multiplier", "zscore"],
#         ascending=False
#     )

#     results = []

#     for _, row in flagged.iterrows():

#         multiplier = float(row["multiplier"])
#         z_score_val = float(row["zscore"])

#         if multiplier >= 8:
#             severity = "critical"
#         elif multiplier >= 5:
#             severity = "high"
#         else:
#             severity = "medium"

#         results.append({
#             "detector": "LargeTransaction",
#             "triggered": True,
#             "score": int(row["risk_score"]),
#             "reason": (
#                 f"₹{row['amount']:,.2f} is "
#                 f"{multiplier:.2f}x the historical average "
#                 f"of ₹{row['rolling_avg']:,.2f}. "
#                 f"Z-score: {z_score_val:.2f}"
#             ),
#             "severity": severity,
#             "transactions_involved": [row["txn_id"]],
#             "metadata": {
#                 "amount": float(row["amount"]),
#                 "rolling_avg": float(row["rolling_avg"]),
#                 "multiplier": round(multiplier, 2),
#                 "zscore": round(z_score_val, 2)
#             }
#         })

#     return results

import pandas as pd
from scipy.stats import zscore
from app.models.transaction import Transaction


from app.models.statement import Statement

# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_AMOUNT_THRESHOLD = 50000
MULTIPLIER_THRESHOLD = 3.0
ROLLING_WINDOW = 20


# ============================================================================
# DETECTOR
# ============================================================================

def detect_large_transaction(case_id: str, statement_id: str = None):

    query = (
        Transaction.query
        .join(Statement)
        .filter(Transaction.case_id == case_id, Transaction.is_failed == False)
    )
    
    if statement_id:
        query = query.filter(Transaction.statement_id == statement_id)

    transactions = query.order_by(Transaction.date).all()

    if not transactions:
        return []

    # ========================================================================
    # BUILD DATAFRAME
    # ========================================================================

    df = pd.DataFrame([
        {
            "txn_id": t.id,
            "sender_account": t.sender_account,
            "receiver_account": t.receiver_account,
            "amount": abs(float(t.amount or 0)),
            "date": pd.to_datetime(t.date),
            "type": getattr(t, "type", "UNKNOWN")
        }
        for t in transactions
    ])

    if df.empty:
        return []

    # Normalize transaction type
    df["type"] = (
        df["type"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    df = df.sort_values(["type", "date"])

    # ========================================================================
    # HISTORICAL ROLLING AVERAGE (EXCLUDING CURRENT TXN)
    # ========================================================================

    df["rolling_avg"] = (
        df.groupby("type")["amount"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=ROLLING_WINDOW,
                    min_periods=1
                )
                .mean()
            )
        )
    )

    # For first transactions, use dataset median
    median_amount = max(df["amount"].median(), 1)

    df["rolling_avg"] = (
        df["rolling_avg"]
        .fillna(median_amount)
        .replace(0, 1)
    )

    # ========================================================================
    # Z-SCORE CALCULATION
    # ========================================================================

    df["zscore"] = (
        df.groupby("type")["amount"]
        .transform(
            lambda x: pd.Series(
                zscore(x, nan_policy="omit"),
                index=x.index
            )
        )
    )

    df["zscore"] = df["zscore"].fillna(0)

    # ========================================================================
    # MULTIPLIER AGAINST HISTORICAL BASELINE
    # ========================================================================

    df["multiplier"] = (
        df["amount"] / df["rolling_avg"]
    )

    # ========================================================================
    # DETECTION RULES
    # ========================================================================

    flagged = df[
        (df["amount"] >= MIN_AMOUNT_THRESHOLD)
        &
        (df["multiplier"] >= MULTIPLIER_THRESHOLD)
    ].copy()

    if flagged.empty:
        return []

    # ========================================================================
    # RISK SCORING
    # ========================================================================

    flagged["risk_score"] = flagged.apply(
        lambda row: min(
            100,
            int(
                (row["multiplier"] * 15)
                +
                (max(row["zscore"], 0) * 10)
            )
        ),
        axis=1
    )

    # Highest-risk transactions first
    flagged = flagged.sort_values(
        by=["risk_score", "multiplier", "zscore"],
        ascending=False
    )

    # ========================================================================
    # OUTPUT
    # ========================================================================

    results = []

    for _, row in flagged.iterrows():

        multiplier = float(row["multiplier"])
        z_score_val = float(row["zscore"])

        if multiplier >= 8:
            severity = "critical"
        elif multiplier >= 5:
            severity = "high"
        else:
            severity = "medium"

        results.append({
            "detector": "LargeTransaction",
            "triggered": True,
            "score": int(row["risk_score"]),
            "reason": (
                f"₹{row['amount']:,.2f} is "
                f"{multiplier:.2f}x the historical average "
                f"of ₹{row['rolling_avg']:,.2f}. "
                f"Z-score: {z_score_val:.2f}"
            ),
            "severity": severity,
            "transactions_involved": [
                row["txn_id"]
            ],
            "metadata": {
                "amount":
                    float(row["amount"]),
                "rolling_avg":
                    float(row["rolling_avg"]),
                "multiplier":
                    round(multiplier, 2),
                "zscore":
                    round(z_score_val, 2),
                "transaction_type":
                    row["type"]
            }
        })

    return results