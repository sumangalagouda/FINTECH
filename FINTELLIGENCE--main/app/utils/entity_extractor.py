    # import re

    # def infer_counterparty(description):
    #     """
    #     Infers the counterparty (sender or receiver entity) from a transaction description.
    #     """
    #     if not description:
    #         return None
            
    #     desc = str(description).strip()
        
    #     # 1. ATM Withdrawals
    #     if "ATM" in desc.upper() and ("CASH" in desc.upper() or "WDL" in desc.upper() or "WITHDRAWAL" in desc.upper()):
    #         return "ATM_WITHDRAWAL"
    #     if desc.upper().startswith("ATMCASH"):
    #         return "ATM_WITHDRAWAL"
            
    #     # 2. Explicit Transfers (TO / FROM)
    #     # E.g. "TRANSFER TO HARSH SAHU", "FUNDS TRF FROM MS S K ENTERPRISES"
    #     match = re.search(r'(?i)(?:TRANSFER TO|FUNDS TRF TO|TRF TO|TO)\s+([A-Za-z\s]+)', desc)
    #     if match:
    #         name = match.group(1).strip()
    #         if len(name) > 2:
    #             return name.upper()
                
    #     match = re.search(r'(?i)(?:TRANSFER FROM|FUNDS TRF FROM|TRF FROM|FROM)\s+([A-Za-z\s]+)', desc)
    #     if match:
    #         name = match.group(1).strip()
    #         if len(name) > 2:
    #             return name.upper()

    #     # 3. UPI, RTGS, NEFT, IMPS with long reference numbers
    #     # Example: UPIP2A015264151524HARSH SAHU
    #     # Example: RTGSBDBLR62025042818275734Ms S K ENTERPRISESBANDHAN BANK LIMITED
    #     # Example: INBNEFT...Shahnawaz Ahmad
    #     # Matches prefix, optional non-digits, followed by at least 10 digits (the RRN/UTR), and then text
    #     match = re.search(r'(?i)(?:UPI|RTGS|NEFT|IMPS|INBNEFT)[A-Za-z0-9]*?\d{10,}([A-Za-z\s]+)', desc)
    #     if match:
    #         name = match.group(1).strip()
    #         # Remove common bank suffixes that might have merged
    #         name = re.sub(r'(?i)(?:BANDHAN|BANK|LTD|LIMITED)$', '', name).strip()
    #         if len(name) > 2:
    #             return name.upper()

    #     # 4. Slashed formats common in UPI (e.g. UPI/123456789012/JOHN DOE/SBI)
    #     match = re.search(r'(?i)UPI/(?:[A-Za-z0-9]+/)?\d{10,}/([^/]+)', desc)
    #     if match:
    #         name = match.group(1).strip()
    #         name = re.sub(r'[^A-Za-z\s]', '', name).strip()
    #         if len(name) > 2:
    #             return name.upper()

    #     # 5. Hyphenated formats common in NEFT/RTGS (e.g. NEFT-123456-JOHN DOE)
    #     match = re.search(r'(?i)(?:NEFT|RTGS|IMPS)[-/]?\w+[-/]+([A-Za-z\s]+)', desc)
    #     if match:
    #         name = match.group(1).strip()
    #         name = re.sub(r'[^A-Za-z\s]', '', name).strip()
    #         if len(name) > 2:
    #             return name.upper()
                
    #     # 6. Generic cleanup for purely alphabetic remaining patterns after common prefixes if no numbers
    #     match = re.search(r'(?i)^(?:UPI|RTGS|NEFT|IMPS|INBNEFT)[\s:-]+([A-Za-z\s]+)', desc)
    #     if match:
    #         name = match.group(1).strip()
    #         if len(name) > 2:
    #             return name.upper()

    #     return None
import re


# ============================================================================
# HELPERS
# ============================================================================

