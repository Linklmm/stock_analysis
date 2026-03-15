"""
数据缓存模块
Data Cache Module

该模块提供数据缓存功能，减少重复数据获取，
提高性能并减少API调用次数。

This module provides data caching functionality,
reducing redundant data retrieval, improving performance,
and reducing API calls.
"""

import os
import sys
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.exceptions import DataCacheError
from src.core.utils import logger, ensure_dir
from config.settings import CACHE_DIR, CACHE_CONFIG


class CacheKey:
    """
    缓存键生成器
    Cache key generator

    用于生成统一的缓存键。
    Used to generate unified cache keys.
    """

    @staticmethod
    def generate(*args, **kwargs) -> str:
        """
        生成缓存键
        Generate cache key

        将参数转换为唯一的缓存键字符串。
        Convert parameters to unique cache key string.

        Args:
            *args: 位置参数 / Positional arguments
            **kwargs: 关键字参数 / Keyword arguments

        Returns:
            缓存键字符串 / Cache key string
        """
        # 将参数转换为字符串 / Convert parameters to string
        key_parts = []

        for arg in args:
            if isinstance(arg, pd.DataFrame):
                key_parts.append(f"df_{hashlib.md5(pd.util.hash_pandas_object(arg).values.tobytes()).hexdigest()}")
            elif isinstance(arg, (list, dict)):
                key_parts.append(json.dumps(arg, sort_keys=True, default=str))
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            if isinstance(v, pd.DataFrame):
                key_parts.append(f"{k}=df_{hashlib.md5(pd.util.hash_pandas_object(v).values.tobytes()).hexdigest()}")
            elif isinstance(v, (list, dict)):
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True, default=str)}")
            else:
                key_parts.append(f"{k}={v}")

        key_str = "_".join(key_parts)

        # 使用 MD5 生成短键 / Use MD5 to generate short key
        return hashlib.md5(key_str.encode()).hexdigest()


class DataCache:
    """
    数据缓存类
    Data cache class

    提供文件系统的缓存功能，支持缓存有效期。
    Provides file system caching functionality with TTL support.

    Attributes:
        cache_dir: 缓存目录 / Cache directory
        ttl: 缓存有效期（秒）/ Cache TTL in seconds
        enabled: 是否启用缓存 / Whether cache is enabled
    """

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        ttl: Optional[int] = None,
        enabled: bool = True
    ):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录 / Cache directory
            ttl: 缓存有效期（秒）/ Cache TTL in seconds
            enabled: 是否启用缓存 / Whether cache is enabled
        """
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.ttl = ttl or CACHE_CONFIG.ttl
        self.enabled = enabled and CACHE_CONFIG.enabled

        # 确保缓存目录存在 / Ensure cache directory exists
        if self.enabled:
            ensure_dir(self.cache_dir)

        # 缓存元数据文件 / Cache metadata file
        self._metadata_file = self.cache_dir / "cache_metadata.json"
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Dict]:
        """
        加载缓存元数据
        Load cache metadata

        Returns:
            元数据字典 / Metadata dictionary
        """
        if not self._metadata_file.exists():
            return {}

        try:
            with open(self._metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载缓存元数据失败: {e}")
            return {}

    def _save_metadata(self):
        """
        保存缓存元数据
        Save cache metadata
        """
        try:
            with open(self._metadata_file, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存元数据失败: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """
        获取缓存文件路径
        Get cache file path

        Args:
            key: 缓存键 / Cache key

        Returns:
            缓存文件路径 / Cache file path
        """
        return self.cache_dir / f"{key}.cache"

    def _is_expired(self, key: str) -> bool:
        """
        检查缓存是否过期
        Check if cache is expired

        Args:
            key: 缓存键 / Cache key

        Returns:
            是否过期 / Whether expired
        """
        if key not in self._metadata:
            return True

        cached_time = datetime.fromisoformat(self._metadata[key].get("timestamp", "1970-01-01"))
        return datetime.now() - cached_time > timedelta(seconds=self.ttl)

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        Get cached data

        Args:
            key: 缓存键 / Cache key

        Returns:
            缓存的数据，如果不存在或过期返回 None / Cached data, None if not exists or expired
        """
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(key)

        # 检查是否存在 / Check if exists
        if not cache_path.exists():
            return None

        # 检查是否过期 / Check if expired
        if self._is_expired(key):
            self.delete(key)
            return None

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            logger.debug(f"缓存命中: {key}")
            return data

        except Exception as e:
            logger.warning(f"读取缓存失败: {key}, {e}")
            return None

    def set(self, key: str, data: Any, metadata: Optional[Dict] = None):
        """
        设置缓存数据
        Set cached data

        Args:
            key: 缓存键 / Cache key
            data: 要缓存的数据 / Data to cache
            metadata: 元数据 / Metadata
        """
        if not self.enabled:
            return

        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)

            # 更新元数据 / Update metadata
            self._metadata[key] = {
                "timestamp": datetime.now().isoformat(),
                "size": cache_path.stat().st_size,
                **(metadata or {})
            }
            self._save_metadata()

            logger.debug(f"缓存已保存: {key}")

        except Exception as e:
            logger.warning(f"保存缓存失败: {key}, {e}")

    def delete(self, key: str):
        """
        删除缓存
        Delete cache

        Args:
            key: 缓存键 / Cache key
        """
        cache_path = self._get_cache_path(key)

        try:
            if cache_path.exists():
                cache_path.unlink()

            if key in self._metadata:
                del self._metadata[key]
                self._save_metadata()

            logger.debug(f"缓存已删除: {key}")

        except Exception as e:
            logger.warning(f"删除缓存失败: {key}, {e}")

    def clear(self):
        """
        清空所有缓存
        Clear all cache
        """
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()

            self._metadata = {}
            self._save_metadata()

            logger.info("所有缓存已清空")

        except Exception as e:
            raise DataCacheError(
                operation="clear",
                message="清空缓存失败",
                details=str(e)
            )

    def clear_expired(self):
        """
        清理过期缓存
        Clear expired cache
        """
        cleared_count = 0

        for key in list(self._metadata.keys()):
            if self._is_expired(key):
                self.delete(key)
                cleared_count += 1

        logger.info(f"已清理 {cleared_count} 个过期缓存")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        Get cache statistics

        Returns:
            统计信息字典 / Statistics dictionary
        """
        total_size = sum(
            self._metadata.get(key, {}).get("size", 0)
            for key in self._metadata
        )

        valid_count = sum(1 for key in self._metadata if not self._is_expired(key))

        return {
            "total_entries": len(self._metadata),
            "valid_entries": valid_count,
            "expired_entries": len(self._metadata) - valid_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.ttl,
            "enabled": self.enabled
        }

    def cached(self, key_func: Optional[Callable] = None):
        """
        缓存装饰器
        Cache decorator

        用于缓存函数返回值。
        Used to cache function return values.

        Args:
            key_func: 生成缓存键的函数 / Function to generate cache key

        Returns:
            装饰器 / Decorator

        Example:
            @cache.cached()
            def get_data(code, start_date, end_date):
                # 获取数据
                return data

            # 或自定义键函数
            @cache.cached(key_func=lambda code, **kwargs: f"stock_{code}")
            def get_stock_data(code):
                return data
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # 生成缓存键 / Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}_{CacheKey.generate(*args, **kwargs)}"

                # 尝试从缓存获取 / Try to get from cache
                cached_data = self.get(cache_key)
                if cached_data is not None:
                    return cached_data

                # 执行函数 / Execute function
                result = func(*args, **kwargs)

                # 缓存结果 / Cache result
                self.set(cache_key, result)

                return result

            return wrapper
        return decorator


