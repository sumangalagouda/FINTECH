# from app.detectors.structuring import detect_structuring
# from app.detectors.dormant_revival import detect_dormant_revival
# from app.detectors.large_transaction import detect_large_transaction
# from app.detectors.beneficiary_burst import detect_beneficiary_burst
# from app.detectors.high_risk_time import detect_high_risk_time


# WEIGHTS = {
#     "Structuring": 0.25,
#     "DormantRevival": 0.25,
#     "LargeTransaction": 0.20,
#     "BeneficiaryBurst": 0.15,
#     "HighRiskTime": 0.15
# }


# def calculate_evidence_confidence(case_id: str):

#     # --------------------------------------------------
#     # Run all detectors
#     # --------------------------------------------------
#     results = {
#         "Structuring": detect_structuring(case_id),
#         "DormantRevival": detect_dormant_revival(case_id),
#         "LargeTransaction": detect_large_transaction(case_id),
#         "BeneficiaryBurst": detect_beneficiary_burst(case_id),
#         "HighRiskTime": detect_high_risk_time(case_id)
#     }

#     breakdown = {}
#     triggered_count = 0
#     total_weighted_score = 0

#     # --------------------------------------------------
#     # Process detector outputs
#     # --------------------------------------------------
#     for detector_name, detector_outputs in results.items():

#         weight = WEIGHTS.get(detector_name, 0.10)

#         triggered_items = [
#             d for d in detector_outputs
#             if d.get("triggered", False)
#         ]

#         if triggered_items:

#             highest_score = max(
#                 d.get("score", 0)
#                 for d in triggered_items
#             )

#             breakdown[detector_name] = {
#                 "score": highest_score,
#                 "weight": weight,
#                 "triggered": True
#             }

#             total_weighted_score += (
#                 highest_score * weight
#             )

#             triggered_count += 1

#         else:

#             breakdown[detector_name] = {
#                 "score": 0,
#                 "weight": weight,
#                 "triggered": False
#             }

#     # --------------------------------------------------
#     # Confidence Calculation
#     # --------------------------------------------------
#     max_weight = sum(WEIGHTS.values())

#     if max_weight > 0:
#         overall_confidence = (
#             total_weighted_score / max_weight
#         )
#     else:
#         overall_confidence = 0

#     # --------------------------------------------------
#     # Multi-pattern Synergy Bonus
#     # --------------------------------------------------
#     synergy_bonus = 0

#     if triggered_count >= 4:
#         synergy_bonus = 25

#     elif triggered_count == 3:
#         synergy_bonus = 20

#     elif triggered_count == 2:
#         synergy_bonus = 10

#     overall_confidence += synergy_bonus

#     overall_confidence = min(
#         100,
#         round(overall_confidence)
#     )

#     # --------------------------------------------------
#     # Risk Assessment
#     # --------------------------------------------------
#     if overall_confidence >= 85:

#         assessment = (
#             "Strong multi-pattern fraud evidence. "
#             "Immediate investigator review recommended."
#         )

#     elif overall_confidence >= 70:

#         assessment = (
#             "Multiple suspicious patterns detected. "
#             "High-risk case requiring investigation."
#         )

#     elif overall_confidence >= 50:

#         assessment = (
#             "Moderate suspicious activity detected. "
#             "Further review recommended."
#         )

#     elif overall_confidence > 0:

#         assessment = (
#             "Limited suspicious activity detected."
#         )

#     else:

#         assessment = (
#             "No suspicious patterns detected."
#         )

#     # --------------------------------------------------
#     # Final Response
#     # --------------------------------------------------
#     return {
#         "overall_confidence": overall_confidence,
#         "breakdown": breakdown,
#         "triggered_count": triggered_count,
#         "assessment": assessment,
#         "raw_results": results
#     }

from app.detectors.structuring import detect_structuring
from app.detectors.dormant_revival import detect_dormant_revival
from app.detectors.large_transaction import detect_large_transaction
from app.detectors.beneficiary_burst import detect_beneficiary_burst
from app.detectors.high_risk_time import detect_high_risk_time
from app.detectors.velocity import detect_velocity
from app.detectors.pass_through import detect_pass_through
from app.detectors.cash_cycling import detect_cash_cycling


