# import pandas as pd
# from app.models.transaction import Transaction

# def detect_cash_cycling(case_id: str):
#     transactions = (
#         Transaction.query
#         .filter_by(case_id=case_id, is_failed=False)
#         .all()
#     )

#     if len(transactions) < 2:
#         return {
#             "detector": "CashCycling",
#             "triggered": False,
#             "score": 0,
#             "reason": "Not enough transactions for cash cycling analysis.",
#             "transactions_involved": [],
#             "severity": "none",
#             "metadata": {}
#         }

#     df = pd.DataFrame([
#         {
#             "txn_id": t.id,
#             "amount": float(t.amount),
#             "type": t.type,
#             "date": pd.to_datetime(t.date),
#             "description": str(t.description).lower() if t.description else ""
#         }
#         for t in transactions
#     ])

#     results = []
    
#     df = df.sort_values("date").reset_index(drop=True)
    
#     cash_keywords = ["cash", "atm deposit", "cdm", "atm withdrawal"]
    
#     def is_cash(desc):
#         return any(k in desc for k in cash_keywords)

#     df["is_cash"] = df["description"].apply(is_cash)
    
#     cash_deposits = df[(df["type"] == "credit") & (df["is_cash"])]
#     cash_withdrawals = df[(df["type"] == "debit") & (df["is_cash"])]
    
#     for idx, deposit in cash_deposits.iterrows():
#         mask = (cash_withdrawals["date"] >= deposit["date"]) & ((cash_withdrawals["date"] - deposit["date"]).dt.total_seconds() <= 86400)
#         subsequent_withdrawals = cash_withdrawals[mask]
        
#         for w_idx, withdrawal in subsequent_withdrawals.iterrows():
#             amt_in = deposit["amount"]
#             amt_out = withdrawal["amount"]
            
#             diff_pct = abs(amt_in - amt_out) / amt_in if amt_in > 0 else 0
            
#             if diff_pct <= 0.10:
#                 score = 70 if diff_pct <= 0.05 else 50
#                 severity = "high" if score >= 60 else "medium"
                
#                 results.append({
#                     "detector": "CashCycling",
#                     "triggered": True,
#                     "score": score,
#                     "reason": f"Cash deposit of ₹{amt_in:,.2f} followed by cash withdrawal of ₹{amt_out:,.2f} within 24 hours.",
#                     "transactions_involved": [deposit["txn_id"], withdrawal["txn_id"]],
#                     "severity": severity,
#                     "metadata": {
#                         "amount_deposited": amt_in,
#                         "amount_withdrawn": amt_out,
#                         "difference_pct": round(diff_pct * 100, 1)
#                     }
#                 })

#     if not results:
#         return {
#             "detector": "CashCycling",
#             "triggered": False,
#             "score": 0,
#             "reason": "No cash cycling patterns detected.",
#             "transactions_involved": [],
#             "severity": "none",
#             "metadata": {}
#         }
        
#     results.sort(key=lambda x: x["score"], reverse=True)
#     return results[0]


import pandas as pd
from app.models.transaction import Transaction
from app.models.statement import Statement


# ============================================================================
# CONFIGURATION
# ============================================================================

WINDOW_HOURS = 24
MATCH_THRESHOLD = 0.80      # 80% of deposited cash withdrawn
CRITICAL_THRESHOLD = 0.95
HIGH_THRESHOLD = 0.90


# ============================================================================
# HELPERS
# ============================================================================

CASH_KEYWORDS = [
    "cash",
    "atm",
    "cdm",
    "cash deposit",
    "cash withdrawal",
    "atm withdrawal",
    "self withdrawal",
    "cheque withdrawal"
]


def is_cash_transaction(description: str) -> bool:

    if not description:
        return False

    description = description.lower()

    return any(
        keyword in description
        for keyword in CASH_KEYWORDS
    )


# ============================================================================
# DETECTOR
# ============================================================================

def detect_cash_cycling(case_id: str, statement_id: str = None):

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
            "detector": "CashCycling",
            "triggered": False,
            "score": 0,
            "reason": "Not enough transactions for cash cycling analysis.",
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
            "date": pd.to_datetime(t.date),
            "description": (
                t.description.lower()
                if t.description
                else ""
            )
        }
        for t in transactions
    ])

    if df.empty:

        return {
            "detector": "CashCycling",
            "triggered": False,
            "score": 0,
            "reason": "No transaction data available.",
            "transactions_involved": [],
            "severity": "none",
            "metadata": {}
        }

    df = df.sort_values("date").reset_index(drop=True)

    df["is_cash"] = df["description"].apply(
        is_cash_transaction
    )

    cash_credits = df[
        (df["type"] == "credit")
        &
        (df["is_cash"])
    ]

    cash_debits = df[
        (df["type"] == "debit")
        &
        (df["is_cash"])
    ]

    results = []

    # ========================================================================
    # ANALYZE EACH CASH DEPOSIT
    # ========================================================================

    for _, deposit in cash_credits.iterrows():

        deposit_time = deposit["date"]

        window_end = (
            deposit_time
            + pd.Timedelta(hours=WINDOW_HOURS)
        )

        withdrawals = cash_debits[
            (cash_debits["date"] >= deposit_time)
            &
            (cash_debits["date"] <= window_end)
        ]

        if withdrawals.empty:
            continue

        amount_in = deposit["amount"]
        amount_out = withdrawals["amount"].sum()

        if amount_in <= 0:
            continue

        ratio = amount_out / amount_in

        if ratio < MATCH_THRESHOLD:
            continue

        # ====================================================================
        # SCORING
        # ====================================================================

        if ratio >= CRITICAL_THRESHOLD:

            score = 90
            severity = "critical"

        elif ratio >= HIGH_THRESHOLD:

            score = 75
            severity = "high"

        else:

            score = 60
            severity = "medium"

        score = min(score, 100)

        time_diff_hours = round(
            (
                withdrawals.iloc[-1]["date"]
                - deposit_time
            ).total_seconds() / 3600,
            1
        )

        results.append({
            "detector": "CashCycling",
            "triggered": True,
            "score": score,
            "reason": (
                f"Cash deposit of "
                f"₹{amount_in:,.2f} was followed by "
                f"₹{amount_out:,.2f} in cash withdrawals "
                f"within {time_diff_hours} hours."
            ),
            "transactions_involved": (
                [deposit["txn_id"]]
                + withdrawals["txn_id"].tolist()
            ),
            "severity": severity,
            "metadata": {
                "amount_deposited":
                    round(amount_in, 2),

                "amount_withdrawn":
                    round(amount_out, 2),

                "cycling_ratio":
                    round(ratio * 100, 1),

                "time_window_hours":
                    WINDOW_HOURS,

                "withdrawal_count":
                    len(withdrawals)
            }
        })

    # ========================================================================
    # NO MATCHES
    # ========================================================================

    if not results:

        return {
            "detector": "CashCycling",
            "triggered": False,
            "score": 0,
            "reason": "No cash cycling patterns detected.",
            "transactions_involved": [],
            "severity": "none",
            "metadata": {}
        }

    # ========================================================================
    # RETURN STRONGEST EVENT
    # ========================================================================

    results.sort(
        key=lambda x: (
            x["score"],
            x["metadata"]["amount_withdrawn"]
        ),
        reverse=True
    )

    return results[0]