def clean_name(name: str):

    if not name:
        return None

    # Remove bank suffixes and noise
    name = re.sub(
        r'(?i)(BANK.*|LIMITED.*|LTD.*|PAYMENT.*|PAYMEN.*|FINANC.*|TRANSFER.*)$',
        '',
        name
    )

    # Remove special characters
    name = re.sub(
        r'[^A-Za-z ]',
        ' ',
        name
    )

    # Remove extra spaces
    name = " ".join(name.split())

    if len(name) < 3:
        return None

    return name.upper()


# ============================================================================
# MAIN ENTITY EXTRACTION
# ============================================================================

def infer_counterparty(description):

    if not description:
        return None

    desc = str(description).strip()
    desc_upper = desc.upper()

    # ========================================================================
    # ATM CASH
    # ========================================================================

    if (
        "ATM" in desc_upper
        and (
            "CASH" in desc_upper
            or "WDL" in desc_upper
            or "WITHDRAWAL" in desc_upper
        )
    ):
        return "ATM_WITHDRAWAL"

    if desc_upper.startswith("ATMCASH"):
        return "ATM_WITHDRAWAL"

    # ========================================================================
    # RTGS SPECIAL CASE
    # Example:
    # RTGSBDBLR62025042818275734Ms S K ENTERPRISESBANDHAN BANK LIMITED
    # ========================================================================

    match = re.search(
        r'(?i)RTGS.*?\d{10,}([A-Za-z ]+?)BANDHAN',
        desc
    )

    if match:

        name = clean_name(
            match.group(1)
        )

        if name:
            return name

    # ========================================================================
    # NEFT SPECIAL CASE
    # Example:
    # INBNEFTAXOIR04163823501Shahnawaz AhmadBANK OF INDIA TRANSFER
    # ========================================================================

    match = re.search(
        r'(?i)INBNEFT.*?\d{8,}([A-Za-z ]+?)BANK',
        desc
    )

    if match:

        name = clean_name(
            match.group(1)
        )

        if name:
            return name

    # ========================================================================
    # UPI SPECIAL CASE
    # Example:
    # UPIP2A015264151524HARSH SAHUPaymenUTKARSH SMALL FINANC
    # ========================================================================

    match = re.search(
        r'(?i)UPI[A-Za-z0-9]*?\d{8,}([A-Za-z ]+)',
        desc
    )

    if match:

        name = match.group(1)

        name = re.sub(
            r'(?i)(PAYMENT.*|PAYMEN.*|UTKARSH.*|SMALL.*|FINANC.*)$',
            '',
            name
        )

        name = clean_name(name)

        if name:
            return name

    # ========================================================================
    # IMPS
    # ========================================================================

    match = re.search(
        r'(?i)IMPS.*?\d{8,}([A-Za-z ]+)',
        desc
    )

    if match:

        name = clean_name(
            match.group(1)
        )

        if name:
            return name

    # ========================================================================
    # TRANSFER TO
    # ========================================================================

    match = re.search(
        r'(?i)(?:TRANSFER TO|FUNDS TRF TO|TRF TO|TO)\s+([A-Za-z ]+)',
        desc
    )

    if match:

        name = clean_name(
            match.group(1)
        )

        if name:
            return name

    # ========================================================================
    # TRANSFER FROM
    # ========================================================================

    match = re.search(
        r'(?i)(?:TRANSFER FROM|FUNDS TRF FROM|TRF FROM|FROM)\s+([A-Za-z ]+)',
        desc
    )

    if match:

        name = clean_name(
            match.group(1)
        )

        if name:
            return name

    # ========================================================================
    # UPI SLASH FORMAT
    # Example:
    # UPI/1234567890/HARSH SAHU/SBI
    # ========================================================================

    match = re.search(
        r'(?i)UPI/(?:[A-Za-z0-9]+/)?\d{8,}/([^/]+)',
        desc
    )

    if match:

        name = clean_name(
            match.group(1)
        )

        if name:
            return name

    # ========================================================================
    # LAST RESORT
    # Prevents SELF -> UNKNOWN collapsing
    # ========================================================================

    cleaned = re.sub(
        r'[^A-Za-z ]',
        ' ',
        desc
    )

    cleaned = " ".join(cleaned.split())

    if len(cleaned) > 10:

        return cleaned[:30].upper()

    return "UNIDENTIFIED"