class DataFrameCache(DataCache):
    """
    DataFrame 专用缓存类
    DataFrame specialized cache class

    针对 pandas DataFrame 进行优化的缓存实现。
    Cache implementation optimized for pandas DataFrame.
    """

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        获取缓存的 DataFrame
        Get cached DataFrame

        Args:
            key: 缓存键 / Cache key

        Returns:
            DataFrame 或 None / DataFrame or None
        """
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(key)

        if not cache_path.exists() or self._is_expired(key):
            if cache_path.exists():
                self.delete(key)
            return None

        try:
            # 使用 parquet 格式存储 DataFrame
            # Use parquet format for DataFrame storage
            parquet_path = cache_path.with_suffix(".parquet")

            if parquet_path.exists():
                return pd.read_parquet(parquet_path)
            else:
                with open(cache_path, "rb") as f:
                    return pickle.load(f)

        except Exception as e:
            logger.warning(f"读取 DataFrame 缓存失败: {key}, {e}")
            return None

    def set(self, key: str, data: pd.DataFrame, metadata: Optional[Dict] = None):
        """
        设置 DataFrame 缓存
        Set DataFrame cache

        Args:
            key: 缓存键 / Cache key
            data: DataFrame 数据 / DataFrame data
            metadata: 元数据 / Metadata
        """
        if not self.enabled:
            return

        cache_path = self._get_cache_path(key)
        parquet_path = cache_path.with_suffix(".parquet")

        try:
            # 使用 parquet 格式存储
            # Use parquet format for storage
            if isinstance(data, pd.DataFrame):
                data.to_parquet(parquet_path, index=True)
            else:
                with open(cache_path, "wb") as f:
                    pickle.dump(data, f)

            # 更新元数据
            self._metadata[key] = {
                "timestamp": datetime.now().isoformat(),
                "size": parquet_path.stat().st_size if parquet_path.exists() else 0,
                "type": "DataFrame",
                **(metadata or {})
            }
            self._save_metadata()

        except Exception as e:
            logger.warning(f"保存 DataFrame 缓存失败: {key}, {e}")


# ==================== 全局缓存实例 / Global Cache Instance ====================

# 默认数据缓存实例 / Default data cache instance
cache = DataCache()

# DataFrame 专用缓存实例 / DataFrame cache instance
df_cache = DataFrameCache()


# ==================== 便捷函数 / Convenience Functions ====================

def cached(key_func: Optional[Callable] = None):
    """
    缓存装饰器便捷函数
    Cache decorator convenience function

    Args:
        key_func: 生成缓存键的函数 / Function to generate cache key

    Returns:
        装饰器 / Decorator
    """
    return cache.cached(key_func)


def clear_all_cache():
    """
    清空所有缓存
    Clear all cache
    """
    cache.clear()
    df_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息
    Get cache statistics

    Returns:
        统计信息字典 / Statistics dictionary
    """
    return cache.get_stats()