import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as animation
from chart_constants import COUNTRY_COLORS, GENERIC_COLORS, ChartCategoryIconPosition, BarColorType, StatisticsTime
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import time
import os
import math
from dataclasses import dataclass
import numpy as np


# macOS系统上的中文处理
plt.rcParams['axes.unicode_minus'] = False
# 需要修改~/.matplotlib/fontlist-v330.json
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['STHeiti Medium']
# plt.rcParams['figure.constrained_layout.use'] = True


@dataclass
class BarChartVideoGenerator:
    csv_path: str
    video_save_path: str
    is_preview_mode: bool
    statistics_time: StatisticsTime
    chart_category_icon_position: ChartCategoryIconPosition
    index_col: str = "Time"
    # https://pyformat.info/
    number_format: str = "{:}"
    x_label_format: str = None
    bar_color_type: BarColorType = BarColorType.RANDOM_COLOR
    # bar的颜色只有一种，优先级高于COUNTRY_COLOR和RANDOM_COLOR
    bar_color: str = None
    background_image_path: str = None
    background_image_alpha: float = None
    preview_frame_count: int = None
    preview_frame_index: int = None
    chart_bar_height: float = 0.75
    frame_interval: int = 50
    # 相邻两个数据之间出现的时间间隔
    period_duration: int = 2500
    # 相邻的排名动画过渡时间
    rank_transition_duration: int = 500
    video_dpi: int = 120
    video_aspect_ratio: tuple = (16,9)
    chart_top_n: int = 15
    is_show_grid: bool = True
    chart_category_icon_zoom: float = 1
    # 某个种类单独在时间文字区域显示
    summary_category: str = None
    summary_category_display_name: str = None
    summary_category_color: str = "#f6c90e"
    chart_category_icon_x_offset: int = -30
    category_icons_dir: str = None
    chart_number_font_size: int = 24
    chart_y_label_font_size: int = 24
    chart_category_font_size: int = 22
    chart_time_font_size: int = 100
    chart_left_pad: float = 0.22
    chart_right_pad: float = 0.88
    chart_top_pad: float = 0.95
    chart_bottom_pad: float = 0.1
    chart_background_color: str = '#202040'
    chart_number_color: str = '#ffffff'
    chart_category_color: str = None
    chart_time_color: str = '#ffbd69'
    chart_grid_line_color: str = '#47555e'
    chart_x_label_color: str = None
    chart_x_label_font_size: int = 18
    time_x_position: float = 1
    time_y_position: float = 0.2
    # 最后一帧定格时间，单位：毫秒
    last_frame_duration: int = 5000
    # 开始一帧定格时间
    first_frame_duration: int = 1500
    number_font_family: str = "serif"
    number_font_weight: str = "1000"

    def __post_init__(self):
        self._validate_params()

        if self.chart_category_color is None:
            self.chart_category_color = self.chart_number_color

        if self.chart_x_label_color is None:
            self.chart_x_label_color = self.chart_number_color

        # {:,.2f} ==> {x:,.2f}
        if self.x_label_format is None:
            self.x_label_format = "{x" + self.number_format[1:-1] + "}"

        self.csv_fill_steps = math.ceil(self.period_duration / self.frame_interval)
        self.rank_transition_steps = math.ceil(self.rank_transition_duration / self.frame_interval)

        data_frame = pd.read_csv(self.csv_path, index_col=self.index_col)
        data_frame.fillna(value=0, inplace=True)

        if self.summary_category:
            expended_category_df = self.fill_csv(data_frame[self.summary_category], with_rank=False)
            self.summary_category_values = expended_category_df[self.summary_category].values
            data_frame.drop([self.summary_category], axis=1, inplace=True)

            if self.summary_category_display_name is None:
                self.summary_category_display_name = self.summary_category

        if self.statistics_time is StatisticsTime.END_OF_THE_YEAR:
            # 说明第一帧时间为0，并且最后一帧有时间
            self.last_frame_duration -= self.period_duration
            if self.last_frame_duration < 0:
                self.last_frame_duration = 0
        elif self.statistics_time is StatisticsTime.START_OF_THE_YEAR:
            # 说明最后一帧时间为0，并且第一帧有时间
            self.first_frame_duration -= self.period_duration
            if self.first_frame_duration < 0:
                self.first_frame_duration = 0

        self.df_filled, self.df_rank_filled = self.fill_csv(data_frame)
        self.fig, self.ax = plt.subplots(figsize=self.video_aspect_ratio, dpi=self.video_dpi)

        # 为了提高性能，过滤出只在动画中出现的category
        if self.chart_top_n < self.df_filled.shape[1]:
            # 如果不在动画中出现，说明等于0
            column_in_animation = (self.df_rank_filled > 0).any()
            if not column_in_animation.all():
                self.df_filled = self.df_filled.loc[:, column_in_animation]
                self.df_rank_filled = self.df_rank_filled.loc[:, column_in_animation]

        # 排名过渡动画数据准备
        self.make_smooth_rank_transition()

        if self.is_preview_mode:
            file_path, file_extension = self.video_save_path.split('.')
            self.video_save_path = f"{file_path}_预览.{file_extension}"
            self.frame_count = self.preview_frame_count or len(self.df_filled)
        else:
            self.frame_count = len(self.df_filled)

        self.video_duration = math.ceil(self.frame_count * self.frame_interval * 1.0 / 1000)

        if self.bar_color_type is BarColorType.RANDOM_COLOR:
            total_colors = GENERIC_COLORS
            if self.df_filled.shape[1] > len(total_colors):
                total_colors = total_colors * (self.df_filled.shape[1] // self.chart_top_n + 1)
            self.bar_colors = dict(zip(self.df_filled.columns.values, total_colors))
        elif self.bar_color_type is BarColorType.COUNTRY_COLOR:
            self.bar_colors = COUNTRY_COLORS

        if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
            self.category_images = {}
            for category in self.df_filled.columns.values:
                self.category_images[category] = plt.imread(f"{self.category_icons_dir}/{category}.png")

    def _validate_params(self):
        assert self.rank_transition_duration < self.period_duration, "排名过渡时间需要小于相邻时间段间隔时间"
        assert self.rank_transition_duration < self.last_frame_duration, "排名过渡时间需要小于最后一帧的间隔时间"

    # 线性填充数据，用于实现平滑过渡效果
    def fill_csv(self, df_arg, with_rank=True):
        _df = df_arg.reset_index()
        _df.index = _df.index * self.csv_fill_steps
        last_idx = _df.index[-1] + 1

        df_expanded = _df.reindex(range(last_idx))

        if self.statistics_time is StatisticsTime.START_OF_THE_YEAR:
            df_expanded[self.index_col] = df_expanded[self.index_col].fillna(method='ffill')
        elif self.statistics_time is StatisticsTime.END_OF_THE_YEAR:
            df_expanded[self.index_col] = df_expanded[self.index_col].fillna(method='bfill')

        df_expanded = df_expanded.set_index(self.index_col)
        df_expanded = df_expanded.interpolate()

        # 填充第一帧和最后一帧的定格时间
        replicated_count = round(self.last_frame_duration / self.frame_interval)
        if replicated_count > 0:
            df_expanded = df_expanded.append(df_expanded.iloc[[-1] * replicated_count])

        replicated_count = round(self.first_frame_duration / self.frame_interval)
        if replicated_count > 0:
            df_expanded = df_expanded.iloc[[0] * replicated_count].append(df_expanded)

        if with_rank:
            df_rank_expanded = df_expanded.rank(axis=1, method='first', ascending=False).clip(upper=self.chart_top_n + 1)
            df_rank_expanded = self.chart_top_n + 1 - df_rank_expanded
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

    def set_figure_background(self):
        background = plt.imread(self.background_image_path)
        self.fig.figimage(background, alpha=self.background_image_alpha).set_zorder(0)
        self.ax.set_zorder(1)

    def update(self, row_index):
        self.ax.clear()
        self.ax.set_ylim(0.1, self.chart_top_n + 0.5)

        # 获取一行数据并排序
        y = self.df_rank_filled.iloc[row_index].values
        top_filter = (y > 0) & (y < self.chart_top_n + 1)
        y = y[top_filter]
        width = self.df_filled.iloc[row_index].values[top_filter]
        labels = self.df_filled.columns[top_filter]

        if self.bar_color:
            bar_color = self.bar_color
        else:
            bar_color = [self.bar_colors[x] for x in labels]
        self.ax.barh(y=y, width=width, height=self.chart_bar_height, color=bar_color, tick_label=labels)

        if self.chart_category_icon_position is ChartCategoryIconPosition.BEFORE_BAR:
            self.ax.set_yticks([])
        else:
            self.ax.tick_params(axis='y', colors=self.chart_category_color, labelsize=self.chart_y_label_font_size, length=0)
        dx = width.max() / 200

        for i_, (x_value, y_value) in enumerate(zip(width, y)):
            # todo enum添加is_show方法
            if self.chart_category_icon_position is not ChartCategoryIconPosition.HIDE:
                category_name = labels[i_]
                img = OffsetImage(self.category_images[category_name], zoom=self.chart_category_icon_zoom)
                img.image.axes = self.ax

                # icon在最前面
                if self.chart_category_icon_position is ChartCategoryIconPosition.BEFORE_BAR:
                    # 图片
                    ab = AnnotationBbox(img, (0, y_value), xybox=(self.chart_category_icon_x_offset, 0), frameon=False,
                                        xycoords='data', boxcoords='offset points', pad=0)
                    self.ax.add_artist(ab)

                    # 数字
                    self.ax.text(x_value + dx * 2, y_value, self.number_format.format(x_value), ha='left',
                                 size=self.chart_number_font_size, weight=self.number_font_weight,
                                 va='center', color= self.chart_number_color, family=self.number_font_family)
                    # 类别
                    self.ax.text(x_value - dx, y_value, category_name, ha='right', size=self.chart_category_font_size,
                                 va='center', color= self.chart_category_color, weight='heavy')
                elif self.chart_category_icon_position is ChartCategoryIconPosition.BEHIND_BAR:
                    # 图片
                    ab = AnnotationBbox(img, (x_value , y_value), xybox=(-self.chart_category_icon_x_offset, 0), frameon=False,
                                        xycoords='data', boxcoords='offset points', pad=0)
                    self.ax.add_artist(ab)

                    # 数字
                    self.ax.annotate(self.number_format.format(x_value), (x_value, y_value),
                                     xytext=(-self.chart_category_icon_x_offset * 2.1, 0),
                                     xycoords='data', textcoords='offset points', fontsize=self.chart_number_font_size,
                                     weight=self.number_font_weight,
                                     va="center", color= self.chart_number_color, family=self.number_font_family)
            else:
                # 数字
                self.ax.text(x_value + dx * 2, y_value, self.number_format.format(x_value), ha='left',
                             size=self.chart_number_font_size, weight=self.number_font_weight,
                             va='center', color= self.chart_number_color, family=self.number_font_family)

        # 时间
        data_time = int(self.df_filled.index[row_index])
        self.ax.text(self.time_x_position, self.time_y_position, data_time, transform=self.fig.transFigure,
                     size=self.chart_time_font_size, ha='right', color=self.chart_time_color, weight='1000',
                     family='fantasy')
        # 单独显示的种类
        if self.summary_category:
            self.ax.text(
                self.time_x_position, self.time_y_position * 2.5,
                f"{self.summary_category_display_name} {self.number_format.format(self.summary_category_values[row_index])}",
                transform=self.fig.transFigure,
                size=self.chart_time_font_size * 0.4,
                ha='right', color=self.summary_category_color, weight='800',
            )

        if self.is_show_grid:
            self.ax.xaxis.set_major_formatter(ticker.StrMethodFormatter(self.x_label_format))
            self.ax.grid(which='major', axis='x', linestyle='--', linewidth=1, color=self.chart_grid_line_color, clip_on=True)
            self.ax.tick_params(axis='x', colors=self.chart_x_label_color, labelsize=self.chart_x_label_font_size, length=0)
            self.ax.xaxis.set_ticks_position('top')
            # 隐藏x轴开始的0
            self.ax.xaxis.get_major_ticks()[0].set_visible(False)
        else:
            self.ax.set_xticks([])

        self.ax.set_axisbelow(True)
        [spine.set_visible(False) for spine in self.ax.spines.values()]
        plt.subplots_adjust(top=self.chart_top_pad, bottom=self.chart_bottom_pad, left=self.chart_left_pad,
                            right=self.chart_right_pad)

    def generate(self):
        print(f"视频帧数：{self.frame_count}, 视频总时长：{self.video_duration}秒")
        if self.is_preview_mode and self.preview_frame_index is not None:
            if self.background_image_path:
                self.set_figure_background()
            row_index = list(range(0, len(self.df_filled)))[self.preview_frame_index]
            self.update(row_index)
            file_path, _ = self.video_save_path.split('.')
            plt.savefig(f"{file_path}_{row_index}.png", dpi=self.video_dpi, transparent=True)
            return

        if self.is_preview_mode or (not os.path.exists(self.video_save_path)) or input("表格视频已经存在，是否覆盖？(y/n)") == "y":
            start = time.time()
            if self.background_image_path:
                self.set_figure_background()
            animator = animation.FuncAnimation(fig=self.fig, func=self.update, frames=self.frame_count,
                                               interval=self.frame_interval)
            animator.save(self.video_save_path, dpi=self.video_dpi, progress_callback=self.show_progress,
                          savefig_kwargs={'transparent': True, 'facecolor': self.chart_background_color })
            end = time.time()
            print(f'\n用时：{round(end - start)}秒')
        print(f"视频帧数：{self.frame_count}, 视频总时长：{self.video_duration}秒")

    @staticmethod
    def show_progress(i, n):
        print(f'正在合成视频：{round(i / n * 100, 2)}%', end="\r", flush=True)
        time.sleep(0.1)
