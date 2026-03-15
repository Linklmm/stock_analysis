"""
数据预处理模块
Data Processor Module

该模块提供数据预处理功能，
包括数据清洗、特征工程、数据转换等。

This module provides data preprocessing functionality,
including data cleaning, feature engineering, and data transformation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple

import pandas as pd
import numpy as np

from src.core.exceptions import DataValidationError
from src.core.utils import logger, safe_divide
from config.settings import TECHNICAL_INDICATORS


class DataProcessor:
    """
    数据处理器类
    Data processor class

    提供数据清洗、特征工程等功能。
    Provides data cleaning, feature engineering, etc.

    Attributes:
        config: 配置字典 / Configuration dictionary
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据处理器

        Args:
            config: 配置字典 / Configuration dictionary
        """
        self.config = config or {}

    def clean_data(
        self,
        data: pd.DataFrame,
        remove_outliers: bool = True,
        fill_method: str = "ffill",
        **kwargs
    ) -> pd.DataFrame:
        """
        清洗数据
        Clean data

        处理缺失值、异常值等。
        Handle missing values, outliers, etc.

        Args:
            data: 原始数据 / Raw data
            remove_outliers: 是否移除异常值 / Whether to remove outliers
            fill_method: 填充方法 ("ffill", "bfill", "interpolate", "drop") / Fill method
            **kwargs: 其他参数 / Other parameters

        Returns:
            清洗后的数据 / Cleaned data
        """
        df = data.copy()

        # 记录原始数据量 / Record original data count
        original_count = len(df)

        # 处理缺失值 / Handle missing values
        df = self._handle_missing_values(df, method=fill_method)

        # 移除异常值 / Remove outliers
        if remove_outliers:
            df = self._remove_outliers(df, **kwargs)

        # 移除重复行 / Remove duplicate rows
        df = df[~df.index.duplicated(keep="last")]

        # 记录清洗后的数据量
        cleaned_count = len(df)
        logger.info(f"数据清洗完成: {original_count} -> {cleaned_count} 行")

        return df

    def _handle_missing_values(
        self,
        data: pd.DataFrame,
        method: str = "ffill"
    ) -> pd.DataFrame:
        """
        处理缺失值
        Handle missing values

        Args:
            data: 数据 / Data
            method: 填充方法 / Fill method
                - "ffill": 向前填充 / Forward fill
                - "bfill": 向后填充 / Backward fill
                - "interpolate": 插值 / Interpolate
                - "drop": 删除 / Drop
                - "mean": 均值填充 / Mean fill
                - "median": 中位数填充 / Median fill

        Returns:
            处理后的数据 / Processed data
        """
        df = data.copy()

        # 检查缺失值情况 / Check missing values
        missing = df.isnull().sum()
        if missing.sum() == 0:
            return df

        logger.debug(f"缺失值统计:\n{missing[missing > 0]}")

        if method == "ffill":
            df = df.fillna(method="ffill").fillna(method="bfill")
        elif method == "bfill":
            df = df.fillna(method="bfill").fillna(method="ffill")
        elif method == "interpolate":
            df = df.interpolate(method="time")
        elif method == "drop":
            df = df.dropna()
        elif method == "mean":
            df = df.fillna(df.mean())
        elif method == "median":
            df = df.fillna(df.median())

        return df

    def _remove_outliers(
        self,
        data: pd.DataFrame,
        method: str = "iqr",
        columns: Optional[List[str]] = None,
        threshold: float = 3.0,
        **kwargs
    ) -> pd.DataFrame:
        """
        移除异常值
        Remove outliers

        Args:
            data: 数据 / Data
            method: 方法 ("iqr", "zscore", "mad") / Method
            columns: 要处理的列 / Columns to process
            threshold: 阈值 / Threshold
            **kwargs: 其他参数 / Other parameters

        Returns:
            处理后的数据 / Processed data
        """
        df = data.copy()

        # 默认处理数值列 / Default to numeric columns
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            if method == "iqr":
                # IQR 方法 / IQR method
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # 用边界值替换异常值 / Replace outliers with boundary values
                df[col] = df[col].clip(lower_bound, upper_bound)

            elif method == "zscore":
                # Z-score 方法 / Z-score method
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df.loc[z_scores > threshold, col] = df[col].median()

            elif method == "mad":
                # MAD 方法 / MAD method
                median = df[col].median()
                mad = np.median(np.abs(df[col] - median))
                modified_z_scores = 0.6745 * (df[col] - median) / mad
                df.loc[np.abs(modified_z_scores) > threshold, col] = median

        return df

    def normalize_data(
        self,
        data: pd.DataFrame,
        method: str = "zscore",
        columns: Optional[List[str]] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        标准化数据
        Normalize data

        Args:
            data: 数据 / Data
            method: 方法 ("zscore", "minmax", "robust") / Method
            columns: 要处理的列 / Columns to process
            **kwargs: 其他参数 / Other parameters

        Returns:
            标准化后的数据 / Normalized data
        """
        df = data.copy()

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            if method == "zscore":
                # Z-score 标准化 / Z-score normalization
                mean = df[col].mean()
                std = df[col].std()
                if std != 0:
                    df[col] = (df[col] - mean) / std

            elif method == "minmax":
                # Min-Max 归一化 / Min-Max normalization
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val != min_val:
                    df[col] = (df[col] - min_val) / (max_val - min_val)

            elif method == "robust":
                # Robust 标准化 / Robust normalization
                median = df[col].median()
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                if iqr != 0:
                    df[col] = (df[col] - median) / iqr

        return df

    def add_returns(
        self,
        data: pd.DataFrame,
        price_col: str = "close",
        periods: List[int] = None
    ) -> pd.DataFrame:
        """
        添加收益率特征
        Add return features

        Args:
            data: 数据 / Data
            price_col: 价格列 / Price column
            periods: 周期列表 / Periods list

        Returns:
            添加收益率后的数据 / Data with return features
        """
        df = data.copy()

        if periods is None:
            periods = [1, 5, 10, 20]

        for period in periods:
            # 简单收益率 / Simple return
            df[f"return_{period}d"] = df[price_col].pct_change(period)

            # 对数收益率 / Log return
            df[f"log_return_{period}d"] = np.log(df[price_col] / df[price_col].shift(period))

        return df

    def add_volatility(
        self,
        data: pd.DataFrame,
        price_col: str = "close",
        periods: List[int] = None
    ) -> pd.DataFrame:
        """
        添加波动率特征
        Add volatility features

        Args:
            data: 数据 / Data
            price_col: 价格列 / Price column
            periods: 周期列表 / Periods list

        Returns:
            添加波动率后的数据 / Data with volatility features
        """
        df = data.copy()

        if periods is None:
            periods = [5, 10, 20, 60]

        returns = df[price_col].pct_change()

        for period in periods:
            # 滚动波动率 / Rolling volatility
            df[f"volatility_{period}d"] = returns.rolling(period).std() * np.sqrt(252)

        return df

    def add_ma_features(
        self,
        data: pd.DataFrame,
        price_col: str = "close",
        periods: List[int] = None
    ) -> pd.DataFrame:
        """
        添加移动平均特征
        Add moving average features

        Args:
            data: 数据 / Data
            price_col: 价格列 / Price column
            periods: 周期列表 / Periods list

        Returns:
            添加移动平均后的数据 / Data with MA features
        """
        df = data.copy()

        if periods is None:
            periods = TECHNICAL_INDICATORS["ma_periods"]

        for period in periods:
            # 简单移动平均 / Simple moving average
            df[f"ma_{period}"] = df[price_col].rolling(period).mean()

            # 价格与均线的偏离 / Price deviation from MA
            df[f"ma_{period}_deviation"] = (df[price_col] - df[f"ma_{period}"]) / df[f"ma_{period}"]

            # 均线斜率 / MA slope
            df[f"ma_{period}_slope"] = df[f"ma_{period}"].diff(5) / df[f"ma_{period}"].shift(5)

        return df

    def add_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        添加价格相关特征
        Add price-related features

        Args:
            data: 数据 / Data (需要包含 open, high, low, close 列)

        Returns:
            添加特征后的数据 / Data with price features
        """
        df = data.copy()

        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"缺少列: {missing_cols}，跳过价格特征计算")
            return df

        # 日内收益率 / Intraday return
        df["intraday_return"] = (df["close"] - df["open"]) / df["open"]

        # 上影线 / Upper shadow
        df["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]

        # 下影线 / Lower shadow
        df["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]

        # 实体大小 / Body size
        df["body_size"] = abs(df["close"] - df["open"]) / df["open"]

        # 振幅 / Amplitude
        df["amplitude"] = (df["high"] - df["low"]) / df["low"]

        # 涨跌 / Up or down
        df["is_up"] = (df["close"] > df["open"]).astype(int)

        # 跳空缺口 / Gap
        df["gap"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1)

        return df

    def add_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        添加成交量相关特征
        Add volume-related features

        Args:
            data: 数据 / Data

        Returns:
            添加特征后的数据 / Data with volume features
        """
        df = data.copy()

        if "volume" not in df.columns:
            logger.warning("缺少 volume 列，跳过成交量特征计算")
            return df

        periods = TECHNICAL_INDICATORS.get("volume_ma_periods", [5, 10, 20])

        for period in periods:
            # 成交量移动平均 / Volume moving average
            df[f"volume_ma_{period}"] = df["volume"].rolling(period).mean()

            # 成交量比率 / Volume ratio
            df[f"volume_ratio_{period}"] = df["volume"] / df[f"volume_ma_{period}"]

        # 成交量变化率 / Volume change rate
        df["volume_change"] = df["volume"].pct_change()

        # OBV (On-Balance Volume)
        if "close" in df.columns:
            df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).cumsum()

        return df

    def prepare_for_model(
        self,
        data: pd.DataFrame,
        target_period: int = 1,
        feature_columns: Optional[List[str]] = None,
        drop_na: bool = True
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备模型训练数据
        Prepare data for model training

        Args:
            data: 数据 / Data
            target_period: 预测周期 / Prediction period
            feature_columns: 特征列 / Feature columns
            drop_na: 是否删除缺失值 / Whether to drop NA

        Returns:
            (特征DataFrame, 标签Series) / (Features DataFrame, Labels Series)
        """
        df = data.copy()

        # 创建标签 / Create label
        # 预测未来 N 天的收益率 / Predict return for next N days
        df["label"] = df["close"].pct_change(target_period).shift(-target_period)

        # 分类标签：涨跌 / Classification label: up or down
        df["label_direction"] = (df["label"] > 0).astype(int)

        # 选择特征列 / Select feature columns
        if feature_columns is None:
            # 排除非特征列 / Exclude non-feature columns
            exclude_cols = ["code", "label", "label_direction"]
            feature_columns = [col for col in df.columns if col not in exclude_cols]

        X = df[feature_columns].copy()
        y = df["label_direction"].copy()  # 分类任务使用方向标签

        # 删除缺失值 / Drop NA
        if drop_na:
            valid_idx = ~(X.isna().any(axis=1) | y.isna())
            X = X[valid_idx]
            y = y[valid_idx]

        logger.info(f"准备模型数据完成: {len(X)} 样本, {len(feature_columns)} 特征")

        return X, y

    def split_by_time(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        valid_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        按时间分割数据
        Split data by time

        Args:
            data: 数据 / Data
            train_ratio: 训练集比例 / Training set ratio
            valid_ratio: 验证集比例 / Validation set ratio
            test_ratio: 测试集比例 / Test set ratio

        Returns:
            (训练集, 验证集, 测试集) / (Train, Valid, Test)
        """
        assert abs(train_ratio + valid_ratio + test_ratio - 1.0) < 1e-6, "比例之和必须为1"

        n = len(data)
        train_end = int(n * train_ratio)
        valid_end = int(n * (train_ratio + valid_ratio))

        train = data.iloc[:train_end]
        valid = data.iloc[train_end:valid_end]
        test = data.iloc[valid_end:]

        logger.info(f"数据分割: 训练 {len(train)}, 验证 {len(valid)}, 测试 {len(test)}")

        return train, valid, test


# ==================== 便捷函数 / Convenience Functions ====================

def process_data(
    data: pd.DataFrame,
    clean: bool = True,
    add_features: bool = True,
    normalize: bool = False,
    **kwargs
) -> pd.DataFrame:
    """
    数据处理便捷函数
    Data processing convenience function

    Args:
        data: 原始数据 / Raw data
        clean: 是否清洗 / Whether to clean
        add_features: 是否添加特征 / Whether to add features
        normalize: 是否标准化 / Whether to normalize
        **kwargs: 其他参数 / Other parameters

    Returns:
        处理后的数据 / Processed data
    """
    processor = DataProcessor(kwargs)

    if clean:
        data = processor.clean_data(data, **kwargs)

    if add_features:
        data = processor.add_returns(data)
        data = processor.add_volatility(data)
        data = processor.add_ma_features(data)
        data = processor.add_price_features(data)
        data = processor.add_volume_features(data)

    if normalize:
        data = processor.normalize_data(data, **kwargs)

    return data