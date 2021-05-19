import pandas as pd
import time
from chart_constants import COUNTRY_NAME_ENGLISH_TO_CHINESE, ProvinceNameType, PROVINCE_NAME_ABBR_MAPS, PROVINCE_NAME_SINGLE_WORD_MAPS


# 删除首尾特定的几行
def delete_rows(source_file, save_file, head_rows_num=0, tail_rows_num=0, source_encode='utf-8'):
    with open(source_file, encoding=source_encode) as f:
        lines = f.readlines()
    lines = lines[head_rows_num:-tail_rows_num]
    with open(save_file, 'w') as f:
        f.writelines(lines)
    time.sleep(1)


# 处理苏联数据
def handle_ussr_data(df_arg):
    df_columns = set(df_arg.columns.values)

    if '苏联' in df_columns and input('已有苏联数据，是否继续 y/n') != 'y':
        return df_arg

    # https://zh.m.wikipedia.org/zh-hans/%E8%8B%8F%E8%81%94%E5%8A%A0%E7%9B%9F%E5%85%B1%E5%92%8C%E5%9B%BD
    # 苏联是1922年12月30日成立的
    # 假设某个国家于1936年加入苏联，那么其数据从1937年开始计入苏联，也就是从次年开始计算
    # 以下国家大多在1991.01 ~ 1991.12之间独立
    ussr_countries_list = [
        # 1922年加入苏联
        ['俄罗斯', '乌克兰', '白俄罗斯', '阿塞拜疆', '格鲁吉亚', '亚美尼亚'],
        # 1924年加入苏联
        ['乌兹别克斯坦', '土库曼斯坦'],
        # 1929年加入苏联
        ['塔吉克斯坦'],
        # 1936年加入苏联
        ['吉尔吉斯斯坦', '哈萨克斯坦'],
        # 1940年加入苏联
        ['拉脱维亚', '爱沙尼亚', '立陶宛', '摩尔多瓦']
    ]
    df_row_count = df_arg.shape[0]
    total_ussr_countries = []

    for country_list in ussr_countries_list:
        total_ussr_countries += country_list

    # 填充数据
    for country in total_ussr_countries:
        if country not in df_columns:
            df_arg[country] = [0] * df_row_count

    df_arg['苏联'] = [0] * df_arg.shape[0]

    s1 = df_arg.loc[1923:1991, ussr_countries_list[0]].sum(axis=1)
    s2 = df_arg.loc[1925:1991, ussr_countries_list[1]].sum(axis=1)
    s3 = df_arg.loc[1930:1991, ussr_countries_list[2]].sum(axis=1)
    s4 = df_arg.loc[1937:1991, ussr_countries_list[3]].sum(axis=1)
    s5 = df_arg.loc[1941:1991, ussr_countries_list[4]].sum(axis=1)

    for s in [s1, s2, s3, s4, s5]:
        df_arg['苏联'] = df_arg['苏联'].add(s, fill_value=0)

    # 加盟共和国这段时间的数据为0，防止出现在表格上面
    df_arg.loc[1923:1991, ussr_countries_list[0]] = 0
    df_arg.loc[1925:1991, ussr_countries_list[1]] = 0
    df_arg.loc[1930:1991, ussr_countries_list[2]] = 0
    df_arg.loc[1937:1991, ussr_countries_list[3]] = 0
    df_arg.loc[1941:1991, ussr_countries_list[4]] = 0

    return df_arg


# 捷克斯洛伐克数据
# 1918 ~ 1992
def handle_czechoslovakia_data(df_arg):
    df_columns = set(df_arg.columns.values)
    df_blank_data = [0] * df_arg.shape[0]
    dissolved_country = '捷克斯洛伐克'

    if dissolved_country in df_columns and input(f'已有{dissolved_country}数据，是否继续 y/n') != 'y':
        return df_arg

    df_arg[dissolved_country] = df_blank_data
    country_list = ['捷克', '斯洛伐克']
    # 填充数据
    for country in country_list:
        if country not in df_columns:
            df_arg[country] = df_blank_data

    df_arg[dissolved_country] = df_arg.loc[1919:1992, country_list].sum(axis=1)
    df_arg.loc[1919:1992, country_list] = 0
    return df_arg


def merge_china_sar_data(df):
    # 合并港澳台
    area_list = ['中国香港', '中国澳门', '中国台湾']
    for area in area_list:
        if area in df.columns:
            df['中国'] += df[area]
    df.drop(['中国香港', '中国澳门', '中国台湾'], axis=1, inplace=True, errors="ignore")
    return df


def rename_china_province_name(df, name_type):
    # rename
    if name_type is ProvinceNameType.SINGLE_WORD:
        df.rename(columns=PROVINCE_NAME_SINGLE_WORD_MAPS, inplace=True)
    elif name_type is ProvinceNameType.ABBR:
        df.rename(columns=PROVINCE_NAME_ABBR_MAPS, inplace=True)
    return df


def merge_ethiopia_pdr_data(df):
    column_to_merge = '埃塞俄比亚人民民主共和国'
    if column_to_merge not in df.columns:
        return df
    df['埃塞俄比亚'] = df['埃塞俄比亚'].fillna(df[column_to_merge])
    df.drop([column_to_merge], axis=1, inplace=True, errors="ignore")
    return df


def remove_china_sar_data(df):
    df.drop(['中国香港', '中国澳门', '中国台湾'], axis=1, inplace=True, errors="ignore")
    return df


# 合并联合国粮农组织的最新数据
# http://www.fao.org/faostat/en/?#data
def merge_fao_data(df, fao_file_path):
    fao_df = pd.read_csv(fao_file_path)

    data_dict = dict(zip(fao_df['Area'].values, fao_df['Value'].values))
    data_dict[df.index.name] = df.index[-1]

    fao_df = pd.DataFrame([data_dict]).set_index(df.index.name)
    fao_df.rename(columns=COUNTRY_NAME_ENGLISH_TO_CHINESE, inplace=True)
    df.update(fao_df)
    return df
