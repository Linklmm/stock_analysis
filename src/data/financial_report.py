"""
财报数据获取模块
Financial Report Data Module

提供股票财报数据获取和分析功能。
Provides stock financial report data fetching and analysis functions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd
import streamlit as st

from src.core.utils import logger


class FinancialReportProvider:
    """
    财报数据提供者
    Financial report data provider
    """

    def __init__(self):
        self._akshare_available = None

    def _check_akshare(self) -> bool:
        """检查 AkShare 是否可用"""
        if self._akshare_available is not None:
            return self._akshare_available

        try:
            import akshare as ak
            self._akshare_available = True
            return True
        except Exception:
            self._akshare_available = False
            return False

    @st.cache_data(ttl=3600, show_spinner=False)  # 1小时缓存
    def get_financial_abstract(_self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取财务摘要数据

        Args:
            stock_code: 股票代码 (如 000001 或 000001.SZ)

        Returns:
            财务数据 DataFrame
        """
        if not _self._check_akshare():
            logger.warning("AkShare 不可用")
            return None

        try:
            import akshare as ak

            # 提取纯数字代码
            code_num = stock_code.split(".")[0]

            # 获取财务摘要
            df = ak.stock_financial_abstract(symbol=code_num)

            if df is None or df.empty:
                return None

            logger.info(f"获取财务摘要成功: {stock_code}")
            return df

        except Exception as e:
            logger.error(f"获取财务摘要失败: {e}")
            return None

    def get_financial_data(self, stock_code: str) -> Optional[Dict]:
        """
        获取并整理财务数据

        Args:
            stock_code: 股票代码

        Returns:
            整理后的财务数据字典
        """
        df = self.get_financial_abstract(stock_code)
        if df is None or df.empty:
            return None

        # 整理数据
        result = {
            "raw_data": df,
            "indicators": {},
            "years": [],
        }

        # 获取年份列表（从列名中提取）
        date_cols = [col for col in df.columns if col not in ['选项', '指标']]
        result["years"] = date_cols

        # 按指标类型整理
        for _, row in df.iterrows():
            category = row['选项']
            indicator = row['指标']

            if category not in result["indicators"]:
                result["indicators"][category] = {}

            result["indicators"][category][indicator] = {
                col: row[col] for col in date_cols
            }

        return result

    def calculate_growth_rates(self, data: Dict) -> Dict:
        """
        计算增长率

        Args:
            data: 财务数据

        Returns:
            包含增长率的字典
        """
        if not data or "indicators" not in data:
            return {}

        growth = {}
        years = data.get("years", [])

        # 营收增长率
        if "常用指标" in data["indicators"] and "营业总收入" in data["indicators"]["常用指标"]:
            revenue = data["indicators"]["常用指标"]["营业总收入"]
            growth["营收增长率"] = self._calc_growth(revenue, years)

        # 净利润增长率
        if "常用指标" in data["indicators"] and "归母净利润" in data["indicators"]["常用指标"]:
            profit = data["indicators"]["常用指标"]["归母净利润"]
            growth["净利润增长率"] = self._calc_growth(profit, years)

        return growth

    def _calc_growth(self, values: Dict, years: List) -> Dict:
        """计算同比增长率"""
        growth = {}
        sorted_years = sorted([y for y in years if y])

        for i, year in enumerate(sorted_years[1:], 1):
            try:
                current = values.get(year)
                prev = values.get(sorted_years[i-1])

                if current and prev and prev != 0:
                    growth_rate = (float(current) - float(prev)) / abs(float(prev)) * 100
                    growth[year] = growth_rate
            except Exception:
                pass

        return growth

    def analyze_financial_health(self, data: Dict) -> Dict:
        """
        分析财务健康度

        Args:
            data: 财务数据

        Returns:
            健康度分析结果
        """
        if not data or "indicators" not in data:
            return {}

        analysis = {
            "盈利能力": self._analyze_profitability(data),
            "成长能力": self._analyze_growth(data),
            "财务风险": self._analyze_risk(data),
            "综合评分": 0,
        }

        # 计算综合评分 (0-100)
        scores = []
        for key in ["盈利能力", "成长能力", "财务风险"]:
            if analysis.get(key) and "score" in analysis[key]:
                scores.append(analysis[key]["score"])

        if scores:
            analysis["综合评分"] = sum(scores) / len(scores)

        return analysis

    def _analyze_profitability(self, data: Dict) -> Dict:
        """分析盈利能力"""
        result = {"score": 50, "analysis": [], "rating": "一般"}

        if "盈利能力" not in data["indicators"]:
            return result

        indicators = data["indicators"]["盈利能力"]
        years = data.get("years", [])
        if not years:
            return result

        latest_year = years[0]  # 最新一期

        # ROE 分析
        if "净资产收益率(ROE)" in indicators:
            roe = indicators["净资产收益率(ROE)"].get(latest_year)
            if roe:
                roe_val = float(roe) if roe else 0
                if roe_val >= 15:
                    result["analysis"].append(f"ROE {roe_val:.1f}% 优秀 (>=15%)")
                    result["score"] += 15
                elif roe_val >= 10:
                    result["analysis"].append(f"ROE {roe_val:.1f}% 良好 (10-15%)")
                    result["score"] += 8
                elif roe_val >= 5:
                    result["analysis"].append(f"ROE {roe_val:.1f}% 一般 (5-10%)")
                else:
                    result["analysis"].append(f"ROE {roe_val:.1f}% 较差 (<5%)")
                    result["score"] -= 10

        # 毛利率分析
        if "毛利率" in indicators:
            gross = indicators["毛利率"].get(latest_year)
            if gross:
                gross_val = float(gross) if gross else 0
                if gross_val >= 40:
                    result["analysis"].append(f"毛利率 {gross_val:.1f}% 优秀 (>=40%)")
                    result["score"] += 10
                elif gross_val >= 20:
                    result["analysis"].append(f"毛利率 {gross_val:.1f}% 良好 (20-40%)")
                else:
                    result["analysis"].append(f"毛利率 {gross_val:.1f}% 较低 (<20%)")

        # 净利率分析
        if "销售净利率" in indicators:
            net = indicators["销售净利率"].get(latest_year)
            if net:
                net_val = float(net) if net else 0
                if net_val >= 15:
                    result["analysis"].append(f"净利率 {net_val:.1f}% 优秀 (>=15%)")
                    result["score"] += 10
                elif net_val >= 5:
                    result["analysis"].append(f"净利率 {net_val:.1f}% 良好 (5-15%)")
                else:
                    result["analysis"].append(f"净利率 {net_val:.1f}% 较低 (<5%)")

        # 评分上限100
        result["score"] = min(100, max(0, result["score"]))

        # 评级
        if result["score"] >= 80:
            result["rating"] = "优秀"
        elif result["score"] >= 60:
            result["rating"] = "良好"
        elif result["score"] >= 40:
            result["rating"] = "一般"
        else:
            result["rating"] = "较差"

        return result

    def _analyze_growth(self, data: Dict) -> Dict:
        """分析成长能力"""
        result = {"score": 50, "analysis": [], "rating": "一般"}

        growth_data = self.calculate_growth_rates(data)

        # 营收增长
        if "营收增长率" in growth_data:
            revenue_growth = growth_data["营收增长率"]
            if revenue_growth:
                avg_growth = sum(revenue_growth.values()) / len(revenue_growth)
                if avg_growth >= 20:
                    result["analysis"].append(f"营收年均增长 {avg_growth:.1f}% 高速成长")
                    result["score"] += 15
                elif avg_growth >= 10:
                    result["analysis"].append(f"营收年均增长 {avg_growth:.1f}% 稳健增长")
                    result["score"] += 8
                elif avg_growth >= 0:
                    result["analysis"].append(f"营收年均增长 {avg_growth:.1f}% 小幅增长")
                else:
                    result["analysis"].append(f"营收年均增长 {avg_growth:.1f}% 下滑")
                    result["score"] -= 10

        # 净利润增长
        if "净利润增长率" in growth_data:
            profit_growth = growth_data["净利润增长率"]
            if profit_growth:
                avg_growth = sum(profit_growth.values()) / len(profit_growth)
                if avg_growth >= 20:
                    result["analysis"].append(f"净利润年均增长 {avg_growth:.1f}% 高速增长")
                    result["score"] += 15
                elif avg_growth >= 10:
                    result["analysis"].append(f"净利润年均增长 {avg_growth:.1f}% 稳健增长")
                    result["score"] += 8
                elif avg_growth >= 0:
                    result["analysis"].append(f"净利润年均增长 {avg_growth:.1f}% 小幅增长")
                else:
                    result["analysis"].append(f"净利润年均增长 {avg_growth:.1f}% 下滑")
                    result["score"] -= 10

        result["score"] = min(100, max(0, result["score"]))

        if result["score"] >= 80:
            result["rating"] = "优秀"
        elif result["score"] >= 60:
            result["rating"] = "良好"
        elif result["score"] >= 40:
            result["rating"] = "一般"
        else:
            result["rating"] = "较差"

        return result

    def _analyze_risk(self, data: Dict) -> Dict:
        """分析财务风险"""
        result = {"score": 70, "analysis": [], "rating": "一般"}

        if "财务风险" not in data["indicators"]:
            return result

        indicators = data["indicators"]["财务风险"]
        years = data.get("years", [])
        if not years:
            return result

        latest_year = years[0]

        # 资产负债率
        if "资产负债率" in indicators:
            debt_ratio = indicators["资产负债率"].get(latest_year)
            if debt_ratio:
                ratio = float(debt_ratio) if debt_ratio else 0
                if ratio <= 40:
                    result["analysis"].append(f"资产负债率 {ratio:.1f}% 财务稳健")
                    result["score"] += 15
                elif ratio <= 60:
                    result["analysis"].append(f"资产负债率 {ratio:.1f}% 适中")
                    result["score"] += 5
                elif ratio <= 80:
                    result["analysis"].append(f"资产负债率 {ratio:.1f}% 较高")
                    result["score"] -= 10
                else:
                    result["analysis"].append(f"资产负债率 {ratio:.1f}% 风险较高")
                    result["score"] -= 20

        result["score"] = min(100, max(0, result["score"]))

        if result["score"] >= 80:
            result["rating"] = "低风险"
        elif result["score"] >= 60:
            result["rating"] = "中等"
        elif result["score"] >= 40:
            result["rating"] = "较高"
        else:
            result["rating"] = "高风险"

        return result


# 全局实例
_financial_provider = FinancialReportProvider()


def get_financial_abstract(stock_code: str) -> Optional[pd.DataFrame]:
    """获取财务摘要"""
    return _financial_provider.get_financial_abstract(stock_code)


def get_financial_data(stock_code: str) -> Optional[Dict]:
    """获取并整理财务数据"""
    return _financial_provider.get_financial_data(stock_code)


def analyze_financial_health(stock_code: str) -> Dict:
    """分析财务健康度"""
    data = get_financial_data(stock_code)
    if data:
        return _financial_provider.analyze_financial_health(data)
    return {}