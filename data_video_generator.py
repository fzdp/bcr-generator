import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Rectangle
from matplotlib.dates import DateFormatter, MonthLocator, date2num
import matplotlib.animation as animation
from chart_constants import COUNTRY_COLORS, GENERIC_COLORS, ChartCategoryIconPosition, BarColorType, StatisticsTime, ChartType, CategoryLabelPosition
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import time
import os
import math
from dataclasses import dataclass
import numpy as np
from typing import Callable
import random
import configparser


# macOS系统上的中文处理
plt.rcParams['axes.unicode_minus'] = False
# 需要修改~/.matplotlib/fontlist-v330.json
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['STHeiti Medium']
# plt.rcParams['figure.constrained_layout.use'] = True


@dataclass
class DataVideoGenerator:
    chart_type: ChartType
    csv_path: str
    output_dir: str
    statistics_time: StatisticsTime
    chart_category_icon_position: ChartCategoryIconPosition
    category_label_position: CategoryLabelPosition = CategoryLabelPosition.RIGHT
    rows_in_column: int = 10
    is_preview_mode: bool = False
    index_col: str = "Time"
    # https://pyformat.info/
    # 注意：添加了x，为了兼容matplotlib的默认参数
    number_format: str = "{x:}"
    # 空值填充
    fill_na_value: int = -1
    # todo 目前是通过是否大于0来判断有无数据的，可能会导致bug！
    na_value_display_text: str = '无数据'
    bar_color_type: BarColorType = BarColorType.RANDOM_COLOR
    # bar的颜色只有一种，优先级高于COUNTRY_COLOR和RANDOM_COLOR
    bar_color: str = None
    background_image_path: str = None
    background_image_alpha: float = None
    preview_frame_count: int = None
    preview_frame_index: int = None
    chart_bar_width: float = 0.3
    frame_interval: int = 50
    number_rotation: int = -60
    # 相邻两个数据之间出现的时间间隔
    period_duration: int = 2500
    # 相邻的排名动画过渡时间
    rank_transition_duration: int = None
    video_dpi: int = 120
    video_aspect_ratio: tuple = (16, 9)
    chart_top_n: int = None
    is_show_grid: bool = True
    grid_axis: str = 'both'
    grid_line_style: str = '-'
    chart_category_icon_zoom: float = 1
    # 某个种类单独在时间文字区域显示
    summary_category: str = None
    summary_category_display_name: str = None
    summary_category_color: str = "#f6c90e"
    category_x_offset: float = None
    category_y_offset: float = None
    number_x_offset: float = None
    number_y_offset: float = None
    icon_x_offset: float = None
    category_icons_dir: str = None
    bar_height: float = 0.75
    chart_number_font_size: int = None
    tick_label_format: str = "{x:.0f}"
    chart_category_font_size: int = 26
    category_font_name: str = "DIY_category"
    chart_time_font_size: int = 120
    # ~/.matplotlib/fontlist-v330.json
    time_font_name: str = "Hiragino Sans"
    chart_left_pad: float = None
    chart_right_pad: float = None
    chart_top_pad: float = None
    chart_bottom_pad: float = None
    chart_number_color: str = '#4a4a48'
    rank_number_color: str = '#ffffff'
    rank_number_font_size: int = 16
    chart_category_color: str = None
    chart_time_color: str = '#ffbd69'
    chart_grid_line_color: str = '#47555e'
    time_x_position: float = 0.98
    time_y_position: float = 0.12
    # 最后一帧定格时间，单位：毫秒
    last_frame_duration: int = 5000
    # 开始一帧定格时间
    first_frame_duration: int = 1000
    number_font_name: str = "DIY_number"
    number_font_weight: str = "1000"
    # 是否允许插值
    enable_category_value_interpolation: bool = True
    # chart type: GRID_AND_BAR
    grid_bar_x_position: float = 0.84
    grid_last_column_width: float = 1
    grid_second_column_x_position: float = 2
    progress_callback: Callable[[int, int], None] = None
    bar_alpha: float = 0.85
    show_value_change_indicator: bool = True
    change_indicator_x_offset: int = 10
    default_change_indicator: str = u'\u2501'
    default_change_indicator_color: str = "#fdb827"
    arrow_indicator_font_size: str = 30
    # 显示第一名图片
    show_champion_images: bool = False
    champion_images_dir: str = None
    champion_image_position: list = None
    champion_image_zoom: float = 1.0
    random_color_seed: int = 0
    # 前N名种类分组配置文件，同一组的种类，它们的颜色和图片都相同！
    top_categories_group_file: str = None
    show_fill_na_value: bool = False
    show_category_bbox: bool = False
    category_bbox_pad: float = 0.5
    bbox_x_offset: float = 0
    bbox_line_width: float = 2
    intermediate_na_fill_method: str = None
    tick_label_color: str = "#000000"
    tick_label_font_size: int = 26
    tick_position: str = "top"
    date_time_format: str = "%Y/%m/%d"
    # 显示最大值和最小值，目前仅用于line chart
    show_max_and_min: bool = True
    max_min_area_y_offset: float = 0.25
    # max
    max_min_area_first_x1_position: float = 0.9
    max_min_area_first_y1_position: float = 0.8
    # min
    max_min_area_first_x2_position: float = 0.9
    max_min_area_first_y2_position: float = 0.75
    line_width: float = 2

    def __post_init__(self):
        self._adjust_time_duration_params()
        self._prepare_data_frame()

        # 数值上升下降图标显示
        if self.show_value_change_indicator:
            shifted_df_filled = self.df_filled.shift(-1)
            self.df_value_changed = shifted_df_filled - self.df_filled
            self.df_value_changed.iloc[-1] = [0] * len(self.df_value_changed.columns)
            self.df_value_changed[self.df_value_changed > 0] = 1
            self.df_value_changed[self.df_value_changed < 0] = -1
            self.change_indicator_symbols = [self.default_change_indicator, u'\u2191', u'\u2193']
            self.change_indicator_colors = [self.default_change_indicator_color, "#ef4f4f", "#00917c"]

        if self.is_preview_mode:
            if self.preview_frame_count > 0:
                self.video_save_path = f"{self.output_dir}/表格_预览.mp4"
            else:
                self.video_save_path = f"{self.output_dir}/预览.png"
        else:
            self.video_save_path = f"{self.output_dir}/表格.mp4"

        if self.chart_type is ChartType.H_BAR:
            if self.show_value_change_indicator:
                self.update_method = self.h_bar_chart_with_change_indicator_update
            else:
                self.update_method = self.h_bar_chart_update
        elif self.chart_type is ChartType.V_BAR:
            self.update_method = self.v_bar_chart_update
        elif self.chart_type is ChartType.GRID:
            self.update_method = self.grid_chart_update
            self.max_xlim = self.chart_top_n / self.rows_in_column
        elif self.chart_type is ChartType.GRID_AND_BAR:
            self.update_method = self.grid_and_bar_chart_update
            total_columns = math.ceil(self.chart_top_n / self.rows_in_column)
            self.max_xlim = total_columns + self.grid_last_column_width
            self.grid_column_x_position_list = [0]
            if total_columns > 2:
                x_offset = (total_columns - self.grid_second_column_x_position) / (total_columns - 2)
                for i in range(1, total_columns):
                    self.grid_column_x_position_list.append(self.grid_second_column_x_position + (i - 1) * x_offset)
            else:
                self.grid_column_x_position_list.append(self.grid_second_column_x_position)
        elif self.chart_type is ChartType.LINE_CHART:
            self.update_method = self.line_chart_update
            self.max_xlim = self.df_filled.index[-1]
            self.min_xlim = self.df_filled.index[0]
            if self.show_max_and_min:
                self.category_min_max_dict = dict()
                for category in self.df_filled.columns:
                    self.category_min_max_dict[category] = [10 ** 9, -10 ** 9]

        self._adjust_bar_color_params()
        self._adjust_offset_params()
        self._adjust_chart_pad_params()
        self._adjust_video_save_params()
        self._adjust_time_text_params()
        self._adjust_font_size_params()

        if self.show_champion_images:
            self.champion_images = {}
            for file in os.listdir(self.champion_images_dir):
                if not file.startswith("."):
                    self.champion_images[file.split('.')[0]] = plt.imread(f"{self.champion_images_dir}/{file}")
            # 获取每一行最小值的列名字
            self.df_champion_categories = self.df_rank_filled.idxmin(axis=1)

        if self.chart_type is ChartType.GRID_AND_BAR:
            self.normalized_numbers_of_first_column = self.get_normalized_number_values_of_first_column()

        if self.chart_category_color is None:
            self.chart_category_color = self.chart_number_color

            # {:,.2f} ==> {x:,.2f}
        if self.tick_label_format is None:
            self.tick_label_format = self.number_format

        self._validate_params()

    def _prepare_data_frame(self):
        self.csv_fill_steps = math.ceil(self.period_duration / self.frame_interval)
        self.rank_transition_steps = math.ceil(self.rank_transition_duration / self.frame_interval)

        if self.chart_type is ChartType.LINE_CHART:
            data_frame = pd.read_csv(self.csv_path, index_col=self.index_col, parse_dates=[self.index_col])
        else:
            data_frame = pd.read_csv(self.csv_path, index_col=self.index_col)
        if self.intermediate_na_fill_method:
            # Index column must be numeric or datetime type when using ffill/bfill method other than linear
            # loc method works with number index
            data_frame = data_frame.reset_index()
            if self.intermediate_na_fill_method == 'ffill':
                data_frame = data_frame.apply(lambda series: series.loc[:series.last_valid_index()].ffill())
            elif self.intermediate_na_fill_method == 'bfill':
                data_frame = data_frame.apply(lambda series: series.loc[series.first_valid_index():].bfill())
            else:
                data_frame = data_frame.interpolate(method=self.intermediate_na_fill_method, limit_area='inside')
            data_frame.set_index(self.index_col, inplace=True)
        data_frame.fillna(value=self.fill_na_value, inplace=True)

        if self.chart_top_n is None:
            self.chart_top_n = data_frame.shape[1]

        if self.summary_category:
            expended_category_df = self.fill_csv(data_frame[self.summary_category], with_rank=False)
            self.summary_category_values = expended_category_df[self.summary_category].values
            data_frame.drop([self.summary_category], axis=1, inplace=True)

            if self.summary_category_display_name is None:
                self.summary_category_display_name = self.summary_category

        self.df_filled, self.df_rank_filled = self.fill_csv(data_frame)
        self.fig, self.ax = plt.subplots(figsize=self.video_aspect_ratio, dpi=self.video_dpi)

        if not self.show_fill_na_value:
            # 如果在一开始就出现了na_value，可以通过将na_value排名设置为靠后数值，从而避免在一开始显示na_value
            na_value_position = self.df_filled == self.fill_na_value
            self.df_rank_filled[na_value_position] = self.chart_top_n

            # 如果在下降过程中出现na_value，可以通过ffill将na_value设置为前面的数值，这样的话bar在消失的过程中数值是不变的，避免显示na_value
            self.df_filled.replace(self.fill_na_value, value=None, inplace=True, method="ffill")

        # 为了提高性能，过滤出只在动画中出现的category
        if self.chart_top_n < self.df_filled.shape[1]:
            # 如果在动画中出现，说明排名在 0 ~ self.chart_top_n - 1 之间
            column_in_animation = (self.df_rank_filled < self.chart_top_n).any()
            if not column_in_animation.all():
                self.df_filled = self.df_filled.loc[:, column_in_animation]
                self.df_rank_filled = self.df_rank_filled.loc[:, column_in_animation]

        # 排名过渡动画数据准备
        self.make_smooth_rank_transition()

    def _adjust_video_save_params(self):
        if self.is_preview_mode:
            self.frame_count = self.preview_frame_count or len(self.df_filled)
        else:
            self.frame_count = len(self.df_filled)
        self.video_duration = math.ceil(self.frame_count * self.frame_interval * 1.0 / 1000)

    def _get_top_categories_group_config(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.optionxform = str
        config.read(self.top_categories_group_file)
        return config

    def _adjust_bar_color_params(self):
        if self.chart_type in [ChartType.GRID, ChartType.GRID_AND_BAR]:
            top_n = self.rows_in_column
        else:
            top_n = self.df_filled.shape[1]
        if self.bar_color_type is BarColorType.RANDOM_COLOR:
            # note: 必须添加copy方法
            total_colors = GENERIC_COLORS.copy()
            random.Random(self.random_color_seed).shuffle(total_colors)
            self.bar_colors = {}
            if self.top_categories_group_file:
                config = self._get_top_categories_group_config()
                for i, category_group in enumerate(config.sections()):
                    group_color = total_colors[i]
                    for category in config[category_group]:
                        self.bar_colors[category] = group_color
            else:
                if top_n > len(total_colors):
                    total_colors = total_colors * (top_n // len(total_colors) + 1)
                top_categories = self.get_total_top_categories(top_n)
                self.bar_colors = dict(zip(top_categories, total_colors))
        elif self.bar_color_type is BarColorType.COUNTRY_COLOR:
            self.bar_colors = COUNTRY_COLORS
        elif self.bar_color_type is BarColorType.SINGLE_COLOR:
            top_categories = self.get_total_top_categories(top_n)
            self.bar_colors = dict(zip(top_categories, [self.bar_color] * len(top_categories)))

    def _adjust_time_text_params(self):
        if self.chart_type is ChartType.GRID_AND_BAR:
            self.time_x_position = self.time_x_position or 0.16
            self.time_y_position = self.time_y_position or 0.92
            if self.chart_time_font_size is None:
                self.chart_time_font_size = 50

    def _adjust_time_duration_params(self):
        if self.statistics_time is StatisticsTime.START_OF_THE_YEAR or not self.enable_category_value_interpolation:
            # 说明最后一帧时间为0，并且第一帧有时间
            self.first_frame_duration -= self.period_duration
            if self.first_frame_duration < 0:
                self.first_frame_duration = 0
        elif self.statistics_time is StatisticsTime.END_OF_THE_YEAR:
            # 说明第一帧时间为0，并且最后一帧有时间
            self.last_frame_duration -= self.period_duration
            if self.last_frame_duration < 0:
                self.last_frame_duration = 0

        if self.rank_transition_duration is None:
            if self.chart_type is ChartType.GRID_AND_BAR:
                self.rank_transition_duration = 800

    def _adjust_category_images_params(self):
        if self.chart_category_icon_position is ChartCategoryIconPosition.HIDE:
            return
        self.category_images = {}
        top_categories = self.get_total_top_categories(self.chart_top_n)
        if self.category_icons_dir is None:
            if '中国' in top_categories:
                self.category_icons_dir = "../../countries"
            elif '北京' in top_categories:
                self.category_icons_dir = "../../province"
            else:
                print('category_icons_dir缺失并且无法智能判断')
                exit()
        if self.top_categories_group_file:
            config = self._get_top_categories_group_config()
            for category_group in config.sections():
                category_image = self._get_category_image(category_group)
                for category in config[category_group]:
                    self.category_images[category] = category_image
        else:
            for category in top_categories:
                self.category_images[category] = self._get_category_image(category)

    def _get_category_image(self, category_name):
        for image_format in ['png', 'gif', 'jpg', 'jpeg']:
            image_path = f"{self.category_icons_dir}/{category_name}.{image_format}"
            if os.path.exists(image_path):
                break
        return plt.imread(image_path)

    def _adjust_offset_params(self):
        if self.chart_type is ChartType.GRID_AND_BAR:
            if self.icon_x_offset is None:
                self.icon_x_offset = 0.25
            if self.category_x_offset is None:
                self.category_x_offset = 0.38
            if self.category_y_offset is None:
                self.category_y_offset = 0.18
            self.number_x_offset = self.category_x_offset
            self.number_y_offset = -0.24

    def _adjust_chart_pad_params(self):
        if self.chart_type is ChartType.GRID_AND_BAR:
            if self.chart_top_pad is None:
                self.chart_top_pad = 0.9
            if self.chart_bottom_pad is None:
                self.chart_bottom_pad = 0.05
            if self.chart_left_pad is None:
                self.chart_left_pad = 0.04
            if self.chart_right_pad is None:
                self.chart_right_pad = 0.96

    def _adjust_font_size_params(self):
        if self.chart_number_font_size is None:
            if self.chart_type is ChartType.GRID_AND_BAR:
                self.chart_number_font_size = 18

    def get_total_top_categories(self, top_n):
        total = []
        for row_index in range(len(self.df_rank_filled)):
            rank_list = self.df_rank_filled.iloc[row_index].values
            top_filter = (rank_list >= 0) & (rank_list < top_n)
            labels = self.df_filled.columns[top_filter].values.tolist()
            total += labels
        total = list(set(total))
        return total

    def get_normalized_number_values_of_first_column(self):
        total = []
        grid_bar_max_width = self.grid_second_column_x_position - 0.08 - self.grid_bar_x_position
        for row_index in range(len(self.df_rank_filled)):
            rank_list = self.df_rank_filled.iloc[row_index].values
            top_filter = (rank_list >= 0) & (rank_list < self.rows_in_column - 0.5)
            value_list = self.df_filled.iloc[row_index].values[top_filter]
            value_list = value_list / max(value_list) * grid_bar_max_width
            total.append(value_list)
        return total

    def _validate_params(self):
        assert self.rank_transition_duration <= self.period_duration, "排名过渡时间不能大于相邻时间段间隔时间"
        assert self.rank_transition_duration < self.last_frame_duration, "排名过渡时间需要小于最后一帧的间隔时间"

    # 线性填充数据，用于实现平滑过渡效果
    def fill_csv(self, df_arg, with_rank=True):
        _df = df_arg.reset_index()
        _df.index = _df.index * self.csv_fill_steps
        last_idx = _df.index[-1] + 1

        df_expanded = _df.reindex(range(last_idx))

        if self.statistics_time is StatisticsTime.START_OF_THE_YEAR or not self.enable_category_value_interpolation:
            df_expanded[self.index_col] = df_expanded[self.index_col].fillna(method='ffill')
        elif self.statistics_time is StatisticsTime.END_OF_THE_YEAR:
            df_expanded[self.index_col] = df_expanded[self.index_col].fillna(method='bfill')

        df_expanded = df_expanded.set_index(self.index_col)
        if self.enable_category_value_interpolation:
            df_expanded = df_expanded.interpolate()
        else:
            df_expanded = df_expanded.fillna(method='ffill')

        # 填充第一帧和最后一帧的定格时间
        replicated_count = round(self.last_frame_duration / self.frame_interval)
        if replicated_count > 0:
            df_expanded = df_expanded.append(df_expanded.iloc[[-1] * replicated_count])

        replicated_count = round(self.first_frame_duration / self.frame_interval)
        if replicated_count > 0:
            df_expanded = df_expanded.iloc[[0] * replicated_count].append(df_expanded)

        if with_rank:
            df_rank_expanded = df_expanded.rank(axis=1, method='first', ascending=False).clip(upper=self.chart_top_n + 1)
            # rank范围：[0, self.chart_top_n - 1]，并且数值越小，排名越靠前
            df_rank_expanded = df_rank_expanded - 1
            return df_expanded, df_rank_expanded
        return df_expanded

    # 排名动画自然过渡，首先筛选出排名动画过渡起始时刻的排名数值，然后对这两个数值进行线性变化，将过渡过程中的排名数值一一替换即可
    def make_smooth_rank_transition(self):
        # value_list: ndarray
        # 假设过渡动画帧数量为2，输入为 ndarray:
        # [1,    1,    1,       1,       2,       2,        2]
        # 输出为 ndarray：
        # [1,    1,    1,       1,       1.3333,  1.66667,  2]
        def smooth_rank(value_list):
            last_rank = value_list[0]
            i = 0
            while i < len(value_list):
                current_rank = value_list[i]
                if current_rank == last_rank:
                    i += 1
                    continue
                transition_rank_list = np.linspace(last_rank, current_rank, num=self.rank_transition_steps)
                # 将过渡期间的排名数值替换掉
                transition_start_index = i - 1
                value_list.put(
                    range(transition_start_index, transition_start_index + self.rank_transition_steps),
                    transition_rank_list
                )
                last_rank = current_rank
                i = transition_start_index + self.rank_transition_steps
            return value_list

        for column in self.df_rank_filled:
            self.df_rank_filled[column] = smooth_rank(self.df_rank_filled[column].values)
        if not self.enable_category_value_interpolation:
            for column in self.df_filled:
                self.df_filled[column] = smooth_rank(self.df_filled[column].values)

    def set_figure_background(self):
        if not self._is_background_image_exist():
            if self.chart_type in [ChartType.GRID, ChartType.GRID_AND_BAR]:
                self.generate_rank_background()
            else:
                return
        background = plt.imread(self.background_image_path)
        self.fig.figimage(background, alpha=self.background_image_alpha).set_zorder(0)
        self.ax.set_zorder(1)

    def _is_background_image_exist(self):
        return self.background_image_path and os.path.exists(self.background_image_path)

    def _init_ax(self):
        self.ax.clear()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_ylim(0.5, self.rows_in_column + 0.5)
        self.ax.set_xlim(0, self.max_xlim)

    def line_chart_update(self, row_index):
        self.ax.clear()
        df = self.df_filled.head(row_index + 1)
        time_list = df.index.values

        for i, (category, category_values) in enumerate(df.iteritems()):
            color = self.bar_colors[category]
            self.ax.plot(time_list, category_values, color=color, linewidth=self.line_width)
            x_value = date2num(time_list[-1])
            y_value = category_values[-1]
            if self.show_category_bbox:
                bbox_props = dict(fill=False, boxstyle=f"square,pad={self.category_bbox_pad}",
                                           ec=color,
                                           alpha=self.bar_alpha, lw=self.bbox_line_width)
                x_offset = self.bbox_x_offset
            else:
                bbox_props = None
                x_offset = self.category_x_offset
            self.ax.annotate(f"{category} {self.number_format.format(x=y_value)}", (x_value, y_value),
                             xytext=(x_offset, 0), weight='800',
                             bbox=bbox_props,
                             xycoords='data', textcoords='offset points',
                             fontsize=self.chart_category_font_size,
                             va="center", color=self.chart_category_color, ha="left",
                             fontname=self.category_font_name)

            if self.show_max_and_min:
                # 显示最小和最大值
                min_value, max_value = self.category_min_max_dict[category]
                if y_value < min_value:
                    min_value = y_value
                if y_value > max_value:
                    max_value = y_value
                self.category_min_max_dict[category] = [min_value, max_value]
                # 表格列靠前的在最上面
                y_offset = i * self.max_min_area_y_offset
                self.ax.text(
                    self.max_min_area_first_x1_position, self.max_min_area_first_y1_position - y_offset, self.number_format.format(x=max_value), transform=self.fig.transFigure, size=30,
                    ha='left'
                )
                # self.ax.text(
                #     0.8, 0.75 - y_offset, self.number_format.format(x=y_value), transform=self.fig.transFigure, size=30,
                #     ha='left'
                # )
                self.ax.text(
                    self.max_min_area_first_x2_position, self.max_min_area_first_y2_position - y_offset, self.number_format.format(x=min_value), transform=self.fig.transFigure, size=30,
                    ha='left'
                )

        # 时间
        data_time = pd.to_datetime(str(time_list[-1])).strftime(self.date_time_format)
        self.ax.text(self.time_x_position, self.time_y_position, data_time, transform=self.fig.transFigure,
                     size=self.chart_time_font_size, ha='right', color=self.chart_time_color, weight='1000',
                     family='monospace', fontname=self.time_font_name).set_zorder(0)

        self.ax.yaxis.set_major_formatter(self.tick_label_format)
        self.ax.tick_params(axis='both', colors=self.tick_label_color, labelsize=self.tick_label_font_size, length=0)
        self.ax.set_xlim(self.min_xlim, self.max_xlim)
        # only works on linux/macos
        self.ax.xaxis.set_ticks_position(self.tick_position)
        self.ax.xaxis.set_major_formatter(DateFormatter("%Y%年%-m月"))
        self.ax.xaxis.set_major_locator(MonthLocator(interval=6))

        if self.is_show_grid:
            self.ax.grid(which='major', axis=self.grid_axis, linestyle=self.grid_line_style, linewidth=1, color=self.chart_grid_line_color, clip_on=True)

        self._optimise_ax()

    def _draw_category_bbox(self, category_label, number_value, x, y):
        self.ax.annotate(f"{category_label} {number_value}", (x, y),
                         xytext=(self.bbox_x_offset, 0), weight='800', zorder=0,
                         bbox=dict(fill=False, boxstyle=f"square,pad={self.category_bbox_pad}",
                                   ec=self.bar_colors[category_label],
                                   alpha=self.bar_alpha, lw=self.bbox_line_width),
                         xycoords='data', textcoords='offset points',
                         fontsize=self.chart_category_font_size,
                         va="center", color=self.chart_category_color, ha="left",
                         fontname=self.category_font_name)

    def _draw_category_label(self, category_label, x, y):
        category_label_x_position = 0 if self.category_label_position is CategoryLabelPosition.LEFT else x
        self.ax.annotate(category_label, (category_label_x_position, y),
                         xytext=(self.category_x_offset, 0), weight='800',
                         xycoords='data', textcoords='offset points', fontsize=self.chart_category_font_size,
                         va="center", color=self.chart_category_color, ha="right", fontname=self.category_font_name)

    def _draw_category_number(self, number_value, x, y):
        self.ax.annotate(number_value, (x, y),
                         xytext=(self.number_x_offset, 0),
                         xycoords='data', textcoords='offset points', fontsize=self.chart_number_font_size,
                         weight=self.number_font_weight,
                         va="center", color=self.chart_number_color, fontname=self.number_font_name)

    def _draw_category_icon(self, category_icon, x, y):
        icon_x_position = 0 if self.chart_category_icon_position is ChartCategoryIconPosition.LEFT else x
        img = OffsetImage(category_icon, zoom=self.chart_category_icon_zoom)
        img.image.axes = self.ax
        ab = AnnotationBbox(img, (icon_x_position, y), xybox=(self.icon_x_offset, 0), frameon=False,
                            xycoords='data', boxcoords='offset points', pad=0)
        self.ax.add_artist(ab)

    def _draw_time_label(self, time_label):
        data_time = pd.to_datetime(time_label).strftime(self.date_time_format)
        self.ax.text(self.time_x_position, self.time_y_position, data_time, transform=self.fig.transFigure,
                     size=self.chart_time_font_size, ha='right', color=self.chart_time_color, weight='1000',
                     family='monospace', fontname=self.time_font_name)

    def _optimise_ax(self):
        self.ax.set_axisbelow(True)
        [spine.set_visible(False) for spine in self.ax.spines.values()]
        plt.subplots_adjust(top=self.chart_top_pad, bottom=self.chart_bottom_pad, left=self.chart_left_pad,
                            right=self.chart_right_pad)

    def h_bar_chart_update(self, row_index):
        self.ax.clear()
        self.ax.set_ylim(0.1, self.chart_top_n + 0.5)

        # 获取一行数据并排序
        y = self.df_rank_filled.iloc[row_index].values
        top_filter = (y >= 0) & (y < self.chart_top_n)
        y = self.chart_top_n - y[top_filter]
        width = self.df_filled.iloc[row_index].values[top_filter]
        labels = self.df_filled.columns[top_filter]

        if self.bar_color_type is BarColorType.SINGLE_COLOR:
            bar_color = self.bar_color
        else:
            bar_color = [self.bar_colors[x] for x in labels]
        self.ax.barh(y=y, width=width, height=self.bar_height, color=bar_color, tick_label=labels, alpha=self.bar_alpha)
        self.ax.set_yticks([])

        if self.show_champion_images:
            self._display_champion_image(row_index)

        for i_, (x_value, y_value) in enumerate(zip(width, y)):
            category_name = labels[i_]
            # todo 有bug
            if float(y_value) < 0:
                number_value = self.na_value_display_text
            else:
                number_value = self.number_format.format(x=x_value)

            # 种类文字和数字
            if self.show_category_bbox:
                self._draw_category_bbox(category_name, number_value, x_value, y_value)
            else:
                self._draw_category_label(category_name, x_value, y_value)
                self._draw_category_number(number_value, x_value, y_value)
            # 种类icon
            if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
                self._draw_category_icon(self.category_images[category_name], x_value, y_value)

        # 时间
        self._draw_time_label(str(self.df_filled.index[row_index]))

        if self.is_show_grid:
            self.ax.xaxis.set_major_formatter(self.tick_label_format)
            self.ax.grid(which='major', axis=self.grid_axis, linestyle=self.grid_line_style, linewidth=1, color=self.chart_grid_line_color,
                         clip_on=True)
            self.ax.tick_params(axis='x', colors=self.tick_label_color, labelsize=self.tick_label_font_size,
                                length=0)
            self.ax.xaxis.set_ticks_position(self.tick_position)
            # 隐藏x轴开始的0
            self.ax.xaxis.get_major_ticks()[0].set_visible(False)
        else:
            self.ax.set_xticks([])

        self._optimise_ax()

    def _display_champion_image(self, row_index):
        img = OffsetImage(
            self.champion_images[self.df_champion_categories.iloc[row_index]],
            zoom=self.champion_image_zoom
        )
        ab = AnnotationBbox(img, (
            self.champion_image_position[0], self.champion_image_position[1]), frameon=False,
                            xycoords='figure fraction', pad=0)
        self.ax.add_artist(ab)

    def h_bar_chart_with_change_indicator_update(self, row_index):
        self.ax.clear()
        self.ax.set_ylim(0.1, self.chart_top_n + 0.5)

        # 获取一行数据并排序
        y = self.df_rank_filled.iloc[row_index].values
        top_filter = (y >= 0) & (y < self.chart_top_n)
        y = self.chart_top_n - y[top_filter]
        width = self.df_filled.iloc[row_index].values[top_filter]
        labels = self.df_filled.columns[top_filter]
        change_indicators = self.df_value_changed.iloc[row_index].values[top_filter]

        if self.bar_color_type is BarColorType.SINGLE_COLOR:
            bar_color = self.bar_color
        else:
            bar_color = [self.bar_colors[x] for x in labels]
        self.ax.barh(y=y, width=width, height=self.bar_height, color=bar_color, tick_label=labels, alpha=self.bar_alpha)
        self.ax.set_yticks([])

        if self.show_champion_images:
            self._display_champion_image(row_index)

        for i_, (x_value, y_value) in enumerate(zip(width, y)):
            category_name = labels[i_]
            # todo 有bug
            if float(y_value) < 0:
                number_value = self.na_value_display_text
            else:
                number_value = self.number_format.format(x=x_value)

            # 种类文字和数字
            if self.show_category_bbox:
                self._draw_category_bbox(category_name, number_value, x_value, y_value)
            else:
                self._draw_category_label(category_name, x_value, y_value)
                self._draw_category_number(number_value, x_value, y_value)
            # 种类icon
            if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
                self._draw_category_icon(self.category_images[category_name], x_value, y_value)

            # 上升、下降箭头指示
            change_value = int(change_indicators[i_])
            if change_value != 0:
                self.ax.annotate(self.change_indicator_symbols[change_value], (x_value, y_value),
                                 xytext=(self.change_indicator_x_offset, 0),
                                 xycoords='data', textcoords='offset points', fontsize=self.arrow_indicator_font_size,
                                 weight="1000", fontname="Hiragino Sans",
                                 family='monospace',
                                 va="center", color=self.change_indicator_colors[change_value])

        # 时间
        self._draw_time_label(str(self.df_filled.index[row_index]))

        if self.is_show_grid:
            self.ax.xaxis.set_major_formatter(self.tick_label_format)
            self.ax.grid(which='major', axis=self.grid_axis, linestyle=self.grid_line_style, linewidth=1, color=self.chart_grid_line_color,
                         clip_on=True)
            self.ax.tick_params(axis='x', colors=self.tick_label_color, labelsize=self.tick_label_font_size,
                                length=0)
            self.ax.xaxis.set_ticks_position(self.tick_position)
            # 隐藏x轴开始的0
            self.ax.xaxis.get_major_ticks()[0].set_visible(False)
        else:
            self.ax.set_xticks([])

        self._optimise_ax()

    def v_bar_chart_update(self, row_index):
        self.ax.clear()
        self.ax.set_xlim(0.1, self.chart_top_n + 0.5)

        # 获取一行数据并排序
        y = self.df_rank_filled.iloc[row_index].values
        top_filter = (y >= 0) & (y < self.chart_top_n)
        y = self.chart_top_n - y[top_filter]

        width = self.df_filled.iloc[row_index].values[top_filter]
        labels = self.df_filled.columns[top_filter]

        if self.bar_color and self.bar_color_type is BarColorType.SINGLE_COLOR:
            bar_color = self.bar_color
        else:
            bar_color = [self.bar_colors[x] for x in labels]
        # self.ax.bar(y, width, width=self.chart_bar_width, color=bar_color, tick_label=labels)
        self.ax.bar(y, width, color=bar_color, tick_label=labels)

        if self.chart_category_icon_position is ChartCategoryIconPosition.BEFORE_BAR:
            self.ax.set_xticks([])
        else:
            self.ax.tick_params(axis='x', colors=self.tick_label_color, labelsize=self.tick_label_font_size,
                                length=0)
        dx = width.max() / 200

        for i_, (x_value, y_value) in enumerate(zip(y, width)):
            # todo enum添加is_show方法
            if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
                category_name = labels[i_]
                img = OffsetImage(self.category_images[category_name], zoom=self.chart_category_icon_zoom)
                img.image.axes = self.ax

                # icon在最前面
                if self.chart_category_icon_position is ChartCategoryIconPosition.BEFORE_BAR:
                    # 图片
                    ab = AnnotationBbox(img, (self.icon_x_offset, y_value), xybox=(0, 0), frameon=False,
                                        xycoords='data', boxcoords='offset points', pad=0)
                    self.ax.add_artist(ab)

                    # 数字
                    self.ax.text(x_value + dx * 2, y_value, self.number_format.format(x=x_value), ha='left',
                                 size=self.chart_number_font_size, weight=self.number_font_weight,
                                 va='center', color=self.chart_number_color, fontname=self.number_font_name)
                    # 类别
                    self.ax.text(x_value - dx, y_value, category_name, ha='right', size=self.chart_category_font_size,
                                 va='center', color=self.chart_category_color, weight='800', fontname=self.category_font_name)
                elif self.chart_category_icon_position is ChartCategoryIconPosition.BEHIND_BAR:
                    # 图片
                    ab = AnnotationBbox(img, (x_value, y_value), xybox=(0, 0),
                                        frameon=False,
                                        xycoords='data', boxcoords='offset points', pad=0)
                    self.ax.add_artist(ab)

                    # 数字
                    self.ax.annotate(self.number_format.format(x=x_value), (x_value + self.icon_x_offset, y_value),
                                     xytext=(0, 0),
                                     xycoords='data', textcoords='offset points', fontsize=self.chart_number_font_size,
                                     weight=self.number_font_weight,
                                     va="center", color=self.chart_number_color, fontname=self.number_font_name)
            else:
                # 数字
                if float(y_value) < 0:
                    self.ax.text(
                        x_value + 0.3, y_value, self.na_value_display_text, ha='right',
                        size=self.chart_number_font_size, weight=self.number_font_weight, rotation=self.number_rotation,
                        va='bottom', color=self.chart_number_color, fontname=self.number_font_name
                    )
                else:
                    self.ax.text(
                        x_value + 0.3, y_value, self.number_format.format(x=y_value), ha='right',
                        size=self.chart_number_font_size, weight=self.number_font_weight, rotation=self.number_rotation,
                        va='bottom', color=self.chart_number_color, fontname=self.number_font_name
                    )

        # 时间
        data_time = self.df_filled.index[row_index]
        self.ax.text(self.time_x_position, self.time_y_position, data_time, transform=self.fig.transFigure,
                     size=self.chart_time_font_size, ha='right', color=self.chart_time_color, weight='1000',
                     family='monospace', fontname=self.time_font_name)

        if self.is_show_grid:
            self.ax.yaxis.set_major_formatter(self.tick_label_format)
            self.ax.grid(which='major', axis=self.grid_axis, linestyle=self.grid_line_style, linewidth=1, color=self.chart_grid_line_color,
                         clip_on=True)
            self.ax.tick_params(axis='y', colors=self.tick_label_color, labelsize=self.tick_label_font_size,
                                length=0)
            self.ax.yaxis.set_ticks_position(self.tick_position)
            # 隐藏y轴开始的0
            self.ax.yaxis.get_major_ticks()[0].set_visible(False)
        else:
            self.ax.set_yticks([])

        self._optimise_ax()

    def grid_chart_update(self, row_index):
        self._init_ax()

        # 获取一行数据并排序
        rank_list = self.df_rank_filled.iloc[row_index].values
        top_filter = (rank_list >= 0) & (rank_list < self.chart_top_n)
        rank_list = rank_list[top_filter]

        value_list = self.df_filled.iloc[row_index].values[top_filter]
        labels = self.df_filled.columns[top_filter]

        for i_, (y_value, num_value) in enumerate(zip(rank_list, value_list)):
            x_value = (y_value+0.5) // self.rows_in_column
            y_value = self.rows_in_column * (x_value + 1) - y_value
            # 类别
            category_name = labels[i_]

            self.ax.annotate(category_name, (x_value, y_value),
                             xytext=(self.category_x_offset, 0),
                             xycoords='data', textcoords='offset points', fontsize=self.chart_category_font_size,
                             va="center", color=self.chart_category_color, ha="right")

            # todo enum添加is_show方法
            if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
                img = OffsetImage(self.category_images[category_name], zoom=self.chart_category_icon_zoom)
                img.image.axes = self.ax

                # 图片
                ab = AnnotationBbox(img, (x_value + self.icon_x_offset, y_value), xybox=(0, 0), frameon=False,
                                    xycoords='data', boxcoords='offset points', pad=0)
                self.ax.add_artist(ab)

            # 数字
            if category_name in ['内蒙古', '黑龙江']:
                number_x_offset = self.number_x_offset + 0.1
            else:
                number_x_offset = self.number_x_offset

            if float(num_value) < 0:
                # 数字
                self.ax.text(x_value + number_x_offset, y_value + self.number_y_offset, self.na_value_display_text, ha='left',
                             size=self.chart_number_font_size, weight=self.number_font_weight,
                             va='center', color=self.chart_number_color)
            else:
                self.ax.text(x_value + number_x_offset, y_value + self.number_y_offset, self.number_format.format(x=num_value), ha='left',
                             size=self.chart_number_font_size, weight=self.number_font_weight,
                             va='center', color=self.chart_number_color, fontname=self.number_font_name)

        # 时间
        self._draw_time_label(str(self.df_filled.index[row_index]))
        self._optimise_ax()

    def grid_and_bar_chart_update(self, row_index):
        self._init_ax()

        # 获取一行数据并排序
        rank_list = self.df_rank_filled.iloc[row_index].values
        top_filter = (rank_list >= 0) & (rank_list < self.chart_top_n)
        rank_list = rank_list[top_filter]

        value_list = self.df_filled.iloc[row_index].values[top_filter]
        labels = self.df_filled.columns[top_filter]
        normalized_numbers = self.normalized_numbers_of_first_column[row_index]
        first_column_bar_index = 0

        for i_, (y_value, num_value) in enumerate(zip(rank_list, value_list)):
            x_value = (y_value + 0.5) // self.rows_in_column
            y_value = self.rows_in_column * (x_value + 1) - y_value

            # 类别
            category_name = labels[i_]

            if x_value == 0:
                row_bar = Rectangle(
                    (self.grid_bar_x_position, y_value - self.bar_height / 2), normalized_numbers[first_column_bar_index],
                    self.bar_height, linewidth=1, color=self.bar_colors[category_name], alpha=self.bar_alpha
                )
                first_column_bar_index += 1
                self.ax.add_patch(row_bar)
            else:
                x_value = self.grid_column_x_position_list[int(x_value)]

            self.ax.annotate(category_name, (x_value, y_value),
                             xytext=(self.category_x_offset, 0),
                             xycoords='data', textcoords='offset points', fontsize=self.chart_category_font_size,
                             va="center", color=self.chart_category_color, ha="right")

            if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
                img = OffsetImage(self.category_images[category_name], zoom=self.chart_category_icon_zoom)
                img.image.axes = self.ax

                # 图片
                ab = AnnotationBbox(img, (x_value + self.icon_x_offset, y_value), xybox=(0, 0), frameon=False,
                                    xycoords='data', boxcoords='offset points', pad=0)
                self.ax.add_artist(ab)

            # 数字
            # if category_name in ['内蒙古', '黑龙江']:
            #     number_x_offset = self.number_x_offset + 0.1
            # else:
            #     number_x_offset = self.number_x_offset

            if float(num_value) < 0:
                # 数字
                self.ax.text(x_value + self.number_x_offset, y_value + self.number_y_offset, self.na_value_display_text,
                             ha='left',
                             size=self.chart_number_font_size, weight=self.number_font_weight,
                             va='center', color=self.chart_number_color)
            else:
                self.ax.text(x_value + self.number_x_offset, y_value + self.number_y_offset,
                             self.number_format.format(x=num_value), ha='left',
                             size=self.chart_number_font_size, weight=self.number_font_weight,
                             va='center', color=self.chart_number_color, fontname=self.number_font_name)

        # 时间
        data_time = self.df_filled.index[row_index]
        self.ax.text(self.time_x_position, self.time_y_position, data_time, transform=self.fig.transFigure,
                     size=self.chart_time_font_size, ha='right', color=self.chart_time_color, weight='1000',
                     family='monospace', fontname=self.time_font_name)

        self._optimise_ax()

    def generate_rank_background(self):
        if self.chart_type not in [ChartType.GRID, ChartType.GRID_AND_BAR]:
            print('chart type is not supported')
            return
        self._init_ax()

        for i in range(0, self.chart_top_n):
            x_value = i // self.rows_in_column
            if self.chart_type is ChartType.GRID_AND_BAR:
                x_value = self.grid_column_x_position_list[x_value]
            y_value = self.rows_in_column - i % self.rows_in_column
            self.ax.text(x_value, y_value, (i+1), ha='left', size=self.rank_number_font_size,
                         va='center', color=self.rank_number_color, weight='1000')

        self._optimise_ax()

        self.background_image_path = f"{self.output_dir}/排名背景.png"
        plt.savefig(self.background_image_path, dpi=self.video_dpi, transparent=True)

    def generate(self):
        self._adjust_category_images_params()

        print(f"视频帧数：{self.frame_count}, 视频总时长：{self.video_duration}秒")
        if self.is_preview_mode and self.preview_frame_count <= 0:
            self.set_figure_background()
            row_index = list(range(0, len(self.df_filled)))[self.preview_frame_index]
            self.update_method(row_index)
            plt.savefig(self.video_save_path, dpi=self.video_dpi, transparent=True)
            return

        if self.progress_callback is None:
            self.progress_callback = self.show_progress

        start = time.time()
        self.set_figure_background()
        animator = animation.FuncAnimation(fig=self.fig, func=self.update_method, frames=self.frame_count,
                                           interval=self.frame_interval)
        animator.save(self.video_save_path, dpi=self.video_dpi, progress_callback=self.progress_callback,
                      savefig_kwargs={'transparent': True})
        end = time.time()
        print(f'\n用时：{round(end - start)}秒')
        print(f"视频帧数：{self.frame_count}, 视频总时长：{self.video_duration}秒")

    @staticmethod
    def show_progress(i, n):
        print(f'正在合成视频：{round(i / n * 100, 2)}%', end="\r", flush=True)
        time.sleep(0.01)
