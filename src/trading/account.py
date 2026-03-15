"""模拟账户模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from src.trading.position import PositionManager
from src.trading.order import OrderManager
from src.core.utils import logger
from config.settings import TRADING_CONFIG


@dataclass
class AccountInfo:
    """账户信息"""
    account_id: str
    created_at: datetime
    initial_capital: float
    cash: float
    total_value: float
    total_profit_loss: float
    total_profit_loss_pct: float
    positions: Dict[str, Dict]


class PaperAccount:
    """
    模拟账户
    Paper Trading Account

    模拟股票交易账户，管理资金和持仓。
    Simulate stock trading account, manage funds and positions.

    Attributes:
        account_id: 账户ID
        initial_capital: 初始资金
        cash: 可用现金
    """

    def __init__(
        self,
        account_id: str = "default",
        initial_capital: float = None
    ):
        """
        初始化账户

        Args:
            account_id: 账户ID
            initial_capital: 初始资金
        """
        self.account_id = account_id
        self.initial_capital = initial_capital or TRADING_CONFIG.initial_capital
        self.cash = self.initial_capital

        # 创建时间和更新时间
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # 持仓管理器
        self.position_manager = PositionManager()

        # 订单管理器
        self.order_manager = OrderManager()

        # 交易历史
        self.trade_history: List[Dict] = []

        # 账户状态
        self.is_active = True

        logger.info(f"创建模拟账户: {account_id}, 初始资金: ¥{initial_capital:,.2f}")

    @property
    def total_value(self) -> float:
        """总资产"""
        return self.cash + self.position_manager.total_market_value

    @property
    def total_profit_loss(self) -> float:
        """总盈亏"""
        return self.total_value - self.initial_capital

    @property
    def total_profit_loss_pct(self) -> float:
        """总收益率"""
        if self.initial_capital == 0:
            return 0
        return (self.total_value - self.initial_capital) / self.initial_capital

    @property
    def available_cash(self) -> float:
        """可用资金"""
        # 考虑冻结资金
        frozen = self.order_manager.get_frozen_cash()
        return max(0, self.cash - frozen)

    def deposit(self, amount: float):
        """
        入金
        Deposit

        Args:
            amount: 金额
        """
        if amount <= 0:
            raise ValueError("入金金额必须大于0")

        self.cash += amount
        self.updated_at = datetime.now()
        logger.info(f"账户 {self.account_id} 入金: ¥{amount:,.2f}")

    def withdraw(self, amount: float) -> bool:
        """
        出金
        Withdraw

        Args:
            amount: 金额

        Returns:
            是否成功
        """
        if amount <= 0:
            raise ValueError("出金金额必须大于0")

        if amount > self.available_cash:
            logger.warning(f"账户 {self.account_id} 可用资金不足")
            return False

        self.cash -= amount
        self.updated_at = datetime.now()
        logger.info(f"账户 {self.account_id} 出金: ¥{amount:,.2f}")
        return True

    def get_account_info(self) -> AccountInfo:
        """
        获取账户信息
        Get account info

        Returns:
            账户信息
        """
        return AccountInfo(
            account_id=self.account_id,
            created_at=self.created_at,
            initial_capital=self.initial_capital,
            cash=self.cash,
            total_value=self.total_value,
            total_profit_loss=self.total_profit_loss,
            total_profit_loss_pct=self.total_profit_loss_pct,
            positions=self.position_manager.get_all_positions()
        )

    def get_positions_df(self) -> pd.DataFrame:
        """获取持仓 DataFrame"""
        return self.position_manager.to_dataframe()

    def get_trade_history_df(self) -> pd.DataFrame:
        """获取交易历史 DataFrame"""
        if not self.trade_history:
            return pd.DataFrame()

        return pd.DataFrame(self.trade_history)

    def update_market_prices(self, prices: Dict[str, float]):
        """
        更新市场价格
        Update market prices

        Args:
            prices: 价格字典 {股票代码: 价格}
        """
        self.position_manager.update_prices(prices)
        self.updated_at = datetime.now()

    def reset(self):
        """
        重置账户
        Reset account
        """
        self.cash = self.initial_capital
        self.position_manager = PositionManager()
        self.order_manager = OrderManager()
        self.trade_history = []
        self.updated_at = datetime.now()
        logger.info(f"账户 {self.account_id} 已重置")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "account_id": self.account_id,
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "total_value": self.total_value,
            "total_profit_loss": self.total_profit_loss,
            "total_profit_loss_pct": self.total_profit_loss_pct,
            "positions": len(self.position_manager.positions),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }