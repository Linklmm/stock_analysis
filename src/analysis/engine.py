"""
分析引擎核心模块
Analysis Engine Core Module

该模块提供分析引擎的核心功能，协调各分析模块。
This module provides core functionality for the analysis engine,
coordinating various analysis modules.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from src.core.exceptions import AnalysisError
from src.core.utils import logger, parse_date
from config.settings import DEFAULT_MODEL


@dataclass
class AnalysisResult:
    """
    分析结果数据类
    Analysis result data class

    Attributes:
        code: 股票代码
        analysis_type: 分析类型
        timestamp: 时间戳
        data: 分析数据
        metrics: 评估指标
        signals: 交易信号
        recommendations: 建议
    """
    code: str
    analysis_type: str
    timestamp: datetime
    data: Optional[pd.DataFrame] = None
    metrics: Optional[Dict[str, float]] = None
    signals: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "analysis_type": self.analysis_type,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "signals": self.signals,
            "recommendations": self.recommendations
        }


class AnalysisEngine:
    """
    分析引擎类
    Analysis Engine Class

    协调各分析模块，提供统一的分析接口。
    Coordinate analysis modules, provide unified analysis interface.

    Attributes:
        config: 配置字典
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分析引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._data_provider = None
        self._model_manager = None

    def set_data_provider(self, provider):
        """设置数据提供者"""
        self._data_provider = provider

    def set_model_manager(self, manager):
        """设置模型管理器"""
        self._model_manager = manager

    def analyze(
        self,
        code: str,
        analysis_types: List[str] = None,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        **kwargs
    ) -> Dict[str, AnalysisResult]:
        """
        执行分析
        Execute analysis

        Args:
            code: 股票代码
            analysis_types: 分析类型列表
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数

        Returns:
            分析结果字典
        """
        if analysis_types is None:
            analysis_types = ["technical", "prediction"]

        results = {}

        # 获取数据
        data = self._get_data(code, start_date, end_date)

        if data is None or data.empty:
            logger.warning(f"未获取到股票 {code} 的数据")
            return results

        for analysis_type in analysis_types:
            try:
                if analysis_type == "technical":
                    results["technical"] = self._analyze_technical(code, data, **kwargs)
                elif analysis_type == "prediction":
                    results["prediction"] = self._analyze_prediction(code, data, **kwargs)
                elif analysis_type == "factor":
                    results["factor"] = self._analyze_factor(code, data, **kwargs)
                elif analysis_type == "risk":
                    results["risk"] = self._analyze_risk(code, data, **kwargs)
            except Exception as e:
                logger.error(f"{analysis_type} 分析失败: {e}")
                results[analysis_type] = AnalysisResult(
                    code=code,
                    analysis_type=analysis_type,
                    timestamp=datetime.now(),
                    recommendations=[f"分析失败: {str(e)}"]
                )

        return results

    def _get_data(
        self,
        code: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> Optional[pd.DataFrame]:
        """获取数据"""
        if self._data_provider is None:
            logger.warning("数据提供者未设置")
            return None

        try:
            from src.data.base import DataFrequency
            return self._data_provider.get_market_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency=DataFrequency.DAY
            )
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return None

    def _analyze_technical(
        self,
        code: str,
        data: pd.DataFrame,
        **kwargs
    ) -> AnalysisResult:
        """技术分析"""
        from src.analysis.technical import calculate_all_indicators, generate_trading_signals

        # 计算技术指标
        indicators = calculate_all_indicators(data)

        # 生成交易信号
        signals = generate_trading_signals(data)
        latest_signal = signals.iloc[-1]

        # 构建结果
        metrics = {
            "rsi": indicators["rsi"].iloc[-1] if "rsi" in indicators.columns else None,
            "macd": indicators["macd"].iloc[-1] if "macd" in indicators.columns else None,
        }

        signal_dict = {
            "final_signal": int(latest_signal.get("final_signal", 0)),
            "composite_score": float(latest_signal.get("composite_signal", 0))
        }

        # 生成建议
        recommendations = self._generate_recommendations(signal_dict)

        return AnalysisResult(
            code=code,
            analysis_type="technical",
            timestamp=datetime.now(),
            data=indicators,
            metrics=metrics,
            signals=signal_dict,
            recommendations=recommendations
        )

    def _analyze_prediction(
        self,
        code: str,
        data: pd.DataFrame,
        model_name: str = None,
        **kwargs
    ) -> AnalysisResult:
        """预测分析"""
        from src.analysis.prediction.trend_predictor import TrendPredictor

        model_name = model_name or DEFAULT_MODEL

        predictor = TrendPredictor(model_name=model_name)

        try:
            # 执行预测
            prediction = predictor.predict(data)

            metrics = {
                "predicted_return": prediction.get("predicted_return", 0),
                "confidence": prediction.get("confidence", 0),
                "direction": prediction.get("direction", 0)
            }

            signals = {
                "buy_probability": prediction.get("buy_probability", 0.5),
                "prediction_horizon": prediction.get("horizon", 5)
            }

            recommendations = []
            if prediction.get("direction", 0) > 0:
                recommendations.append("模型预测上涨趋势")
            else:
                recommendations.append("模型预测下跌趋势")

        except Exception as e:
            logger.error(f"预测失败: {e}")
            metrics = {}
            signals = {}
            recommendations = [f"预测失败: {str(e)}"]

        return AnalysisResult(
            code=code,
            analysis_type="prediction",
            timestamp=datetime.now(),
            metrics=metrics,
            signals=signals,
            recommendations=recommendations
        )

    def _analyze_factor(
        self,
        code: str,
        data: pd.DataFrame,
        **kwargs
    ) -> AnalysisResult:
        """因子分析"""
        # 简化实现
        return AnalysisResult(
            code=code,
            analysis_type="factor",
            timestamp=datetime.now(),
            recommendations=["因子分析功能开发中"]
        )

    def _analyze_risk(
        self,
        code: str,
        data: pd.DataFrame,
        **kwargs
    ) -> AnalysisResult:
        """风险分析"""
        from src.analysis.risk.metrics import calculate_risk_metrics

        try:
            risk_metrics = calculate_risk_metrics(data)

            return AnalysisResult(
                code=code,
                analysis_type="risk",
                timestamp=datetime.now(),
                metrics=risk_metrics,
                recommendations=self._generate_risk_recommendations(risk_metrics)
            )
        except Exception as e:
            return AnalysisResult(
                code=code,
                analysis_type="risk",
                timestamp=datetime.now(),
                recommendations=[f"风险分析失败: {str(e)}"]
            )

    def _generate_recommendations(self, signals: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []

        signal = signals.get("final_signal", 0)
        score = signals.get("composite_score", 0)

        if signal >= 2:
            recommendations.append("强烈建议买入，多个技术指标发出买入信号")
        elif signal == 1:
            recommendations.append("建议买入，技术指标偏多")
        elif signal == 0:
            recommendations.append("建议观望，等待更明确的信号")
        elif signal == -1:
            recommendations.append("建议卖出，技术指标偏空")
        else:
            recommendations.append("强烈建议卖出，多个技术指标发出卖出信号")

        return recommendations

    def _generate_risk_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """生成风险建议"""
        recommendations = []

        volatility = metrics.get("volatility", 0)
        max_drawdown = metrics.get("max_drawdown", 0)

        if volatility > 0.3:
            recommendations.append("⚠️ 波动率较高，注意风险控制")

        if abs(max_drawdown) > 0.2:
            recommendations.append("⚠️ 历史最大回撤较大，需注意仓位管理")

        if not recommendations:
            recommendations.append("风险指标正常")

        return recommendations


def create_engine(config: Optional[Dict] = None) -> AnalysisEngine:
    """
    创建分析引擎的便捷函数

    Args:
        config: 配置

    Returns:
        分析引擎实例
    """
    return AnalysisEngine(config)