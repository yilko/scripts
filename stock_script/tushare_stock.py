import csv
import datetime
import os
import warnings
from typing import Dict
import sys
import tushare
from pandas import DataFrame, concat, ExcelWriter
from encrypt_count import EncryptCount
from excel_style import ExcelStyle

'''
数据来源tushare，小概率某些股票不准，但是免费且次数比较多，暂定用这个
统计维度有四个
价格涨幅：当日价格与预设价格涨幅、当日价格与近十日/三十日最低价(收盘价)涨幅
近期涨幅：当日价格与近5/10/20/30/60/90/180天的价格涨幅
当日涨幅：近十日/三十日中每天最高价最低价涨幅超过5%(可改)的统计次数和最高/最低涨幅
成交量：近十日/三十日中每天成交量超过20w手(可改)的统计次数和最高/最低成交量

'''


class TushareStock:
    def __init__(self, stock_csv: str, stock_count: int, token: str):
        self.token = token
        self.stock_ls = self.__get_stock(stock_csv, stock_count)

    # 获取需要统计的股票列表
    @staticmethod
    def __get_stock(path, stock_count: int) -> list:
        with open(path, "r", encoding='utf-8') as f:
            r = csv.reader(f)
            # 转为列表，获取所有数据
            return list(r)[:stock_count]

    # 判断是深圳或上海股票
    @staticmethod
    def __check_stock_type(stock_code: str) -> str:
        if stock_code.startswith('6'):
            return f'{stock_code}.sh'
        elif stock_code.startswith(('0', '3', '2')):
            return f'{stock_code}.sz'

    # 获取指定股票近一年数据
    def get_data(self) -> Dict[str, DataFrame]:
        stock_dict = {}
        ts = tushare.pro_api(self.token)
        now = datetime.datetime.now()
        one_year = (now - datetime.timedelta(days=365)).strftime('%Y%m%d')

        for stock_info in self.stock_ls:
            stock_code = stock_info[0]
            tushare_code = self.__check_stock_type(stock_code)
            df = ts.daily(ts_code=tushare_code, start_date=one_year, end_date=now.strftime('%Y%m%d'))
            stock_dict[stock_code] = df
        # print(stock_dict)
        return stock_dict

    # 通过股票代码反拿my_stock.csv的数据
    def __get_pre_stock_info(self, stock_code) -> list:
        for info in self.stock_ls:
            if stock_code == info[0]:
                return info

    # 计算涨幅
    def calc_increase(self, data: dict):
        col_name = ['股票代码', '股票名称', '期望价格', '当天价格']
        add_name = ['近五天涨幅(%)', '近十天涨幅(%)', '近二十天涨幅(%)', '近一月涨幅(%)', '近两月涨幅(%)',
                    '近三月涨幅(%)', '近半年涨幅(%)']
        day_ls = [5, 10, 20, 30, 60, 90, 180]
        increase_df = DataFrame(columns=col_name + add_name)
        for stock_code, df in data.items():
            today = round(df.iloc[0]['close'], 4)
            pre_stock_info = self.__get_pre_stock_info(stock_code)
            increase_ls = []
            for i in range(len(day_ls)):
                try:
                    that_day = df.iloc[day_ls[i]]['close']
                    increase = round((today - that_day) / that_day, 4) * 100
                    increase_ls.append(increase)
                except Exception as e:
                    # 可能存在df.iloc[x]行数超出范围，默认补None
                    increase_ls.append(None)
            data = DataFrame([pre_stock_info + [today] + increase_ls], columns=col_name + add_name)
            increase_df = concat([increase_df, data])
        # print(increase_df.sort_values(increase_df.columns[4]))
        return increase_df.sort_values(increase_df.columns[7])

    # 计算当日涨幅
    def calc_max_min(self, data: dict, increase_flag: float):
        col_name = ['股票代码', '股票名称', '期望价格', '当天价格']
        add_name = ['近十日次数', '十日最大涨幅(%)', '十日最小涨幅(%)', '近一月次数', '一月最大涨幅(%)',
                    '一月最小涨幅(%)']
        max_min_df = DataFrame(columns=col_name + add_name)
        for stock_code, df in data.items():
            today = round(df.iloc[0]['close'], 4)
            pre_stock_info = self.__get_pre_stock_info(stock_code)
            max_min_ls = []
            ten_times, month_times = 0, 0
            for i in range(30):
                try:
                    high = round(df.iloc[i]['high'], 4)
                    low = round(df.iloc[i]['low'], 4)
                    max_min_increase = round((high - low) / low, 4)
                    max_min_ls.append(float(max_min_increase))
                except Exception as e:
                    # 可能存在df.iloc[x]行数超出范围，默认补None
                    max_min_ls.append(None)
            # print(max_min_ls)
            # 列表中存在None导致无法统计次数和计算最值，先过滤再计算
            filter_none_10_ls = [i for i in max_min_ls[:10] if i is not None]
            filter_none_ls = [i for i in max_min_ls if i is not None]
            for i in filter_none_10_ls:
                if i > increase_flag: ten_times += 1
            for i in filter_none_ls:
                if i > increase_flag: month_times += 1
            max_ten = max(filter_none_10_ls, default=0) * 100
            max_month = max(filter_none_ls, default=0) * 100
            min_ten = min(filter_none_10_ls, default=0) * 100
            min_month = min(filter_none_ls, default=0) * 100
            join_ls = [today, ten_times, max_ten, min_ten, month_times, max_month, min_month]
            data = DataFrame([pre_stock_info + join_ls], columns=col_name + add_name)
            max_min_df = concat([max_min_df, data])
        sort_col = [max_min_df.columns[7], max_min_df.columns[8]]
        return max_min_df.sort_values(sort_col, ascending=[False, False])

    # 计算成交量
    def calc_amount(self, data: dict, amount_flag: float):
        col_name = ['股票代码', '股票名称', '期望价格', '当天价格']
        add_name = ['近十日次数', '十日最大成交量(手)', '十日最小成交量(手)', '近一月次数', '一月最大成交量(手)',
                    '一月最小成交量(手)']
        amount_df = DataFrame(columns=col_name + add_name)
        for stock_code, df in data.items():
            today = round(df.iloc[0]['close'], 4)
            pre_stock_info = self.__get_pre_stock_info(stock_code)
            amount_ls = []
            ten_times, month_times = 0, 0
            for i in range(30):
                try:
                    amount = round(df.iloc[i]['vol'], 4)
                    amount_ls.append(float(amount))
                except Exception as e:
                    # 可能存在df.iloc[x]行数超出范围，默认补None
                    amount_ls.append(None)
            # print(amount_ls)
            # 列表中存在None导致无法统计次数和计算最值，先过滤再计算
            filter_none_10_ls = [i for i in amount_ls[:10] if i is not None]
            filter_none_ls = [i for i in amount_ls if i is not None]
            for i in filter_none_10_ls:
                if i > amount_flag: ten_times += 1
            for i in filter_none_ls:
                if i > amount_flag: month_times += 1
            # 过滤的列表为空，计算最值报错，默认值赋0
            max_ten = max(filter_none_10_ls, default=0)
            max_month = max(filter_none_ls, default=0)
            min_ten = min(filter_none_10_ls, default=0)
            min_month = min(filter_none_ls, default=0)
            join_ls = [today, ten_times, max_ten, min_ten, month_times, max_month, min_month]
            data = DataFrame([pre_stock_info + join_ls], columns=col_name + add_name)
            amount_df = concat([amount_df, data])
        sort_ls = [amount_df.columns[7], amount_df.columns[8]]
        return amount_df.sort_values(sort_ls, ascending=[False, False])

    # 计算设定价格与现价涨幅
    def calc_price_increase(self, data: dict):
        col_name = ['股票代码', '股票名称', '期望价格', '当天价格', '与期望价格涨幅(%)']
        add_name = ['近十天最低价', '与当天价格涨幅(%)', '近一月最低价', '与当天价格涨幅(%)']
        price_df = DataFrame(columns=col_name + add_name)
        for stock_code, df in data.items():
            today = round(df.iloc[0]['close'], 4)
            pre_stock_info = self.__get_pre_stock_info(stock_code)
            except_increase = round((today - float(pre_stock_info[2])) / float(pre_stock_info[2]), 4) * 100
            price_ls = []
            for i in range(1, 31):
                try:
                    price_ls.append(round(df.iloc[i]['close'], 4))
                except Exception as e:
                    # 可能存在df.iloc[x]行数超出范围，默认补None
                    price_ls.append(None)
            filter_none_10_ls = [i for i in price_ls[:10] if i is not None]
            filter_none_ls = [i for i in price_ls if i is not None]
            # 可能存在没这么多行报错
            # price_ls1 = [round(df.iloc[i]['close'], 4) for i in range(1, 31)]
            ten_min = min(filter_none_10_ls, default=0)
            ten_min_increase = round((today - ten_min) / ten_min, 4) * 100 if ten_min != 0 else 0
            month_min = min(filter_none_ls, default=0)
            month_min_increase = round((today - month_min) / month_min, 4) * 100 if month_min != 0 else 0
            add_ls = [today, except_increase, ten_min, ten_min_increase, month_min, month_min_increase]
            data = DataFrame([pre_stock_info + add_ls], columns=col_name + add_name)
            price_df = concat([price_df, data])
        # print(price_df.sort_values(price_df.columns[4]))
        return price_df.sort_values(price_df.columns[4])

    # 获取最新交易日
    @staticmethod
    def __get_last_day(data: dict):
        df = data[list(data.keys())[0]]
        return df.iloc[0]['trade_date']

    # 保存到excel
    def save_data(self, data: dict, df_dict: dict):
        folder_name = 'stock_excel'
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        last_day = self.__get_last_day(data)
        file_name = f'{folder_name}{os.path.sep}{last_day}.xlsx'
        writer = ExcelWriter(file_name)
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name, '无', index=False)
        writer.close()
        return file_name


