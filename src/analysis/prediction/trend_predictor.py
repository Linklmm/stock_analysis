"""
趋势预测模块
Trend Prediction Module

该模块提供股票趋势预测功能，
支持多种预测模型和方法。

This module provides stock trend prediction functionality,
supporting multiple prediction models and methods.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple

import pandas as pd
import numpy as np

from src.core.exceptions import ModelPredictionError
from src.core.utils import logger
from config.settings import DEFAULT_MODEL, get_model_config


class TrendPredictor:
    """
    趋势预测器
    Trend Predictor

    使用机器学习模型预测股票趋势。
    Use machine learning models to predict stock trends.

    Attributes:
        model_name: 模型名称
        model: 预测模型
        config: 配置
    """

    def __init__(
        self,
        model_name: str = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化趋势预测器

        Args:
            model_name: 模型名称 (lightgbm, mlp, transformer)
            config: 配置参数
        """
        self.model_name = model_name or DEFAULT_MODEL
        self.config = config or {}
        self.model = None
        self._is_trained = False

        # 获取模型配置
        self.model_config = get_model_config(self.model_name)

    def prepare_features(
        self,
        data: pd.DataFrame,
        feature_columns: List[str] = None
    ) -> pd.DataFrame:
        """
        准备特征
        Prepare features

        Args:
            data: 原始数据
            feature_columns: 特征列

        Returns:
            特征 DataFrame
        """
        from src.analysis.technical import calculate_all_indicators

        # 计算技术指标作为特征
        features = calculate_all_indicators(data)

        # 添加价格特征
        features["return_1d"] = features["close"].pct_change(1)
        features["return_5d"] = features["close"].pct_change(5)
        features["return_10d"] = features["close"].pct_change(10)

        # 添加波动率特征
        features["volatility_5d"] = features["return_1d"].rolling(5).std()
        features["volatility_20d"] = features["return_1d"].rolling(20).std()

        # 删除 NaN
        features = features.dropna()

        return features

    def train(
        self,
        data: pd.DataFrame,
        target_period: int = 5,
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        训练模型
        Train model

        Args:
            data: 训练数据
            target_period: 预测周期
            validation_split: 验证集比例

        Returns:
            训练指标
        """
        logger.info(f"开始训练 {self.model_name} 模型...")

        # 准备特征
        features = self.prepare_features(data)

        # 创建标签
        features["label"] = (features["close"].pct_change(target_period).shift(-target_period) > 0).astype(int)

        # 移除 NaN
        features = features.dropna()

        # 分割数据
        split_idx = int(len(features) * (1 - validation_split))
        train_data = features.iloc[:split_idx]
        valid_data = features.iloc[split_idx:]

        # 特征列（排除标签和代码）
        exclude_cols = ["label", "code"] if "code" in features.columns else ["label"]
        feature_cols = [col for col in features.columns if col not in exclude_cols]

        X_train = train_data[feature_cols]
        y_train = train_data["label"]
        X_valid = valid_data[feature_cols]
        y_valid = valid_data["label"]

        # 训练模型
        if self.model_name == "lightgbm":
            metrics = self._train_lightgbm(X_train, y_train, X_valid, y_valid)
        elif self.model_name == "mlp":
            metrics = self._train_mlp(X_train, y_train, X_valid, y_valid)
        else:
            raise ValueError(f"不支持的模型: {self.model_name}")

        self._is_trained = True
        self._feature_columns = feature_cols

        logger.info(f"模型训练完成，验证集 AUC: {metrics.get('auc', 0):.4f}")

        return metrics

    def _train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_valid: pd.DataFrame,
        y_valid: pd.Series
    ) -> Dict[str, float]:
        """训练 LightGBM 模型"""
        try:
            import lightgbm as lgb

            params = self.model_config.params if self.model_config else {}

            train_data = lgb.Dataset(X_train, label=y_train)
            valid_data = lgb.Dataset(X_valid, label=y_valid, reference=train_data)

            self.model = lgb.train(
                params,
                train_data,
                valid_sets=[valid_data],
                callbacks=[lgb.log_evaluation(period=100)]
            )

            # 评估
            y_pred = self.model.predict(X_valid)
            from sklearn.metrics import roc_auc_score, accuracy_score

            auc = roc_auc_score(y_valid, y_pred)
            acc = accuracy_score(y_valid, (y_pred > 0.5).astype(int))

            return {"auc": auc, "accuracy": acc}

        except ImportError:
            logger.warning("LightGBM 未安装，使用简单模型")
            return self._train_simple_model(X_train, y_train, X_valid, y_valid)

    def _train_mlp(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_valid: pd.DataFrame,
        y_valid: pd.Series
    ) -> Dict[str, float]:
        """训练 MLP 模型"""
        try:
            from sklearn.neural_network import MLPClassifier
            from sklearn.preprocessing import StandardScaler

            # 标准化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_valid_scaled = scaler.transform(X_valid)

            # 训练
            self.model = MLPClassifier(
                hidden_layer_sizes=(256, 128, 64),
                max_iter=100,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)

            # 评估
            y_pred = self.model.predict_proba(X_valid_scaled)[:, 1]
            from sklearn.metrics import roc_auc_score, accuracy_score

            auc = roc_auc_score(y_valid, y_pred)
            acc = accuracy_score(y_valid, (y_pred > 0.5).astype(int))

            self._scaler = scaler

            return {"auc": auc, "accuracy": acc}

        except ImportError:
            logger.warning("sklearn 未安装，使用简单模型")
            return self._train_simple_model(X_train, y_train, X_valid, y_valid)

    def _train_simple_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_valid: pd.DataFrame,
        y_valid: pd.Series
    ) -> Dict[str, float]:
        """训练简单模型（基于技术指标）"""
        # 使用简单规则作为后备
        self.model = "simple"

        # 基于技术指标的简单预测
        y_pred = np.zeros(len(X_valid))

        if "rsi" in X_valid.columns:
            y_pred += (X_valid["rsi"] < 30).astype(float) * 0.3  # RSI 超卖
            y_pred -= (X_valid["rsi"] > 70).astype(float) * 0.3  # RSI 超买

        if "macd" in X_valid.columns and "signal" in X_valid.columns:
            y_pred += (X_valid["macd"] > X_valid["signal"]).astype(float) * 0.2

        from sklearn.metrics import accuracy_score
        acc = accuracy_score(y_valid, (y_pred > 0).astype(int))

        return {"auc": 0.5, "accuracy": acc}

    def predict(
        self,
        data: pd.DataFrame,
        horizon: int = 5
    ) -> Dict[str, Any]:
        """
        预测趋势
        Predict trend

        Args:
            data: 数据
            horizon: 预测周期

        Returns:
            预测结果
        """
        # 准备特征
        features = self.prepare_features(data)

        if features.empty:
            return {
                "predicted_return": 0,
                "direction": 0,
                "confidence": 0.5,
                "buy_probability": 0.5,
                "horizon": horizon
            }

        # 获取最新特征
        latest = features.iloc[[-1]]

        if self.model is None or not self._is_trained:
            # 使用简单规则预测
            return self._simple_predict(latest, horizon)

        # 使用模型预测
        try:
            feature_cols = getattr(self, "_feature_columns", features.columns)

            X = latest[feature_cols]

            if self.model_name == "lightgbm":
                prob = self.model.predict(X)[0]
            elif self.model_name == "mlp":
                X_scaled = self._scaler.transform(X)
                prob = self.model.predict_proba(X_scaled)[0, 1]
            else:
                return self._simple_predict(latest, horizon)

            # 计算预测收益
            predicted_return = (prob - 0.5) * 0.1  # 简化计算

            return {
                "predicted_return": float(predicted_return),
                "direction": 1 if prob > 0.5 else -1,
                "confidence": float(abs(prob - 0.5) * 2),
                "buy_probability": float(prob),
                "horizon": horizon
            }

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return self._simple_predict(latest, horizon)

    def _simple_predict(
        self,
        features: pd.DataFrame,
        horizon: int
    ) -> Dict[str, Any]:
        """
        简单预测（基于技术指标规则）
        Simple prediction based on technical indicator rules
        """
        latest = features.iloc[0]

        score = 0
        signals = 0

        # RSI 信号
        if "rsi" in latest:
            if latest["rsi"] < 30:
                score += 1
            elif latest["rsi"] > 70:
                score -= 1
            signals += 1

        # MACD 信号
        if "macd" in latest and "signal" in latest:
            if latest["macd"] > latest["signal"]:
                score += 1
            else:
                score -= 1
            signals += 1

        # 均线信号
        if "ma_5" in latest and "ma_20" in latest:
            if latest["ma_5"] > latest["ma_20"]:
                score += 1
            else:
                score -= 1
            signals += 1

        # 计算概率
        if signals > 0:
            prob = (score + signals) / (2 * signals)
        else:
            prob = 0.5

        return {
            "predicted_return": (prob - 0.5) * 0.1,
            "direction": 1 if score > 0 else (-1 if score < 0 else 0),
            "confidence": abs(prob - 0.5) * 2,
            "buy_probability": prob,
            "horizon": horizon
        }

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000,
        target_period: int = 5
    ) -> Dict[str, Any]:
        """
        回测预测策略
        Backtest prediction strategy

        Args:
            data: 数据
            initial_capital: 初始资金
            target_period: 预测周期

        Returns:
            回测结果
        """
        features = self.prepare_features(data)

        # 简单回测逻辑
        features["signal"] = 0

        # 根据技术指标生成信号
        if "rsi" in features.columns:
            features.loc[features["rsi"] < 30, "signal"] = 1
            features.loc[features["rsi"] > 70, "signal"] = -1

        if "macd" in features.columns and "signal" in features.columns:
            macd_col = "macd"
            signal_col = "signal_y" if "signal_y" in features.columns else None
            if signal_col:
                features.loc[features[macd_col] > features[signal_col], "signal"] = 1

        # 计算收益
        features["returns"] = features["close"].pct_change()
        features["strategy_returns"] = features["signal"].shift(1) * features["returns"]

        # 计算累计收益
        cumulative_returns = (1 + features["strategy_returns"]).cumprod()

        total_return = cumulative_returns.iloc[-1] - 1 if len(cumulative_returns) > 0 else 0

        return {
            "total_return": float(total_return),
            "final_capital": float(initial_capital * (1 + total_return)),
            "num_trades": int((features["signal"] != 0).sum())
        }


def predict_trend(
    data: pd.DataFrame,
    model_name: str = None,
    horizon: int = 5
) -> Dict[str, Any]:
    """
    预测趋势的便捷函数
    Convenience function to predict trend

    Args:
        data: 数据
        model_name: 模型名称
        horizon: 预测周期

    Returns:
        预测结果
    """
    predictor = TrendPredictor(model_name)
    return predictor.predict(data, horizon)