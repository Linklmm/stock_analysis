"""订单管理模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

import pandas as pd

from src.core.utils import logger


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"       # 待处理
    SUBMITTED = "submitted"   # 已提交
    FILLED = "filled"         # 已成交
    CANCELLED = "cancelled"   # 已取消
    REJECTED = "rejected"     # 已拒绝


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"    # 市价单
    LIMIT = "limit"      # 限价单


class OrderDirection(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """
    订单类
    Order class

    Attributes:
        order_id: 订单ID
        code: 股票代码
        direction: 方向
        shares: 数量
        price: 价格（限价单）
        order_type: 订单类型
        status: 状态
        created_at: 创建时间
        filled_at: 成交时间
        filled_price: 成交价格
        filled_shares: 成交数量
    """
    order_id: str
    code: str
    direction: OrderDirection
    shares: int
    price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_shares: int = 0
    commission: float = 0.0
    message: str = ""

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "order_id": self.order_id,
            "code": self.code,
            "direction": self.direction.value,
            "shares": self.shares,
            "price": self.price,
            "order_type": self.order_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "filled_price": self.filled_price,
            "filled_shares": self.filled_shares,
            "commission": self.commission,
            "message": self.message
        }


class OrderManager:
    """
    订单管理器
    Order Manager

    管理订单的创建、查询、取消等。
    Manage order creation, query, cancellation, etc.
    """

    def __init__(self):
        """初始化订单管理器"""
        self.orders: Dict[str, Order] = {}
        self.pending_orders: List[str] = []

    def create_order(
        self,
        code: str,
        direction: str,
        shares: int,
        price: Optional[float] = None,
        order_type: str = "market"
    ) -> Order:
        """
        创建订单
        Create order

        Args:
            code: 股票代码
            direction: 方向 (buy/sell)
            shares: 数量
            price: 价格（限价单）
            order_type: 订单类型

        Returns:
            订单对象
        """
        order_id = str(uuid4())[:8]

        order = Order(
            order_id=order_id,
            code=code,
            direction=OrderDirection(direction.lower()),
            shares=shares,
            price=price,
            order_type=OrderType(order_type.lower()),
            status=OrderStatus.PENDING
        )

        self.orders[order_id] = order
        self.pending_orders.append(order_id)

        logger.info(f"创建订单: {order_id} {direction} {code} {shares}股")

        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        Cancel order

        Args:
            order_id: 订单ID

        Returns:
            是否成功
        """
        order = self.orders.get(order_id)

        if order is None:
            logger.warning(f"订单不存在: {order_id}")
            return False

        if order.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            logger.warning(f"订单状态不允许取消: {order.status.value}")
            return False

        order.status = OrderStatus.CANCELLED

        if order_id in self.pending_orders:
            self.pending_orders.remove(order_id)

        logger.info(f"订单已取消: {order_id}")
        return True

    def fill_order(
        self,
        order_id: str,
        filled_price: float,
        filled_shares: int,
        commission: float = 0
    ) -> bool:
        """
        成交订单
        Fill order

        Args:
            order_id: 订单ID
            filled_price: 成交价格
            filled_shares: 成交数量
            commission: 手续费

        Returns:
            是否成功
        """
        order = self.orders.get(order_id)

        if order is None:
            return False

        order.status = OrderStatus.FILLED
        order.filled_at = datetime.now()
        order.filled_price = filled_price
        order.filled_shares = filled_shares
        order.commission = commission

        if order_id in self.pending_orders:
            self.pending_orders.remove(order_id)

        logger.info(f"订单成交: {order_id} @ ¥{filled_price:.2f}")
        return True

    def reject_order(self, order_id: str, reason: str):
        """
        拒绝订单
        Reject order

        Args:
            order_id: 订单ID
            reason: 原因
        """
        order = self.orders.get(order_id)

        if order:
            order.status = OrderStatus.REJECTED
            order.message = reason

            if order_id in self.pending_orders:
                self.pending_orders.remove(order_id)

            logger.warning(f"订单被拒绝: {order_id}, 原因: {reason}")

    def get_pending_orders(self) -> List[Order]:
        """获取待处理订单"""
        return [self.orders[oid] for oid in self.pending_orders if oid in self.orders]

    def get_frozen_cash(self) -> float:
        """获取冻结资金"""
        # 计算买入订单冻结的资金
        frozen = 0
        for order_id in self.pending_orders:
            order = self.orders.get(order_id)
            if order and order.direction == OrderDirection.BUY:
                price = order.price or 0
                frozen += order.shares * price * 1.0003  # 预留手续费

        return frozen

    def get_orders_df(self) -> pd.DataFrame:
        """获取订单 DataFrame"""
        if not self.orders:
            return pd.DataFrame()

        records = [order.to_dict() for order in self.orders.values()]
        return pd.DataFrame(records)