if __name__ == '__main__':
    # 忽略 FutureWarning
    warnings.filterwarnings("ignore", category=FutureWarning)
    print('----------该程序不商用不收费，仅供个人学习使用----------')
    print('----------若他人获取后收费商用，由该本人承担一切后果----------')
    try:
        # 限定执行次数和分享
        te = EncryptCount('.config', 10, r"Software\MyStock", 'count')
        te.update_file(te.get_file_content())
        # 获取和保存数据
        print(f'----------正在获取数据并计算,当前可获取数据100条----------')
        ts = TushareStock('my_stock.csv', 100, sys.argv[3])
        d = ts.get_data()
        d1 = {
            '价格涨幅': ts.calc_price_increase(d),
            '近期涨幅': ts.calc_increase(d),
            '当日涨幅': ts.calc_max_min(d, float(sys.argv[1])),
            '成交量': ts.calc_amount(d, int(sys.argv[2]))
        }
        file_name = ts.save_data(d, d1)
        # excel调整样式
        ExcelStyle(file_name).adjust_style()
        print('----------计算完成，请查看stock_excel目录下是否生成xlsx文件----------')
        os.startfile(file_name)
    except FileNotFoundError as e:
        print(f'缺少相关配置文件或配置有误[r]，请联系相关人员')
        sys.exit(1)
