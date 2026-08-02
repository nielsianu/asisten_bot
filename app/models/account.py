from typing import Optional
from pydantic import BaseModel, Field


class Account(BaseModel):
    """Account data model representing bank accounts, cash, or e-wallets."""
    id: str
    account_name: str
    type: str  # Bank, Cash, E-Wallet
    initial_balance: float = 0.0
    current_balance: float = 0.0
    notes: Optional[str] = ""
    active: bool = True
