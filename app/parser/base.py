from typing import Optional
from pydantic import BaseModel, Field


class ParsedResult(BaseModel):
    """Result returned by parsers in the pipeline."""
    success: bool = False
    type: str = "Expense"  # Expense, Income, Transfer, Refund, Adjustment
    business: str = "Household"  # Household, Catering
    category: str = "Lainnya"
    account: str = "Cash"
    amount: float = 0.0
    description: str = ""
    confidence: int = 0  # 0 to 100
    raw_text: str = ""
    parser_name: str = "Unknown"

    @property
    def is_confident(self) -> bool:
        """Threshold for auto-confirmation without user prompt."""
        return self.confidence >= 90
