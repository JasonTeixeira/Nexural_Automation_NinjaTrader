from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


MarketPosition = Literal["Long", "Short", "Flat"]


class NormalizedTrade(BaseModel):
    trade_number: int
    instrument: str
    account: Optional[str] = None
    strategy: Optional[str] = None
    market_pos: MarketPosition
    qty: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    entry_name: Optional[str] = None
    exit_name: Optional[str] = None
    profit: float = Field(description="Net profit for the trade (after commission if provided).")
    cum_net_profit: Optional[float] = None
    commission: Optional[float] = None

    mae: Optional[float] = Field(default=None, description="Maximum adverse excursion (currency).")
    mfe: Optional[float] = Field(default=None, description="Maximum favorable excursion (currency).")
    etd: Optional[float] = Field(default=None, description="End trade drawdown (currency).")
    bars: Optional[int] = None

    @property
    def duration_seconds(self) -> float:
        return (self.exit_time - self.entry_time).total_seconds()
