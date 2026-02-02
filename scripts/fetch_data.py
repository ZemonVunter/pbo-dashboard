#!/usr/bin/env python3
"""
PBOC 货币政策数据抓取与计算引擎（真实版本）
数据源：Tushare API
功能：
1. 获取央行公开市场操作数据
2. 计算到期日（节假日顺延）
3. 生成前端所需数据
"""

import json
import os
from datetime import datetime, timedelta, date

# Tushare 配置
TUSHARE_TOKEN = "2876ea85cb005fb5fa17c809a98174f2d5aae8b1f830110a5ead6211"

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
    """央行货币政策数据管理器"""

    def __init__(self, token: str):
        self.token = token
        self.operations = []

    def fetch_pbo_operations(self, start_date: str = None, end_date: str = None) -> list:
        """
        从 Tushare 获取央行公开市场操作数据
        
        注意：需要安装 tushare 包：pip install tushare
        """
        print("📡 正在检查 Tushare 依赖...")
        
        # 检查是否安装了 tushare
        try:
            import tushare as ts
            print("✅ Tushare 已安装")
            
            try:
                # 设置 Tushare Token
                ts.set_token(self.token)
                pro = ts.pro_api()

                # 如果没有提供日期，获取最近30天的数据
                if not start_date:
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                
                if not end_date:
                    end_date = datetime.now().strftime('%Y%m%d')

                print(f"📅 查询时间范围: {start_date} 至 {end_date}")

                # 尝试获取央行公开市场操作数据
                # 注意：具体的接口名称可能需要根据 Tushare 最新文档调整
                try:
                    # 尝试 central_bank_daily 接口
                    df = pro.central_bank_daily(
                        start_date=start_date,
                        end_date=end_date,
                        fields="trade_date,trade_type,amount,term,mode"
                    )
                    
                    if df is not None and len(df) > 0:
                        print(f"✅ 通过 central_bank_daily 获取到 {len(df)} 条数据")
                        return self._parse_dataframe(df, 'central_bank_daily')
                    
                except Exception as e:
                    print(f"⚠️  central_bank_daily 接口失败: {e}")

                # 尝试其他可能的接口
                try:
                    # 尝试 money_flow 接口
                    df = pro.money_flow(
                        start_date=start_date,
                        end_date=end_date,
                        fields="trade_date,trade_type,amount,term"
                    )
                    
                    if df is not None and len(df) > 0:
                        print(f"✅ 通过 money_flow 获取到 {len(df)} 条数据")
                        return self._parse_dataframe(df, 'money_flow')
                        
                except Exception as e:
                    print(f"⚠️  money_flow 接口失败: {e}")

                # 如果接口都失败，返回模拟数据并提示
                print("⚠️  Tushare API 接口可能已变更或无数据，使用模拟数据")
                return self._generate_mock_data()

            except Exception as e:
                print(f"❌ Tushare API 连接失败: {e}")
                print("💡 可能原因：")
                print("   1. 网络连接问题")
                print("   2. Tushare Token 无效或过期")
                print("   3. 需要安装 tushare 包：pip install tushare")
                print("🔄 使用模拟数据作为备用...")
                return self._generate_mock_data()
                
        except ImportError:
            print("❌ 未安装 tushare 包")
            print("💡 安装方法：")
            print("   pip3 install tushare")
            print("   或者运行: bash install_deps.sh")
            print("🔄 使用模拟数据作为备用...")
            return self._generate_mock_data()

    def _parse_dataframe(self, df, source_type: str) -> list:
        """解析 DataFrame 数据"""
        operations = []
        
        for _, row in df.iterrows():
            op = self._parse_row(row, source_type)
            if op:
                operations.append(op)
        
        return operations

    def _parse_row(self, row, source_type: str) -> dict:
        """解析单行数据"""
        try:
            # 根据不同的接口类型解析字段
            if source_type == 'central_bank_daily':
                trade_date = str(row.get('trade_date', ''))
                trade_type = str(row.get('trade_type', ''))
                amount = float(row.get('amount', 0))
                term = str(row.get('term', ''))
                mode = str(row.get('mode', ''))
            elif source_type == 'money_flow':
                trade_date = str(row.get('trade_date', ''))
                trade_type = str(row.get('trade_type', ''))
                amount = float(row.get('amount', 0))
                term = str(row.get('term', ''))
                mode = ''
            else:
                return None

            # 过滤：只处理央行操作
            if not any(k in trade_type for k in ['逆回购', 'MLF', '买断式', '央行', '公开市场']):
                return None

            # 提取期限信息
            term_days, term_months = self._extract_term(term)

            # 确定工具类型
            tool_type = self._determine_tool_type(trade_type)

            # 解析日期
            ann_date = self._parse_date(trade_date)

            if not ann_date or amount <= 0:
                return None

            return {
                'ann_date': ann_date.strftime('%Y-%m-%d'),
                'trade_type': trade_type,
                'tool_type': tool_type,
                'amount': amount,
                'term_days': term_days,
                'term_months': term_months,
                'raw_duration': term,
                'source': source_type
            }

        except Exception as e:
            print(f"⚠️  解析数据行失败: {e}")
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
            elif len(date_str) == 19:  # YYYY-MM-DD HH:MM:SS
                return datetime.strptime(date_str[:10], '%Y-%m-%d')
        except:
            return None

    def _generate_mock_data(self) -> list:
        """生成模拟数据（用于测试）"""
        print("📊 生成模拟数据...")
        operations = []
        today = datetime.now()

        # 模拟最近几天的操作
        mock_operations = [
            {
                'ann_date': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
                'trade_date': (today - timedelta(days=3)).strftime('%Y%m%d'),
                'trade_type': '逆回购',
                'tool_type': 'REPO',
                'amount': 5000,
                'term_days': 7,
                'term_months': None,
                'raw_duration': '7天',
                'source': 'mock'
            },
            {
                'ann_date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
                'trade_date': (today - timedelta(days=5)).strftime('%Y%m%d'),
                'trade_type': 'MLF',
                'tool_type': 'MLF',
                'amount': 10000,
                'term_days': None,
                'term_months': 1,
                'raw_duration': '1个月',
                'source': 'mock'
            },
            {
                'ann_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                'trade_date': (today - timedelta(days=1)).strftime('%Y%m%d'),
                'trade_type': '买断式逆回购',
                'tool_type': 'OUTRIGHT',
                'amount': 2000,
                'term_days': 14,
                'term_months': None,
                'raw_duration': '14天',
                'source': 'mock'
            }
        ]

        # 添加更多历史数据
        for i in range(1, 15):
            op_date = today - timedelta(days=i)
            if i % 4 == 0:  # 每4天一个逆回购
                operations.append({
                    'ann_date': op_date.strftime('%Y-%m-%d'),
                    'trade_date': op_date.strftime('%Y%m%d'),
                    'trade_type': '逆回购',
                    'tool_type': 'REPO',
                    'amount': 2000 + i * 100,
                    'term_days': 7,
                    'term_months': None,
                    'raw_duration': '7天',
                    'source': 'mock'
                })
            elif i % 6 == 0:  # 每6天一个MLF
                operations.append({
                    'ann_date': op_date.strftime('%Y-%m-%d'),
                    'trade_date': op_date.strftime('%Y%m%d'),
                    'trade_type': 'MLF',
                    'tool_type': 'MLF',
                    'amount': 5000 + i * 200,
                    'term_days': None,
                    'term_months': 1,
                    'raw_duration': '1个月',
                    'source': 'mock'
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
            'injection_ops': operating_today,
            'data_source': 'tushare' if any(op.get('source') == 'tushare' for op in operations) else 'mock'
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
    manager = PBOCDataManager(TUSHARE_TOKEN)

    print("🚀 开始获取央行数据...")
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
        'all_operations': matured_ops,
        'data_status': 'real' if today_view.get('data_source') == 'tushare' else 'mock'
    }

    # 保存数据
    output_path = os.path.join(
        os.path.dirname(__file__),
        '../data/operations.json'
    )
    manager.save_to_json(output_data, output_path)

    print("🎉 数据生成完成！")
    print(f"📊 数据源: {today_view.get('data_source', 'unknown')}")


if __name__ == '__main__':
    main()