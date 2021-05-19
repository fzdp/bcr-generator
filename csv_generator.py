import pandas as pd
import os
from chart_constants import *
from dataclasses import dataclass
# from typing import Callable
from csv_util import delete_rows


@dataclass
class CSVGenerator:
    original_csv_path: str
    real_csv_path: str
    csv_source: CSVSource
    columns_to_keep: [str] = None
    index_name: str = "Time"

    # 行列互换
    def transpose_csv(self, csv_path, save_path, column_to_rename="Unnamed: 0"):
        data = pd.read_csv(csv_path)
        data.rename(columns={column_to_rename: self.index_name}, inplace=True)
        data.set_index(self.index_name, inplace=True)
        data = data.transpose()
        data.to_csv(save_path)

        data = pd.read_csv(save_path)
        data.rename(columns={"Unnamed: 0": self.index_name}, inplace=True)
        data.to_csv(save_path, index=False)

    # 表格中实际涉及到的种类名称
    def find_total_categories(self, top_n):
        df = pd.read_csv(self.real_csv_path, index_col=self.index_name)
        total = []
        for i in range(len(df)):
            s = df.iloc[i].sort_values(ascending=False).head(top_n)
            values = s.index.values.tolist()
            total += values

        # 注意：每次运行结果的次序不一致
        total = set(total)
        all_countries = set(COUNTRY_COLORS.keys())
        unavailable_countries = list(total - all_countries)

        total = list(total)
        print(f'前{top_n}名排行榜实际涉及到的种类个数为：{len(total)}')
        for item in total:
            print(item)

        print("*" * 30)

        print(f'当前需要补充的种类个数为：{len(unavailable_countries)}')
        for item in unavailable_countries:
            print(item)

        return total
    
    def delete_data(self, csv_path, column_name_list=None, row_name_list=None):
        df = pd.read_csv(csv_path, index_col=self.index_name)
        if column_name_list:
            df.drop(column_name_list, axis=1, inplace=True, errors="ignore")
        if row_name_list:
            df.drop(row_name_list, inplace=True, errors="ignore")
        df.to_csv(csv_path)

    def rename_data(self, csv_path, column_name_dict):
        df = pd.read_csv(csv_path, index_col=self.index_name)
        df.rename(columns=column_name_dict, inplace=True)
        df.to_csv(csv_path)

    # 数据处理，例如处理数据空值，合并行列等
    def process(self, process_period, process_func, is_saving=True, is_index=True):
        if process_period == "pre":
            csv_path = self.original_csv_path
        elif process_period == "post":
            csv_path = self.real_csv_path
        else:
            print('unknown process period')
            return

        if is_index:
            index_col = self.index_name
        else:
            index_col = None

        df = pd.read_csv(csv_path, index_col=index_col)
        df = process_func(df)
        if is_saving:
            df.to_csv(self.real_csv_path, index=is_index)

    # 初步的数据预处理
    def generate(self, *args, **kwargs):
        if self.csv_source is CSVSource.NO_NEED_PREPROCESS:
            return
        # if os.path.exists(self.real_csv_path) and input(f"{self.real_csv_path}已经存在，是否继续？(y/n)") == "n":
        #     return
        if self.csv_source is CSVSource.WORLD_BANK:
            self.handle_world_bank_data(*args, **kwargs)
        elif self.csv_source is CSVSource.OUR_WORLD_IN_DATA:
            self.handle_our_world_in_data(*args, **kwargs)
        elif self.csv_source is CSVSource.STATS_GOV:
            self.handle_stats_gov_data(*args, **kwargs)
        elif self.csv_source is CSVSource.BGS_MINERALS:
            self.handle_bgs_minerals_data(*args, **kwargs)
        elif self.csv_source is CSVSource.UN_DATA:
            self.handle_un_data(*args, **kwargs)
        else:
            print('文件来源有误')

    # world bank数据预处理
    # 一开始需要手动处理一下！为了进行数据勘误
    def handle_world_bank_data(self, *args, **kwargs):
        self.transpose_csv(self.original_csv_path, self.real_csv_path, 'Country Name')
        if self.columns_to_keep is None:
            columns_to_delete = WORLD_BANK_COLUMNS_TO_DELETE
        else:
            columns_to_delete = list(set(WORLD_BANK_COLUMNS_TO_DELETE) - set(self.columns_to_keep))
        self.delete_data(self.real_csv_path, column_name_list=columns_to_delete,
                         row_name_list=WORLD_BANK_ROWS_TO_DELETE)
        self.rename_data(self.real_csv_path, column_name_dict=COUNTRY_NAME_MAPS)

    # BGS数据处理
    def handle_bgs_minerals_data(self, *args, **kwargs):
        df_list = []
        for file in sorted(os.listdir(self.original_csv_path)):
            df_list.append(pd.read_csv(f"{self.original_csv_path}/{file}", index_col=0))
        df = pd.concat(df_list, axis=1)
        df.to_csv(self.real_csv_path)
        data = pd.read_csv(self.real_csv_path)
        print(data.columns)
        self.transpose_csv(self.real_csv_path, self.real_csv_path)

    # 国家统计局数据预处理
    def handle_stats_gov_data(self, *args, **kwargs):
        with open(self.original_csv_path, encoding='gbk') as f:
            lines = f.readlines()
        i = -1
        while lines[i][:4] not in ['新疆维吾', '乌鲁木齐']:
            i -= 1
        tail_rows = (-i) - 1

        delete_rows(
            self.original_csv_path, self.real_csv_path, head_rows_num=3,
            tail_rows_num=tail_rows, source_encode='gbk'
        )
        self.transpose_csv(self.real_csv_path, self.real_csv_path, '地区')

        df = pd.read_csv(self.real_csv_path)
        # 2019年 => 2019
        time_values = df[self.index_name].values
        time_values = list(map(lambda v: int(v[:-1]), time_values))
        df[self.index_name] = time_values
        # reverse
        df = df.iloc[::-1]

        if 'year_list' in kwargs:
            year_list = kwargs['year_list']
            df.set_index(self.index_name, inplace=True)
            df = df.reindex(year_list)
            df.to_csv(self.real_csv_path, index=True)
        else:
            df.to_csv(self.real_csv_path, index=False)

    # ourworldindata.org的数据预处理
    # 注意，处理好了之后还需要翻译
    # 1. 多个category一个entity；2.一个category多个entity
    def handle_our_world_in_data(self, country_name=None, category_name=-1,
                                 translate_country_name=True, year_list=None, **kwargs):
        # 表示选中所有的category
        # Time,category1,category2,...
        # 1996,0.1,0.2,...
        # 1997,06,0.9,...
        if country_name is not None:
            df = pd.read_csv(self.original_csv_path)
            df = df[df['Entity'] == country_name]
            df.drop(['Entity', 'Code'], axis=1, inplace=True, errors="ignore")
            df.rename(columns={'Year': self.index_name}, inplace=True)
            df.fillna(value=0, inplace=True)
            df.to_csv(self.real_csv_path, index=False)
        # 表示选中所有的country或者说是entity
        # Time,country1,country2,...
        # 1996,0.1,0.2,...
        # 1997,06,0.9,...
        elif category_name is not None:
            df = pd.read_csv(self.original_csv_path, index_col='Year')
            # column下标
            if isinstance(category_name, int):
                category_name = df.columns[category_name]

            # 例如有的国家数据时间段是从1990~2000，而有的国家数据则是从1960~2000，太阳能发电量数据就是如此
            if year_list is None:
                year_list = sorted(df.index.unique().values)
            entity_list = list(set(df['Entity'].unique()) - set(WORLD_AREAS_TO_DELETE))

            new_df = pd.DataFrame({self.index_name: year_list})

            for entity_name in entity_list:
                entity_df = df[df['Entity'] == entity_name]
                # 如果这个国家的year index和指定的year index一致，就不需要reindex了！
                if entity_df.index.values.tolist() != year_list:
                    # reindex相当于只截取特定的时间段，如果时间段不存在则用0填充空数据，如果时间段已存在数据不变化
                    entity_df = entity_df.reindex(year_list, fill_value='')
                new_df[entity_name] = entity_df[category_name].values

            if translate_country_name:
                new_df.rename(columns=COUNTRY_NAME_ENGLISH_TO_CHINESE, inplace=True)
            new_df.to_csv(self.real_csv_path, index=False)

    # http://data.un.org/Explorer.aspx
    def handle_un_data(self, value_column_name=-1, entity_column_name=0, index_column="Year", translate_country_name=True, year_list=None, **kwargs):
        df = pd.read_csv(self.original_csv_path, index_col=index_column)
        df.drop(['fnSeqID', '1'], axis=1, inplace=True, errors="ignore")

        # column下标
        if isinstance(value_column_name, int):
            value_column_name = df.columns[value_column_name]
        if isinstance(entity_column_name, int):
            entity_column_name = df.columns[entity_column_name]

        # 例如有的国家数据时间段是从1990~2000，而有的国家数据则是从1960~2000，太阳能发电量数据就是如此
        if year_list is None:
            year_list = sorted(df.index.unique().values)
        entity_list = list(set(df[entity_column_name].unique()) - set(WORLD_AREAS_TO_DELETE))

        new_df = pd.DataFrame({self.index_name: year_list})

        for entity_name in entity_list:
            entity_df = df[df[entity_column_name] == entity_name]
            # 如果这个国家的year index和指定的year index一致，就不需要reindex了！
            if entity_df.index.values.tolist() != year_list:
                # reindex相当于只截取特定的时间段，如果时间段不存在则用空值填充空数据，如果时间段已存在数据不变化
                entity_df = entity_df.reindex(year_list, fill_value='')
            new_df[entity_name] = entity_df[value_column_name].values

        if translate_country_name:
            new_df.rename(columns=COUNTRY_NAME_ENGLISH_TO_CHINESE, inplace=True)
        new_df.to_csv(self.real_csv_path, index=False)
