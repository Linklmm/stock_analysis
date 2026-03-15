"""模拟券商模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Dict, Optional, Tuple

from src.trading.account import PaperAccount
from src.trading.order import Order, OrderDirection, OrderStatus
from src.trading.position import Position
from src.core.exceptions import InsufficientFundsError, InsufficientSharesError
from src.core.utils import logger
from config.settings import TRADING_CONFIG


class PaperBroker:
    """
    模拟券商
    Paper Broker

    模拟券商功能，处理订单验证和执行。
    Simulate broker functionality, handle order validation and execution.

    Attributes:
        commission_rate: 佣金费率
        stamp_duty_rate: 印花税率
        min_commission: 最低佣金
        slippage: 滑点
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化模拟券商

        Args:
            config: 配置参数
        """
        config = config or {}

        self.commission_rate = config.get("commission_rate", TRADING_CONFIG.commission_rate)
        self.stamp_duty_rate = config.get("stamp_duty_rate", TRADING_CONFIG.stamp_duty_rate)
        self.min_commission = config.get("min_commission", TRADING_CONFIG.min_commission)
        self.slippage = config.get("slippage", TRADING_CONFIG.slippage)

        # 当前市场价格
        self.current_prices: Dict[str, float] = {}

    def update_prices(self, prices: Dict[str, float]):
        """
        更新市场价格
        Update market prices

        Args:
            prices: 价格字典
        """
        self.current_prices.update(prices)

    def get_price(self, code: str) -> Optional[float]:
        """获取价格"""
        return self.current_prices.get(code)

    def validate_order(
        self,
        account: PaperAccount,
        order: Order
    ) -> Tuple[bool, str]:
        """
        验证订单
        Validate order

        Args:
            account: 账户
            order: 订单

        Returns:
            (是否有效, 错误信息)
        """
        # 检查股票代码
        if not order.code:
            return False, "股票代码无效"

        # 检查数量
        if order.shares <= 0:
            return False, "数量必须大于0"

        # 检查是否为100的整数倍（A股规则）
        if order.shares % 100 != 0:
            return False, "数量必须是100的整数倍"

        # 检查买入
        if order.direction == OrderDirection.BUY:
            price = order.price or self.current_prices.get(order.code, 0)
            if price <= 0:
                return False, "价格无效"

            required = self._calculate_buy_amount(order.shares, price)

            if required > account.available_cash:
                return False, f"资金不足，需要 ¥{required:,.2f}，可用 ¥{account.available_cash:,.2f}"

        # 检查卖出
        elif order.direction == OrderDirection.SELL:
            position = account.position_manager.get_position(order.code)

            if position is None:
                return False, "无持仓"

            if position.available_shares < order.shares:
                return False, f"持仓不足，可用 {position.available_shares} 股"

        return True, ""

    def execute_order(
        self,
        account: PaperAccount,
        order: Order
    ) -> Tuple[bool, str]:
        """
        执行订单
        Execute order

        Args:
            account: 账户
            order: 订单

        Returns:
            (是否成功, 消息)
        """
        # 验证订单
        valid, message = self.validate_order(account, order)
        if not valid:
            account.order_manager.reject_order(order.order_id, message)
            return False, message

        # 获取成交价格
        price = order.price or self.current_prices.get(order.code, 0)

        if price <= 0:
            message = "无法获取价格"
            account.order_manager.reject_order(order.order_id, message)
            return False, message

        # 应用滑点
        if order.direction == OrderDirection.BUY:
            filled_price = price * (1 + self.slippage)
        else:
            filled_price = price * (1 - self.slippage)

        # 计算手续费
        commission = self._calculate_commission(
            order.shares * filled_price,
            is_sell=(order.direction == OrderDirection.SELL)
        )

        # 执行买入
        if order.direction == OrderDirection.BUY:
            amount = order.shares * filled_price + commission

            if amount > account.cash:
                message = "资金不足"
                account.order_manager.reject_order(order.order_id, message)
                return False, message

            # 扣除资金
            account.cash -= amount

            # 添加持仓
            account.position_manager.add_position(
                order.code,
                order.shares,
                filled_price
            )

            # 更新订单状态
            account.order_manager.fill_order(
                order.order_id,
                filled_price,
                order.shares,
                commission
            )

            # 记录交易
            account.trade_history.append({
                "datetime": datetime.now(),
                "code": order.code,
                "direction": "buy",
                "shares": order.shares,
                "price": filled_price,
                "amount": order.shares * filled_price,
                "commission": commission
            })

            logger.info(f"买入成交: {order.code} {order.shares}股 @ ¥{filled_price:.2f}")
            return True, "买入成功"

        # 执行卖出
        else:
            # 减少持仓
            account.position_manager.reduce_position(order.code, order.shares)

            # 计算收入
            amount = order.shares * filled_price - commission

            # 增加资金
            account.cash += amount

            # 更新订单状态
            account.order_manager.fill_order(
                order.order_id,
                filled_price,
                order.shares,
                commission
            )

            # 记录交易
            account.trade_history.append({
                "datetime": datetime.now(),
                "code": order.code,
                "direction": "sell",
                "shares": order.shares,
                "price": filled_price,
                "amount": order.shares * filled_price,
                "commission": commission
            })

            logger.info(f"卖出成交: {order.code} {order.shares}股 @ ¥{filled_price:.2f}")
            return True, "卖出成功"

    def _calculate_buy_amount(self, shares: int, price: float) -> float:
        """计算买入所需金额"""
        amount = shares * price * (1 + self.slippage)
        commission = self._calculate_commission(amount, is_sell=False)
        return amount + commission

    def _calculate_commission(self, amount: float, is_sell: bool = False) -> float:
        """计算手续费"""
        # 佣金
        commission = amount * self.commission_rate
        commission = max(commission, self.min_commission)

        # 印花税（仅卖出）
        if is_sell:
            commission += amount * self.stamp_duty_rate

        return commission

    def buy(
        self,
        account: PaperAccount,
        code: str,
        shares: int,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        买入
        Buy

        Args:
            account: 账户
            code: 股票代码
            shares: 数量
            price: 价格（可选，默认市价）

        Returns:
            (是否成功, 消息)
        """
        # 创建订单
        order = account.order_manager.create_order(
            code=code,
            direction="buy",
            shares=shares,
            price=price,
            order_type="limit" if price else "market"
        )

        # 执行订单
        return self.execute_order(account, order)

    def sell(
        self,
        account: PaperAccount,
        code: str,
        shares: int,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        卖出
        Sell

        Args:
            account: 账户
            code: 股票代码
            shares: 数量
            price: 价格（可选）

        Returns:
            (是否成功, 消息)
        """
        # 创建订单
        order = account.order_manager.create_order(
            code=code,
            direction="sell",
            shares=shares,
            price=price,
            order_type="limit" if price else "market"
        )

        # 执行订单
        return self.execute_order(account, order)