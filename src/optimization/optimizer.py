"""组合优化器模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.core.utils import logger


class PortfolioOptimizer:
    """
    投资组合优化器
    Portfolio Optimizer

    提供多种组合优化方法。
    Provides multiple portfolio optimization methods.
    """

    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化优化器

        Args:
            risk_free_rate: 无风险利率
        """
        self.risk_free_rate = risk_free_rate

    def optimize_equal_weight(
        self,
        assets: List[str]
    ) -> Dict[str, float]:
        """
        等权重优化
        Equal weight optimization

        Args:
            assets: 资产列表

        Returns:
            权重字典
        """
        weight = 1.0 / len(assets)
        return {asset: weight for asset in assets}

    def optimize_min_variance(
        self,
        returns: pd.DataFrame,
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        最小方差优化
        Minimum variance optimization

        Args:
            returns: 收益率 DataFrame
            constraints: 约束条件

        Returns:
            权重字典
        """
        try:
            import cvxpy as cp

            n = len(returns.columns)
            cov_matrix = returns.cov().values

            # 优化变量
            w = cp.Variable(n)

            # 目标函数：最小化方差
            portfolio_variance = cp.quad_form(w, cov_matrix)

            # 约束条件
            constraints_list = [
                cp.sum(w) == 1,  # 权重和为1
                w >= 0  # 不允许做空
            ]

            # 添加额外约束
            if constraints:
                if "max_weight" in constraints:
                    constraints_list.append(w <= constraints["max_weight"])
                if "min_weight" in constraints:
                    constraints_list.append(w >= constraints["min_weight"])

            # 求解
            problem = cp.Problem(cp.Minimize(portfolio_variance), constraints_list)
            problem.solve()

            if problem.status == "optimal":
                weights = w.value
                return {asset: float(weights[i]) for i, asset in enumerate(returns.columns)}
            else:
                logger.warning("优化失败，返回等权重")
                return self.optimize_equal_weight(list(returns.columns))

        except ImportError:
            logger.warning("cvxpy 未安装，返回等权重")
            return self.optimize_equal_weight(list(returns.columns))

    def optimize_max_sharpe(
        self,
        returns: pd.DataFrame,
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        最大夏普比优化
        Maximum Sharpe ratio optimization

        Args:
            returns: 收益率 DataFrame
            constraints: 约束条件

        Returns:
            权重字典
        """
        try:
            import cvxpy as cp

            n = len(returns.columns)
            mean_returns = returns.mean().values * 252
            cov_matrix = returns.cov().values

            # 优化变量
            w = cp.Variable(n)
            k = cp.Variable()  # 缩放因子

            # 目标函数：最大化夏普比（等价于最小化 k）
            portfolio_return = mean_returns @ w

            # 约束条件
            constraints_list = [
                cp.sum(w) == 1,
                w >= 0,
                portfolio_return - self.risk_free_rate * k >= 0
            ]

            if constraints:
                if "max_weight" in constraints:
                    constraints_list.append(w <= constraints["max_weight"])

            # 求解
            problem = cp.Problem(cp.Minimize(k), constraints_list)
            problem.solve()

            if problem.status == "optimal":
                weights = w.value
                weights = weights / weights.sum()  # 归一化
                return {asset: float(weights[i]) for i, asset in enumerate(returns.columns)}
            else:
                logger.warning("优化失败，返回等权重")
                return self.optimize_equal_weight(list(returns.columns))

        except ImportError:
            logger.warning("cvxpy 未安装，返回等权重")
            return self.optimize_equal_weight(list(returns.columns))

    def optimize_risk_parity(
        self,
        returns: pd.DataFrame
    ) -> Dict[str, float]:
        """
        风险平价优化
        Risk parity optimization

        Args:
            returns: 收益率 DataFrame

        Returns:
            权重字典
        """
        try:
            from scipy.optimize import minimize

            n = len(returns.columns)
            cov_matrix = returns.cov().values

            def risk_contribution(w):
                """计算风险贡献"""
                portfolio_vol = np.sqrt(w @ cov_matrix @ w)
                marginal_contrib = cov_matrix @ w
                risk_contrib = w * marginal_contrib / portfolio_vol
                return risk_contrib

            def objective(w):
                """目标函数：风险贡献的差异"""
                rc = risk_contribution(w)
                target_risk = 1.0 / n
                return np.sum((rc - target_risk) ** 2)

            # 初始猜测
            w0 = np.ones(n) / n

            # 约束
            bounds = [(0.01, 1) for _ in range(n)]
            constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

            # 优化
            result = minimize(
                objective,
                w0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints
            )

            if result.success:
                weights = result.x
                return {asset: float(weights[i]) for i, asset in enumerate(returns.columns)}
            else:
                return self.optimize_equal_weight(list(returns.columns))

        except ImportError:
            return self.optimize_equal_weight(list(returns.columns))


def optimize_portfolio(
    returns: pd.DataFrame,
    method: str = "equal_weight",
    **kwargs
) -> Dict[str, float]:
    """
    优化投资组合的便捷函数
    Convenience function to optimize portfolio

    Args:
        returns: 收益率 DataFrame
        method: 优化方法
        **kwargs: 其他参数

    Returns:
        权重字典
    """
    optimizer = PortfolioOptimizer(kwargs.get("risk_free_rate", 0.03))

    if method == "equal_weight":
        return optimizer.optimize_equal_weight(list(returns.columns))
    elif method == "min_variance":
        return optimizer.optimize_min_variance(returns, kwargs.get("constraints"))
    elif method == "max_sharpe":
        return optimizer.optimize_max_sharpe(returns, kwargs.get("constraints"))
    elif method == "risk_parity":
        return optimizer.optimize_risk_parity(returns)
    else:
        raise ValueError(f"未知的优化方法: {method}")