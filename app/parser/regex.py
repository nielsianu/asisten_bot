import re
from typing import Optional, Tuple
from app.parser.base import ParsedResult


class RegexParser:
    """Regex-based parser for natural language amounts, accounts, types, and business."""

    # Nominal regex patterns
    AMOUNT_PATTERNS = [
        (r"(\d+(?:[\.,]\d+)?)\s*(?:jt|juta)", 1_000_000),
        (r"(\d+(?:[\.,]\d+)?)\s*(?:rb|ribu|k)", 1_000),
        (r"rp\.?\s*(\d+(?:[\.,]\d+)*)", 1),
        (r"\b(\d{4,9})\b", 1),
    ]

    # Type keywords
    INCOME_KEYWORDS = ["dapat", "terima", "menerima", "gaji", "bonus", "omset", "laba", "masuk", "jual", "penjualan", "pembayaran", "pelunasan", "lunas", "dp", "bayaran", "transferan"]
    EXPENSE_KEYWORDS = ["beli", "bayar", "jajan", "sewa", "ongkir", "isi", "tagihan", "keluar"]
    TRANSFER_KEYWORDS = ["transfer", "pindah", "kirim", "topup", "top up"]

    # Account keywords
    ACCOUNT_KEYWORDS = {
        "blu": "Blu BCA",
        "blubca": "Blu BCA",
        "bca": "BCA",
        "mandiri": "Mandiri",
        "cash": "Cash",
        "tunai": "Cash",
        "qris": "QRIS",
        "gopay": "E-Wallet",
        "ovo": "E-Wallet",
        "shopeepay": "E-Wallet",
        "ewallet": "E-Wallet",
        "e-wallet": "E-Wallet",
    }

    @classmethod
    def extract_amount(cls, text: str) -> Optional[float]:
        """Extract numeric amount from text string."""
        for pattern, multiplier in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num_str = match.group(1)
                # If decimal with jt/ribu (e.g. 1.5jt, 2,5rb), convert comma to dot
                if multiplier in (1_000_000, 1_000) and ("," in num_str or "." in num_str):
                    num_str = num_str.replace(",", ".")
                else:
                    # Regular thousand separators (e.g. 250.000)
                    num_str = num_str.replace(".", "").replace(",", ".")
                try:
                    return float(num_str) * multiplier
                except ValueError:
                    continue
        return None

    @classmethod
    def extract_type(cls, text: str) -> str:
        """Extract transaction type (Expense, Income, Transfer)."""
        lower = text.lower()
        if any(kw in lower for kw in cls.INCOME_KEYWORDS):
            if "ke" in lower and "dari" in lower and not any(k in lower for k in ["pembayaran", "pelunasan", "lunas", "dp", "omset", "jual"]):
                return "Transfer"
            return "Income"

        if any(kw in lower for kw in cls.TRANSFER_KEYWORDS):
            return "Transfer"

        return "Expense"  # Default to Expense

    @classmethod
    def extract_account(cls, text: str) -> str:
        """Extract account name from text."""
        lower = text.lower()
        for kw, acc in cls.ACCOUNT_KEYWORDS.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                return acc
        return "Cash"  # Default account

    @classmethod
    def extract_business(cls, text: str) -> str:
        """Determine if transaction belongs to Household or Catering."""
        lower = text.lower()
        catering_keywords = ["katering", "catering", "nasi box", "nasi kotak", "pesanan", "order katering", "bumbu katering", "box mika"]
        if any(kw in lower for kw in catering_keywords):
            return "Catering"
        return "Household"

    @classmethod
    def parse(cls, text: str) -> ParsedResult:
        amount = cls.extract_amount(text)
        if not amount:
            return ParsedResult(success=False, raw_text=text, parser_name="RegexParser")

        tx_type = cls.extract_type(text)
        account = cls.extract_account(text)
        business = cls.extract_business(text)

        return ParsedResult(
            success=True,
            type=tx_type,
            business=business,
            category="Lainnya",  # To be enriched by Synonym Parser
            account=account,
            amount=amount,
            description=text.strip(),
            confidence=70,  # Base regex confidence, boosted if synonym matches category
            raw_text=text,
            parser_name="RegexParser"
        )
