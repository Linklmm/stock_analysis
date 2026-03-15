"""持仓管理模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from src.core.utils import logger


@dataclass
class Position:
    """
    持仓类
    Position class

    Attributes:
        code: 股票代码
        shares: 持仓数量
        available_shares: 可用数量
        cost: 成本价
        current_price: 当前价格
        bought_at: 买入时间
    """
    code: str
    shares: int
    cost: float
    available_shares: int = 0
    current_price: float = 0.0
    bought_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.available_shares == 0:
            self.available_shares = self.shares

    @property
    def market_value(self) -> float:
        """市值"""
        return self.shares * self.current_price

    @property
    def profit_loss(self) -> float:
        """盈亏"""
        return (self.current_price - self.cost) * self.shares

    @property
    def profit_loss_pct(self) -> float:
        """盈亏比例"""
        if self.cost == 0:
            return 0
        return (self.current_price - self.cost) / self.cost

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "code": self.code,
            "shares": self.shares,
            "available_shares": self.available_shares,
            "cost": self.cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "profit_loss": self.profit_loss,
            "profit_loss_pct": self.profit_loss_pct,
            "bought_at": self.bought_at.isoformat()
        }


class PositionManager:
    """
    持仓管理器
    Position Manager

    管理账户持仓。
    Manage account positions.
    """

    def __init__(self):
        """初始化持仓管理器"""
        self.positions: Dict[str, Position] = {}

    @property
    def total_market_value(self) -> float:
        """总市值"""
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_profit_loss(self) -> float:
        """总盈亏"""
        return sum(p.profit_loss for p in self.positions.values())

    def add_position(
        self,
        code: str,
        shares: int,
        cost: float
    ):
        """
        添加持仓
        Add position

        Args:
            code: 股票代码
            shares: 数量
            cost: 成本
        """
        if code in self.positions:
            # 加仓
            existing = self.positions[code]
            total_cost = existing.cost * existing.shares + cost * shares
            total_shares = existing.shares + shares
            new_cost = total_cost / total_shares

            existing.shares = total_shares
            existing.available_shares += shares
            existing.cost = new_cost
        else:
            # 新建持仓
            self.positions[code] = Position(
                code=code,
                shares=shares,
                cost=cost
            )

        logger.info(f"添加持仓: {code} {shares}股 @ ¥{cost:.2f}")

    def reduce_position(
        self,
        code: str,
        shares: int
    ) -> Optional[float]:
        """
        减少持仓
        Reduce position

        Args:
            code: 股票代码
            shares: 数量

        Returns:
            成本价
        """
        if code not in self.positions:
            logger.warning(f"无持仓: {code}")
            return None

        position = self.positions[code]

        if position.available_shares < shares:
            logger.warning(f"可用持仓不足: {code}")
            return None

        cost_price = position.cost

        position.shares -= shares
        position.available_shares -= shares

        if position.shares <= 0:
            del self.positions[code]
            logger.info(f"清空持仓: {code}")

        logger.info(f"减少持仓: {code} {shares}股")

        return cost_price

    def get_position(self, code: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(code)

    def get_all_positions(self) -> Dict[str, Dict]:
        """获取所有持仓"""
        return {code: pos.to_dict() for code, pos in self.positions.items()}

    def update_prices(self, prices: Dict[str, float]):
        """
        更新价格
        Update prices

        Args:
            prices: 价格字典
        """
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code].current_price = price

    def to_dataframe(self) -> pd.DataFrame:
        """转换为 DataFrame"""
        if not self.positions:
            return pd.DataFrame()

        records = [pos.to_dict() for pos in self.positions.values()]
        df = pd.DataFrame(records)

        # 格式化
        if not df.empty:
            df = df[["code", "shares", "available_shares", "cost", "current_price",
                     "market_value", "profit_loss", "profit_loss_pct"]]

        return df

    def clear(self):
        """清空所有持仓"""
        self.positions.clear()
        logger.info("已清空所有持仓")