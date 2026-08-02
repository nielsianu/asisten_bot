import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Transaction model representing financial income, expense, or transfer."""
    id: str = Field(default_factory=lambda: f"TX-{uuid.uuid4().hex[:8]}")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    time: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    type: str  # Expense, Income, Transfer, Refund, Adjustment
    business: str  # Household, Catering
    category: str
    account: str
    amount: float
    description: str
    source: str = "Telegram"
    ai_confidence: int = 100  # 0 - 100

    def to_sheet_row(self) -> list:
        """Convert transaction to Google Sheets row list."""
        return [
            self.id,
            self.date,
            self.time,
            self.type,
            self.business,
            self.category,
            self.account,
            self.amount,
            self.description,
            self.source,
            self.ai_confidence
        ]
