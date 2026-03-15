"""资产配置模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from src.core.utils import logger


@dataclass
class Allocation:
    """资产配置"""
    asset: str
    weight: float
    shares: int = 0
    value: float = 0.0


class AssetAllocator:
    """
    资产配置器
    Asset Allocator

    管理资产配置和再平衡。
    Manage asset allocation and rebalancing.
    """

    def __init__(self, total_capital: float):
        """
        初始化配置器

        Args:
            total_capital: 总资金
        """
        self.total_capital = total_capital
        self.allocations: Dict[str, Allocation] = {}

    def set_allocation(
        self,
        weights: Dict[str, float],
        prices: Optional[Dict[str, float]] = None
    ):
        """
        设置资产配置

        Args:
            weights: 权重字典
            prices: 价格字典（可选）
        """
        self.allocations = {}

        for asset, weight in weights.items():
            value = self.total_capital * weight

            shares = 0
            if prices and asset in prices:
                shares = int(value / prices[asset])

            self.allocations[asset] = Allocation(
                asset=asset,
                weight=weight,
                shares=shares,
                value=value
            )

    def rebalance(
        self,
        new_weights: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict[str, Dict]:
        """
        再平衡组合

        Args:
            new_weights: 新权重
            prices: 当前价格

        Returns:
            调整指令
        """
        adjustments = {}

        for asset, new_weight in new_weights.items():
            target_value = self.total_capital * new_weight
            current_value = self.allocations.get(asset, Allocation(asset, 0)).value

            diff = target_value - current_value
            shares_diff = int(diff / prices.get(asset, 1))

            adjustments[asset] = {
                "current_weight": self.allocations.get(asset, Allocation(asset, 0)).weight,
                "target_weight": new_weight,
                "shares_change": shares_diff,
                "value_change": diff
            }

        return adjustments

    def get_allocation_table(self) -> pd.DataFrame:
        """获取配置表"""
        records = []

        for asset, allocation in self.allocations.items():
            records.append({
                "资产": asset,
                "权重": f"{allocation.weight * 100:.2f}%",
                "股数": allocation.shares,
                "市值": f"¥{allocation.value:,.2f}"
            })

        return pd.DataFrame(records)


def allocate_assets(
    capital: float,
    weights: Dict[str, float],
    prices: Optional[Dict[str, float]] = None
) -> Dict[str, Allocation]:
    """
    资产配置的便捷函数
    Convenience function for asset allocation

    Args:
        capital: 总资金
        weights: 权重字典
        prices: 价格字典

    Returns:
        配置字典
    """
    allocator = AssetAllocator(capital)
    allocator.set_allocation(weights, prices)
    return allocator.allocations