# ============================================================================
# DETECTOR WEIGHTS
# ============================================================================

WEIGHTS = {

    # Core AML signals
    "LargeTransaction": 0.18,
    "Structuring": 0.18,

    # Behavioural patterns
    "TransactionVelocity": 0.15,
    "PassThrough": 0.15,
    "CashCycling": 0.12,

    # Supporting indicators
    "BeneficiaryBurst": 0.10,
    "DormantRevival": 0.07,
    "HighRiskTime": 0.05
}


# ============================================================================
# HELPER
# ============================================================================

def normalize_output(result):

    if result is None:
        return []

    if isinstance(result, dict):
        return [result]

    return result


# ============================================================================
# EVIDENCE CONFIDENCE ENGINE
# ============================================================================

def calculate_evidence_confidence(case_id: str):

    # ========================================================================
    # RUN DETECTORS
    # ========================================================================

    results = {

        "Structuring":
            normalize_output(
                detect_structuring(case_id)
            ),

        "DormantRevival":
            normalize_output(
                detect_dormant_revival(case_id)
            ),

        "LargeTransaction":
            normalize_output(
                detect_large_transaction(case_id)
            ),

        "BeneficiaryBurst":
            normalize_output(
                detect_beneficiary_burst(case_id)
            ),

        "HighRiskTime":
            normalize_output(
                detect_high_risk_time(case_id)
            ),

        "TransactionVelocity":
            normalize_output(
                detect_velocity(case_id)
            ),

        "PassThrough":
            normalize_output(
                detect_pass_through(case_id)
            ),

        "CashCycling":
            normalize_output(
                detect_cash_cycling(case_id)
            )
    }

    # ========================================================================
    # PROCESS RESULTS
    # ========================================================================

    breakdown = {}

    triggered_count = 0
    total_weighted_score = 0

    for detector_name, outputs in results.items():

        weight = WEIGHTS.get(
            detector_name,
            0
        )

        triggered = [
            d
            for d in outputs
            if d.get("triggered", False)
        ]

        if triggered:

            best_score = max(
                d.get("score", 0)
                for d in triggered
            )

            total_weighted_score += (
                best_score * weight
            )

            triggered_count += 1

            breakdown[detector_name] = {

                "triggered": True,

                "score": best_score,

                "weight": weight
            }

        else:

            breakdown[detector_name] = {

                "triggered": False,

                "score": 0,

                "weight": weight
            }

    # ========================================================================
    # BASE CONFIDENCE
    # ========================================================================

    max_weight = sum(
        WEIGHTS.values()
    )

    confidence = (
        total_weighted_score
        / max_weight
    ) if max_weight > 0 else 0

    # ========================================================================
    # SYNERGY BONUS
    # ========================================================================

    synergy_bonus = 0

    if triggered_count >= 5:

        synergy_bonus = 20

    elif triggered_count == 4:

        synergy_bonus = 15

    elif triggered_count == 3:

        synergy_bonus = 10

    elif triggered_count == 2:

        synergy_bonus = 5

    confidence += synergy_bonus

    confidence = min(
        100,
        round(confidence)
    )

    # ========================================================================
    # ASSESSMENT
    # ========================================================================

    if confidence >= 90:

        assessment = (
            "Strong multi-pattern fraud evidence. "
            "Immediate investigator action recommended."
        )

    elif confidence >= 75:

        assessment = (
            "Multiple suspicious behaviours detected. "
            "High-risk case requiring detailed review."
        )

    elif confidence >= 60:

        assessment = (
            "Moderate suspicious activity detected. "
            "Further investigation recommended."
        )

    elif confidence > 0:

        assessment = (
            "Limited suspicious indicators detected."
        )

    else:

        assessment = (
            "No suspicious patterns detected."
        )

    # ========================================================================
    # FINAL OUTPUT
    # ========================================================================

    return {

        "overall_confidence":
            confidence,

        "breakdown":
            breakdown,

        "triggered_count":
            triggered_count,

        "assessment":
            assessment,

        "raw_results":
            results
    }