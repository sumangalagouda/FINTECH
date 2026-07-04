# import pandas as pd
# from app.models.transaction import Transaction

# def detect_velocity(case_id: str):
#     transactions = (
#         Transaction.query
#         .filter_by(case_id=case_id, is_failed=False)
#         .order_by(Transaction.date)
#         .all()
#     )

#     if len(transactions) < 2:
#         return {
#             "detector": "TransactionVelocity",
#             "triggered": False,
#             "score": 0,
#             "reason": "Not enough transactions for velocity analysis.",
#             "transactions_involved": [],
#             "severity": "none",
#             "metadata": {}
#         }

#     df = pd.DataFrame([
#         {
#             "txn_id": t.id,
#             "amount": float(t.amount),
#             "type": t.type,
#             "date": pd.to_datetime(t.date)
#         }
#         for t in transactions
#     ])

#     results = []
    
#     df = df.sort_values("date").reset_index(drop=True)
    
#     credits = df[df["type"] == "credit"]
    
#     for idx, credit in credits.iterrows():
#         mask = (df["type"] == "debit") & (df["date"] >= credit["date"]) & ((df["date"] - credit["date"]).dt.total_seconds() <= 3600)
#         subsequent_debits = df[mask]
        
#         for d_idx, debit in subsequent_debits.iterrows():
#             amt_in = credit["amount"]
#             amt_out = debit["amount"]
            
#             diff_pct = abs(amt_in - amt_out) / amt_in if amt_in > 0 else 0
            
#             if diff_pct <= 0.05:
#                 time_diff_minutes = int((debit["date"] - credit["date"]).total_seconds() / 60)
#                 forwarded_pct = (amt_out / amt_in) * 100 if amt_in > 0 else 0
                
#                 score = 40
#                 if time_diff_minutes <= 10:
#                     score += 40
#                 elif time_diff_minutes <= 30:
#                     score += 20
                
#                 if diff_pct <= 0.01:
#                     score += 20
                    
#                 score = min(score, 100)
                
#                 severity = "critical" if score >= 80 else "high" if score >= 60 else "medium"
                
#                 results.append({
#                     "detector": "TransactionVelocity",
#                     "triggered": True,
#                     "score": score,
#                     "reason": f"₹{amt_in:,.2f} received and ₹{amt_out:,.2f} forwarded within {time_diff_minutes} minutes. {forwarded_pct:.1f}% of funds forwarded.",
#                     "transactions_involved": [credit["txn_id"], debit["txn_id"]],
#                     "severity": severity,
#                     "metadata": {
#                         "time_diff_minutes": time_diff_minutes,
#                         "amount_in": amt_in,
#                         "amount_out": amt_out,
#                         "forwarded_pct": round(forwarded_pct, 1)
#                     }
#                 })

#     if not results:
#         return {
#             "detector": "TransactionVelocity",
#             "triggered": False,
#             "score": 0,
#             "reason": "No high-velocity transaction pairs detected.",
#             "transactions_involved": [],
#             "severity": "none",
#             "metadata": {}
#         }
        
#     # Return highest score if multiple pairs
#     results.sort(key=lambda x: x["score"], reverse=True)
#     return results[0]
import pandas as pd
from app.models.transaction import Transaction
from app.models.statement import Statement


# ============================================================================
# CONFIGURATION
# ============================================================================

WINDOW_MINUTES = 60
MATCH_THRESHOLD = 0.95      # 95% of credit amount forwarded


# ============================================================================
# DETECTOR
# ============================================================================

def detect_velocity(case_id: str, statement_id: str = None):

    query = (
        Transaction.query
        .join(Statement)
        .filter(Transaction.case_id == case_id, Transaction.is_failed == False)
    )
    
    if statement_id:
        query = query.filter(Transaction.statement_id == statement_id)

    transactions = query.order_by(Transaction.date).all()

    if len(transactions) < 2:
        return {
            "detector": "TransactionVelocity",
            "triggered": False,
            "score": 0,
            "reason": "Not enough transactions for velocity analysis.",
            "transactions_involved": [],
            "severity": "none",
            "metadata": {}
        }

    # ========================================================================
    # BUILD DATAFRAME
    # ========================================================================

    df = pd.DataFrame([
        {
            "txn_id": t.id,
            "amount": abs(float(t.amount or 0)),
            "type": str(
                getattr(t, "type", "")
            ).lower(),
            "date": pd.to_datetime(t.date)
        }
        for t in transactions
    ])

    if df.empty:
        return {
            "detector": "TransactionVelocity",
            "triggered": False,
            "score": 0,
            "reason": "No transaction data available.",
            "transactions_involved": [],
            "severity": "none",
            "metadata": {}
        }

    df = df.sort_values("date").reset_index(drop=True)

    credits = df[df["type"] == "credit"]

    results = []

    # ========================================================================
    # ANALYZE EACH CREDIT
    # ========================================================================

    for _, credit in credits.iterrows():

        credit_time = credit["date"]
        credit_amount = credit["amount"]

        window_end = (
            credit_time
            + pd.Timedelta(minutes=WINDOW_MINUTES)
        )

        debits = df[
            (df["type"] == "debit")
            &
            (df["date"] >= credit_time)
            &
            (df["date"] <= window_end)
        ].copy()

        if debits.empty:
            continue

        total_forwarded = debits["amount"].sum()

        forwarded_pct = (
            total_forwarded / credit_amount
        )

        if forwarded_pct < MATCH_THRESHOLD:
            continue

        time_diff_minutes = int(
            (
                debits.iloc[-1]["date"]
                - credit_time
            ).total_seconds() / 60
        )

        # ====================================================================
        # RISK SCORING
        # ====================================================================

        score = 50

        if time_diff_minutes <= 10:
            score += 30
        elif time_diff_minutes <= 30:
            score += 20
        else:
            score += 10

        if forwarded_pct >= 1.0:
            score += 20
        elif forwarded_pct >= 0.98:
            score += 15
        elif forwarded_pct >= 0.95:
            score += 10

        score = min(score, 100)

        severity = (
            "critical"
            if score >= 80
            else "high"
            if score >= 60
            else "medium"
        )

        results.append({
            "detector": "TransactionVelocity",
            "triggered": True,
            "score": score,
            "reason": (
                f"₹{credit_amount:,.2f} received and "
                f"₹{total_forwarded:,.2f} forwarded "
                f"within {time_diff_minutes} minutes. "
                f"{forwarded_pct * 100:.1f}% of funds forwarded."
            ),
            "transactions_involved": (
                [credit["txn_id"]]
                + debits["txn_id"].tolist()
            ),
            "severity": severity,
            "metadata": {
                "time_diff_minutes":
                    time_diff_minutes,
                "amount_in":
                    credit_amount,
                "amount_out":
                    total_forwarded,
                "forwarded_pct":
                    round(
                        forwarded_pct * 100,
                        1
                    ),
                "window_minutes":
                    WINDOW_MINUTES
            }
        })

    # ========================================================================
    # NO MATCHES
    # ========================================================================

    if not results:

        return {
            "detector": "TransactionVelocity",
            "triggered": False,
            "score": 0,
            "reason": "No high-velocity transaction patterns detected.",
            "transactions_involved": [],
            "severity": "none",
            "metadata": {}
        }

    # ========================================================================
    # RETURN HIGHEST-RISK EVENT
    # ========================================================================

    results.sort(
        key=lambda x: (
            x["score"],
            x["metadata"]["amount_out"]
        ),
        reverse=True
    )

    return results[0]