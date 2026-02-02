#!/usr/bin/env python3
"""
PBOC 货币政策数据抓取与计算引擎（模拟版本）
数据源：模拟数据（用于测试界面）
功能：
1. 模拟获取央行公开市场操作数据
2. 计算到期日（节假日顺延）
3. 生成前端所需数据
"""

import json
import os
from datetime import datetime, timedelta, date

# 简化的节假日判断（2026年中国法定节假日）
def is_holiday(date_obj: datetime) -> bool:
    """判断是否是节假日（简化版）"""
    year = date_obj.year
    month = date_obj.month
    day = date_obj.day
    
    # 固定节假日
    holidays = [
        # 元旦
        (1, 1),
        # 春节（2026年：1月28日-2月3日）
        (1, 28), (1, 29), (1, 30), (1, 31),
        (2, 1), (2, 2), (2, 3),
        # 清明节
        (4, 4), (4, 5), (4, 6),
        # 劳动节
        (5, 1), (5, 2), (5, 3),
        # 端午节
        (6, 19), (6, 20), (6, 21),
        # 中秋节
        (9, 25), (9, 26), (9, 27),
        # 国庆节
        (10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7),
    ]
    
    return (month, day) in holidays

def is_workday(date_obj: datetime) -> bool:
    """判断是否是工作日"""
    # 周末不是工作日
    if date_obj.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
    
    # 节假日不是工作日
    return not is_holiday(date_obj)

class PBOCDataManager:
    """央行货币政策数据管理器（模拟版本）"""

    def __init__(self):
        self.operations = []

    def fetch_pbo_operations(self, start_date: str = None, end_date: str = None) -> list:
        """
        模拟获取央行公开市场操作数据
        在实际使用中，这里会调用 Tushare API
        """
        print("📡 正在模拟获取央行数据...")
        
        # 生成模拟数据（最近7天的操作）
        operations = []
        today = datetime.now()
        
        # 模拟最近几天的操作
        mock_operations = [
            {
                'ann_date': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
                'trade_type': '逆回购',
                'tool_type': 'REPO',
                'amount': 5000,
                'term_days': 7,
                'term_months': None,
                'raw_duration': '7天'
            },
            {
                'ann_date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
                'trade_type': 'MLF',
                'tool_type': 'MLF',
                'amount': 10000,
                'term_days': None,
                'term_months': 1,
                'raw_duration': '1个月'
            },
            {
                'ann_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                'trade_type': '买断式逆回购',
                'tool_type': 'OUTRIGHT',
                'amount': 2000,
                'term_days': 14,
                'term_months': None,
                'raw_duration': '14天'
            },
            {
                'ann_date': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
                'trade_type': '逆回购',
                'tool_type': 'REPO',
                'amount': 3000,
                'term_days': 14,
                'term_months': None,
                'raw_duration': '14天'
            }
        ]
        
        # 添加更多历史数据
        for i in range(1, 20):
            op_date = today - timedelta(days=i)
            if i % 4 == 0:  # 每4天一个逆回购
                operations.append({
                    'ann_date': op_date.strftime('%Y-%m-%d'),
                    'trade_type': '逆回购',
                    'tool_type': 'REPO',
                    'amount': 2000 + i * 100,
                    'term_days': 7,
                    'term_months': None,
                    'raw_duration': '7天'
                })
            elif i % 6 == 0:  # 每6天一个MLF
                operations.append({
                    'ann_date': op_date.strftime('%Y-%m-%d'),
                    'trade_type': 'MLF',
                    'tool_type': 'MLF',
                    'amount': 5000 + i * 200,
                    'term_days': None,
                    'term_months': 1,
                    'raw_duration': '1个月'
                })
        
        operations.extend(mock_operations)
        
        # 按日期排序
        operations.sort(key=lambda x: x['ann_date'], reverse=True)
        
        return operations

    def calculate_maturity(self, operations: list) -> list:
        """
        计算到期日（节假日顺延）
        """
        matured_operations = []

        for op in operations:
            ann_date = datetime.strptime(op['ann_date'], '%Y-%m-%d')
            if not ann_date:
                continue

            # 计算到期日
            maturity_date = ann_date

            if op['term_days']:
                maturity_date += timedelta(days=op['term_days'])
            elif op['term_months']:
                # 一个月约等于30天
                maturity_date += timedelta(days=op['term_months'] * 30)

            # 节假日顺延
            matured_date = self._adjust_for_holidays(maturity_date)

            matured_operations.append({
                **op,
                'maturity_date': matured_date.strftime('%Y-%m-%d'),
                'is_weekend': not is_workday(maturity_date)
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

        return adjusted_date

    def calculate_daily_view(self, operations: list, target_date: str = None) -> dict:
        """
        计算每日看板数据
        """
        if target_date:
            target = datetime.strptime(target_date, '%Y-%m-%d')
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
                'is_holiday': is_holiday(check_date)
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
    manager = PBOCDataManager()

    print("📡 开始获取央行数据...")
    operations = manager.fetch_pbo_operations()

    if not operations:
        print("⚠️  未获取到数据")
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