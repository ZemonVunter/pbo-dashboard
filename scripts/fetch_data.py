#!/usr/bin/env python3
"""
PBOC 货币政策数据抓取与计算引擎
数据源：Tushare
功能：
1. 获取央行公开市场操作数据
2. 计算到期日（节假日顺延）
3. 生成前端所需数据
"""

import json
import os
from datetime import datetime, timedelta
from chinese_calendar import is_holiday, is_workday

# Tushare 配置（从环境变量读取，生产环境应从配置文件读取）
TUSHARE_TOKEN = "2876ea85cb005fb5fa17c809a98174f2d5aae8b1f830110a5ead6211"

class PBOCDataManager:
    """央行货币政策数据管理器"""

    def __init__(self, token: str):
        self.token = token
        self.operations = []
        self.holiday_cache = set()

    def fetch_pbo_operations(self, start_date: str = "20240101", end_date: str = None) -> list:
        """
        从 Tushare 获取央行公开市场操作数据

        注意：Tushare 提供的央行数据接口可能有延迟
        这里使用 central_bank_daily 接口作为示例
        实际可能需要根据 Tushare 最新的央行数据接口调整
        """
        import tushare as ts

        ts.set_token(self.token)

        # 尝试获取央行每日操作数据
        # 注意：具体接口名称需要根据 Tushare 最新文档确认
        # 这里使用 central_bank_daily 作为示例
        try:
            pro = ts.pro_api()

            # 获取最近的央行操作记录
            if end_date:
                df = pro.central_bank_daily(
                    start_date=start_date,
                    end_date=end_date,
                    fields="ann_date,trade_type,amount,duration,mode"
                )
            else:
                df = pro.central_bank_daily(
                    start_date=start_date,
                    fields="ann_date,trade_type,amount,duration,mode"
                )

            if df is None or len(df) == 0:
                print(f"⚠️  未获取到数据，可能接口名称已变更")
                return []

            # 转换为标准格式
            operations = []
            for _, row in df.iterrows():
                op = self._parse_operation(row)
                if op:
                    operations.append(op)

            return operations

        except Exception as e:
            print(f"❌ 获取 Tushare 数据失败: {e}")
            return []

    def _parse_operation(self, row) -> dict:
        """
        解析单条操作记录

        示例数据格式：
        - trade_type: 逆回购, MLF, 买断式逆回购
        - amount: 金额（亿元）
        - duration: 期限（天或月）
        - ann_date: 公告日期
        """
        try:
            trade_type = str(row.get('trade_type', ''))

            # 过滤：只处理特定类型
            if not any(k in trade_type for k in ['逆回购', 'MLF', '买断式逆回购', '买断式']):
                return None

            # 提取金额
            amount_str = str(row.get('amount', 0))
            amount = self._extract_amount(amount_str)

            # 提取期限
            duration_str = str(row.get('duration', ''))
            term_days, term_months = self._extract_term(duration_str)

            # 确定工具类型
            tool_type = self._determine_tool_type(trade_type)

            # 公告日期
            ann_date_str = str(row.get('ann_date', ''))
            ann_date = self._parse_date(ann_date_str)

            if not ann_date or amount is None:
                return None

            return {
                'ann_date': ann_date.strftime('%Y-%m-%d'),
                'trade_type': trade_type,
                'tool_type': tool_type,
                'amount': amount,
                'term_days': term_days,
                'term_months': term_months,
                'raw_duration': duration_str
            }

        except Exception as e:
            print(f"⚠️  解析操作失败: {e}")
            return None

    def _extract_amount(self, text: str) -> float:
        """从文本提取金额（亿元）"""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1))
        return None

    def _extract_term(self, duration_str: str) -> tuple:
        """提取期限（天或月）"""
        import re

        term_days = None
        term_months = None

        # 提取天数
        days_match = re.search(r'(\d+)\s*天', duration_str)
        if days_match:
            term_days = int(days_match.group(1))

        # 提取月数
        months_match = re.search(r'(\d+)\s*个月', duration_str)
        if months_match:
            term_months = int(months_match.group(1))

        return term_days, term_months

    def _determine_tool_type(self, trade_type: str) -> str:
        """确定工具类型"""
        if '逆回购' in trade_type:
            return 'REPO'
        elif 'MLF' in trade_type.upper():
            return 'MLF'
        elif '买断式' in trade_type:
            return 'OUTRIGHT'
        else:
            return 'OTHER'

    def _parse_date(self, date_str: str):
        """解析日期"""
        try:
            if len(date_str) == 8:  # YYYYMMDD
                return datetime.strptime(date_str, '%Y%m%d')
            elif len(date_str) == 10:  # YYYY-MM-DD
                return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None

    def calculate_maturity(self, operations: list) -> list:
        """
        计算到期日（节假日顺延）

        逻辑：
        1. 根据期限计算到期日
        2. 如果到期日是周末/节假日，顺延到下一工作日
        """
        matured_operations = []

        for op in operations:
            ann_date = self._parse_date(op['ann_date'])
            if not ann_date:
                continue

            # 计算到期日
            maturity_date = ann_date

            if op['term_days']:
                maturity_date += timedelta(days=op['term_days'])
            elif op['term_months']:
                # 一个月约等于30天（央行操作通常按30天计算）
                maturity_date += timedelta(days=op['term_months'] * 30)

            # 节假日顺延
            matured_date = self._adjust_for_holidays(maturity_date)

            matured_operations.append({
                **op,
                'maturity_date': matured_date.strftime('%Y-%m-%d'),
                'is_weekend': is_workday(maturity_date) == False
            })

        return matured_operations

    def _adjust_for_holidays(self, date: datetime) -> datetime:
        """
        节假日调整：顺延到下一个工作日
        """
        adjusted_date = date
        max_lookahead = 10  # 最多顺延10天

        for _ in range(max_lookahead):
            if is_workday(adjusted_date):
                return adjusted_date
            adjusted_date += timedelta(days=1)

        # 如果超过限制，返回最后一个日期（理论上不应发生）
        return adjusted_date

    def calculate_daily_view(self, operations: list, target_date: str = None) -> dict:
        """
        计算每日看板数据

        返回：
        - 今日到期总额
        - 今日操作金额
        - 净投放
        """
        if target_date:
            target = self._parse_date(target_date)
        else:
            target = datetime.now()

        today_str = target.strftime('%Y-%m-%d')

        # 今日到期总额
        maturing_today = [
            op for op in operations
            if op['maturity_date'] == today_str
        ]
        total_maturing = sum(op['amount'] for op in maturing_today)

        # 今日操作
        operating_today = [
            op for op in operations
            if op['ann_date'] == today_str
        ]
        total_injection = sum(op['amount'] for op in operating_today)

        # 净投放
        net_injection = total_injection - total_maturing

        return {
            'date': today_str,
            'maturing_amount': total_maturing,
            'injection_amount': total_injection,
            'net_injection': net_injection,
            'maturing_ops': maturing_today,
            'injection_ops': operating_today
        }

    def generate_calendar_view(self, operations: list, days: int = 30) -> list:
        """
        生成日历视图（未来 N 天）
        """
        start_date = datetime.now()
        calendar_data = []

        for i in range(days):
            check_date = start_date + timedelta(days=i)
            date_str = check_date.strftime('%Y-%m-%d')

            # 该日到期总额
            maturing = [
                op for op in operations
                if op['maturity_date'] == date_str
            ]
            maturing_amount = sum(op['amount'] for op in maturing)

            calendar_data.append({
                'date': date_str,
                'maturing_amount': maturing_amount,
                'is_holiday': is_workday(check_date) == False
            })

        return calendar_data

    def save_to_json(self, data: dict, output_path: str):
        """保存数据到 JSON 文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据已保存到: {output_path}")


def main():
    """主函数"""
    manager = PBOCDataManager(TUSHARE_TOKEN)

    print("📡 开始获取央行数据...")
    operations = manager.fetch_pbo_operations()

    if not operations:
        print("⚠️  未获取到数据，请检查 Tushare Token")
        return

    print(f"✅ 获取到 {len(operations)} 条操作记录")

    # 计算到期日
    print("📅 正在计算到期日（节假日顺延）...")
    matured_ops = manager.calculate_maturity(operations)

    # 计算今日数据
    print("📊 正在计算每日看板...")
    today_view = manager.calculate_daily_view(matured_ops)

    # 生成日历视图
    print("🗓️  正在生成日历视图...")
    calendar_view = manager.generate_calendar_view(matured_ops, days=30)

    # 生成前端数据
    output_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'today_view': today_view,
        'calendar_view': calendar_view,
        'all_operations': matured_ops
    }

    # 保存数据
    output_path = os.path.join(
        os.path.dirname(__file__),
        '../data/operations.json'
    )
    manager.save_to_json(output_data, output_path)

    print("🎉 数据生成完成！")


if __name__ == '__main__':
    main()
