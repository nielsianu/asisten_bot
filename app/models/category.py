from typing import List, Optional
from pydantic import BaseModel, Field


class Category(BaseModel):
    """Category data model for Household & Catering expense/income."""
    id: str
    business: str  # Household, Catering
    type: str  # Expense, Income
    category_name: str
    keywords: List[str] = Field(default_factory=list)
    budget_category: Optional[str] = None
    active: bool = True

    @classmethod
    def from_raw_keywords(cls, id: str, business: str, type: str, category_name: str, keywords_str: str, active: bool = True, budget_category: Optional[str] = None):
        kw_list = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
        return cls(
            id=id,
            business=business,
            type=type,
            category_name=category_name,
            keywords=kw_list,
            budget_category=budget_category if budget_category else None,
            active=active
        )
