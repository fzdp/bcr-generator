import wx
from csv_generator import CSVGenerator
from csv_util import remove_china_sar_data, merge_fao_data, merge_china_sar_data, merge_ethiopia_pdr_data, rename_china_province_name
from chart_constants import CSVSource, ChartType, StatisticsTime, ChartCategoryIconPosition, CategoryLabelPosition, BarColorType, ProvinceNameType
from data_video_generator import DataVideoGenerator
import os
import json
from multiprocessing import Process, Manager
from threading import Thread
from datetime import datetime


class TopCategoriesDialog(wx.Dialog):
    def __init__(self, params):
        super().__init__(None, title='显示所有的TOP N', size=(200, 400))
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.btn_run = wx.Button(self, label='运行')
        self.tc_top_n = wx.TextCtrl(self, value="10")
        self.tc_result = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        main_sizer.Add(self.tc_top_n)
        main_sizer.Add(self.btn_run)
        main_sizer.Add(self.tc_result, flag=wx.EXPAND, proportion=1)
        self.SetSizer(main_sizer)
        self.generator = None
        self.params = params

        self.btn_run.Bind(wx.EVT_BUTTON, self._show_top_n)

    def _show_top_n(self, _):
        top_n = int(self.tc_top_n.GetValue().strip())
        if self.generator is None:
            self.generator = DataVideoGenerator(**self.params)
        total_categories = "\n".join(self.generator.get_total_top_categories(top_n))
        self.tc_result.SetValue(total_categories)
        self.Layout()


class VideoGeneratorProcess(Process):
    def __init__(self, generator, index, container):
        super().__init__()
        self.generator = generator
        self.generator.progress_callback = self.update_progress
        self.index = index
        self.container = container

    def run(self) -> None:
        self.generator.generate()

    def update_progress(self, i, n):
        # print(f'子进程{self.index}: {i}/{n}')
        self.container[self.index] = (i, n)


class CsvProcessFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="数据可视化GUI", size=(400, 400))
        sizer = self._get_csv_sizer()
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.btn_process_csv.Bind(wx.EVT_BUTTON, self._process_csv)
        self.btn_open_csv_dir.Bind(wx.EVT_BUTTON, self._open_csv_dir)

    def _get_csv_sizer(self):
        sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "CSV预处理")
        grid_sizer = wx.FlexGridSizer(cols=2, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)

        grid_sizer.Add(wx.StaticText(self, label='原始文件'))
        self.fpc_raw_csv_file = wx.FilePickerCtrl(self, wildcard="csv|*.csv")
        grid_sizer.Add(self.fpc_raw_csv_file, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(self, label='BGS数据目录'))
        self.dpc_bgs_data_dir = wx.DirPickerCtrl(self)
        grid_sizer.Add(self.dpc_bgs_data_dir)

        grid_sizer.Add(wx.StaticText(self, label='数据来源'))
        self.cho_csv_source = wx.Choice(self, choices=list(CSVSource.__members__.keys()))
        grid_sizer.Add(self.cho_csv_source, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(self, label='原始文件的索引列'))
        self.tc_index_column_name = wx.TextCtrl(self, value="Year")
        grid_sizer.Add(self.tc_index_column_name, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(self, label='时间段'))
        self.tc_year_range = wx.TextCtrl(self, value="")
        self.tc_year_range.SetHint('1961,2019')
        grid_sizer.Add(self.tc_year_range, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(self, label='输出文件'))
        self.fpc_output_csv = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL | wx.FLP_SAVE, wildcard="csv文件|*.csv")
        grid_sizer.Add(self.fpc_output_csv, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(self, label='需要后期处理'))
        self.chk_need_post_process = wx.CheckBox(self)
        grid_sizer.Add(self.chk_need_post_process)

        grid_sizer.Add(wx.StaticText(self, label='省份缩写'))
        self.cho_province_name_type = wx.Choice(self, choices=list(ProvinceNameType.__members__.keys()))
        grid_sizer.Add(self.cho_province_name_type)

        grid_sizer.Add(wx.StaticText(self, label='移除港澳台数据'))
        self.chk_remove_china_sar_data = wx.CheckBox(self)
        grid_sizer.Add(self.chk_remove_china_sar_data)

        grid_sizer.Add(wx.StaticText(self, label='合并港澳台数据'))
        self.chk_merge_china_sar_data = wx.CheckBox(self)
        grid_sizer.Add(self.chk_merge_china_sar_data)

        grid_sizer.Add(wx.StaticText(self, label='合并埃塞俄比亚PDR数据'))
        self.chk_merge_ethiopia_pdr_data = wx.CheckBox(self)
        grid_sizer.Add(self.chk_merge_ethiopia_pdr_data)

        grid_sizer.Add(wx.StaticText(self, label='合并FAO最新数据'))
        self.fpc_fao_file_path = wx.FilePickerCtrl(self, wildcard="csv文件|*.csv")
        grid_sizer.Add(self.fpc_fao_file_path, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(self, label='数值缩放比例'))
        self.tc_csv_value_scale_ratio = wx.TextCtrl(self)
        grid_sizer.Add(self.tc_csv_value_scale_ratio)

        sizer.Add(grid_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        self.btn_process_csv = wx.Button(self, label='运行')
        self.btn_open_csv_dir = wx.Button(self, label="查看输出文件")
        sizer.Add(self.btn_process_csv, flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        sizer.Add(self.btn_open_csv_dir, flag=wx.ALIGN_CENTER | wx.TOP, border=15)

        return sizer

    def _process_csv(self, _):
        try:
            self.btn_process_csv.Enable(False)

            params = dict()
            params['csv_source'] = CSVSource[self.cho_csv_source.GetStringSelection()]
            if params['csv_source'] is CSVSource.BGS_MINERALS:
                params['original_csv_path'] = self.dpc_bgs_data_dir.GetPath()
                year_list = None
            else:
                params['original_csv_path'] = self.fpc_raw_csv_file.GetPath()
                str_year_range = self.tc_year_range.GetValue().strip()
                if str_year_range:
                    year_start, year_end = str_year_range.split(',')
                    year_list = list(range(int(year_start), int(year_end) + 1))
                else:
                    year_list = None
            params['real_csv_path'] = self.fpc_output_csv.GetPath()

            csv_generator = CSVGenerator(**params)
            csv_generator.generate(year_list=year_list, index_column=self.tc_index_column_name.GetValue().strip())

            if self.chk_need_post_process.IsChecked():
                csv_generator.process("post", self._csv_post_process, is_saving=True)
        finally:
            self.btn_process_csv.Enable(True)

    def _open_csv_dir(self, _=None):
        csv_file = self.fpc_output_csv.GetPath()
        if not csv_file:
            return
        os.popen(f"open -R {csv_file}").read()

    def _csv_post_process(self, df):
        if self.chk_remove_china_sar_data.IsChecked():
            df = remove_china_sar_data(df)

        if self.chk_merge_china_sar_data.IsChecked():
            df = merge_china_sar_data(df)

        if self.chk_merge_ethiopia_pdr_data.IsChecked():
            df = merge_ethiopia_pdr_data(df)

        name_type = ProvinceNameType[self.cho_province_name_type.GetStringSelection()]
        if name_type is not ProvinceNameType.NORMAL:
            df = rename_china_province_name(df, name_type)

        fao_file = self.fpc_fao_file_path.GetPath()
        if fao_file:
            df = merge_fao_data(df, fao_file)

        scale_ratio = self.tc_csv_value_scale_ratio.GetValue().strip()
        if scale_ratio:
            scale_ratio = float(scale_ratio)
            df = df * scale_ratio

        return df


class VideoProgressListFrame(wx.Frame):
    def __init__(self, progress_container, info_container):
        super().__init__(None, title='视频合成列表', size=(400, 600))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)

        for i in range(len(progress_container)):
            name = info_container[i]['name']
            start_time = info_container[i]['start_time']
            current_frame, total_frame = progress_container[i]

            sizer.Add(wx.StaticText(self, label=f"{name} 开始时间：{start_time}，进度：{current_frame}/{total_frame}"), flag=wx.LEFT, border=20)
            guage = wx.Gauge(self, range=total_frame, size=(-1, 30))
            guage.SetValue(current_frame)
            sizer.Add(guage, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)

            sizer.AddSpacer(30)

        self.SetSizer(sizer)


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="数据可视化GUI", size=(1000, 700))
        main_sizer = self._get_video_sizer()
        self.SetSizer(main_sizer)
        main_sizer.SetSizeHints(self)

        self.config_dir = "gui_configs"
        self.progress_container = Manager().dict()
        self.progress_info_container = dict()
        self.config_file_info = dict()

        self.btn_process_video.Bind(wx.EVT_BUTTON, self._process_video)
        self.btn_open_output_dir.Bind(wx.EVT_BUTTON, self._open_output_dir)
        self.btn_refresh_config_list.Bind(wx.EVT_BUTTON, self._refresh_config_list)
        self.btn_save_config.Bind(wx.EVT_BUTTON, self._save_config)
        self.btn_save_as_config.Bind(wx.EVT_BUTTON, self._save_as_config)
        self.cho_config_list.Bind(wx.EVT_CHOICE, self._config_item_selected)
        self.btn_show_progress.Bind(wx.EVT_BUTTON, self._show_generation_progress_list)
        self.btn_open_config_dir.Bind(wx.EVT_BUTTON, self._open_config_dir)
        self.btn_load_project_config.Bind(wx.EVT_BUTTON, self._load_project_config)
        self.btn_show_top_n.Bind(wx.EVT_BUTTON, self._show_top_n)
        self.btn_open_csv_frame.Bind(wx.EVT_BUTTON, self._open_csv_frame)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_collapsible_pane_changed)

    def _on_collapsible_pane_changed(self, _):
        self.Layout()

    def _show_progress(self, i, n):
        progress = f"{round(i / n * 100, 2)}%"
        print(f"进度：{progress}")

    def _open_config_dir(self, _):
        os.popen(f"open {self.config_dir}").read()

    def _load_video_generator_params(self, params):
        params = self._add_compatible_params(params)

        self.dpc_output_dir.SetPath(params.get('output_dir', ''))
        self.cho_chart_type.SetStringSelection(params['chart_type'].split('.')[-1])
        self.fpc_csv_path.SetPath(params['csv_path'])
        self.cho_statistics_time.SetStringSelection(params['statistics_time'].split('.')[-1])
        self.cho_chart_category_icon_position.SetStringSelection(params['chart_category_icon_position'].split('.')[-1])
        self.cho_category_label_position.SetStringSelection(params.get('category_label_position', 'CategoryLabelPosition.RIGHT').split('.')[-1])
        self.spin_rows_in_column.SetValue(params.get('rows_in_column', 10))
        self.spin_change_indicator_x_offset.SetValue(params.get('change_indicator_x_offset', 0))
        self.chk_is_preview_mode.SetValue(params.get('is_preview_mode', True))
        self.chk_is_show_grid.SetValue(params.get('is_show_grid', False))
        self.tc_tick_label_format.SetValue(params.get('tick_label_format', "{x:.0f}"))
        self.chk_show_value_change_indicator.SetValue(params.get('show_value_change_indicator', False))
        self.txt_number_format.SetValue(params.get('number_format', ""))
        self.cho_bar_color_type.SetStringSelection(params['bar_color_type'].split('.')[-1])
        self.cpc_bar_color.SetColour(wx.Colour(params['bar_color']))
        self.fpc_background_image_path.SetPath(params['background_image_path'])
        self.tc_line_width.SetValue(str(params.get('line_width', 2)))
        self.fpc_top_categories_group_file.SetPath(params.get('top_categories_group_file', ''))
        self.spin_preview_frame_count.SetValue(params['preview_frame_count'])
        self.spin_preview_frame_index.SetValue(params['preview_frame_index'])
        self.spin_random_color_seed.SetValue(params.get('random_color_seed', 0))
        self.spin_frame_interval.SetValue(params['frame_interval'])
        self.spin_period_duration.SetValue(params['period_duration'])
        self.spin_transition_duration.SetValue(params['rank_transition_duration'])
        self.spin_top_n.SetValue(params['chart_top_n'])
        self.spin_fill_na_value.SetValue(params.get('fill_na_value', -1))
        self.cho_intermediate_na_fill_method.SetStringSelection(params.get('intermediate_na_fill_method', ''))
        self.tc_icon_zoom.SetValue(str(params['chart_category_icon_zoom']))
        self.dpc_category_icons_dir.SetPath(params['category_icons_dir'])
        self.tc_bar_height.SetValue(str(params['bar_height']))
        self.spin_time_font_size.SetValue(params.get('chart_time_font_size', 16))
        self.spin_category_font_size.SetValue(params.get('chart_category_font_size', 22))
        self.spin_rank_number_font_size.SetValue(params['rank_number_font_size'])
        self.tc_time_font.SetValue(params.get('time_font_name', 'Hiragino Sans'))
        self.tc_category_font.SetValue(params.get('category_font_name', 'DIY_category'))
        self.chk_show_max_and_min.SetValue(params.get('show_max_and_min', False))
        self.tc_max_min_area_y_offset.SetValue(str(params.get('max_min_area_y_offset', 0.2)))
        self.tc_max_min_area_first_x1_position.SetValue(str(params.get('max_min_area_first_x1_position', 0.9)))
        self.tc_max_min_area_first_y1_position.SetValue(str(params.get('max_min_area_first_y1_position', 0.8)))
        self.tc_max_min_area_first_x2_position.SetValue(str(params.get('max_min_area_first_x2_position', 0.9)))
        self.tc_max_min_area_first_y2_position.SetValue(str(params.get('max_min_area_first_y2_position', 0.75)))
        self.spin_number_font_size.SetValue(params.get('chart_number_font_size', 16))
        self.spin_arrow_indicator_font_size.SetValue(params.get('arrow_indicator_font_size', 30))
        self.tc_left_pad.SetValue(str(params['chart_left_pad']))
        self.tc_right_pad.SetValue(str(params['chart_right_pad']))
        self.tc_top_pad.SetValue(str(params['chart_top_pad']))
        self.tc_bottom_pad.SetValue(str(params['chart_bottom_pad']))
        self.cpc_number_color.SetColour(wx.Colour(params['chart_number_color']))
        self.cpc_rank_number_color.SetColour(wx.Colour(params['rank_number_color']))
        self.cpc_category_color.SetColour(wx.Colour(params['chart_category_color']))
        self.cpc_time_color.SetColour(wx.Colour(params['chart_time_color']))
        self.cpc_grid_line_color.SetColour(wx.Colour(params['chart_grid_line_color']))
        self.cpc_tick_label_color.SetColour(wx.Colour(params['tick_label_color']))
        self.spin_tick_label_font_size.SetValue(params.get('tick_label_font_size', 26))
        self.cho_tick_position.SetStringSelection(params.get('tick_position', 'top'))
        self.cho_grid_axis.SetStringSelection(params.get('grid_axis', 'both'))
        self.cho_grid_line_style.SetStringSelection(params.get('grid_line_style', 'solid'))
        self.tc_time_position.SetValue(f"{params['time_x_position']},{params['time_y_position']}")
        self.tc_last_column_width.SetValue(str(params['grid_last_column_width']))
        self.tc_bar_alpha.SetValue(str(params.get('bar_alpha', 0.85)))
        self.tc_grid_bar_x_position.SetValue(str(params['grid_bar_x_position']))
        self.tc_grid_second_column_x_position.SetValue(str(params['grid_second_column_x_position']))
        self.tc_icon_x_offset.SetValue(str(params['icon_x_offset']))
        self.tc_category_x_offset.SetValue(str(params['category_x_offset']))
        self.tc_number_x_offset.SetValue(str(params.get('number_x_offset', 0)))
        self.spin_first_frame_duration.SetValue(params['first_frame_duration'])
        self.spin_last_frame_duration.SetValue(params['last_frame_duration'])
        self.chk_enable_category_value_interpolation.SetValue(params['enable_category_value_interpolation'])
        self.chk_show_champion_images.SetValue(params.get('show_champion_images', False))
        self.dpc_champion_images_dir.SetPath(params.get('champion_images_dir', ''))
        self.tc_champion_image_position.SetValue(",".join(map(str,params.get('champion_image_position', [0, 0]))))
        self.tc_champion_image_zoom.SetValue(str(params.get('champion_image_zoom', 1)))
        self.chk_show_category_bbox.SetValue(params.get('show_category_bbox', False))
        self.tc_category_bbox_pad.SetValue(str(params.get('category_bbox_pad', 0.5)))
        self.tc_bbox_line_width.SetValue(str(params.get('bbox_line_width', 2)))
        self.tc_bbox_x_offset.SetValue(str(params.get('bbox_x_offset', 0)))

    def _get_output_dir(self):
        return self.dpc_output_dir.GetPath()

    def _config_item_selected(self, _):
        config_file = self._get_current_config_file()
        if not config_file:
            return
        with open(config_file) as file:
            params = json.load(file)
        self._load_video_generator_params(params)

    def _show_generation_progress_list(self, _):
        VideoProgressListFrame(self.progress_container, self.progress_info_container).Show()

    def _open_csv_frame(self, _):
        CsvProcessFrame().Show()

    def _get_current_config_file(self):
        current_config = self.cho_config_list.GetStringSelection()
        return self.config_file_info.get(current_config, None)

    def _refresh_config_list(self, _):
        self.config_file_info = dict()
        for file in os.listdir(self.config_dir):
            if file.endswith('.json'):
                self.config_file_info[file[:-5]] = f"{self.config_dir}/{file}"
        self.cho_config_list.Set(list(self.config_file_info.keys()))
        wx.PostEvent(self.cho_config_list, wx.CommandEvent(wx.EVT_CHOICE.typeId))

    def _get_video_generator_params_as_json(self):
        params = self._get_video_generator_params()
        params.pop('progress_callback', None)
        params_json = json.dumps(params, indent=4, sort_keys=True, default=str, ensure_ascii=False)
        return params_json

    def _save_config(self, _):
        config_file = self._get_current_config_file()
        if not config_file:
            return
        with open(config_file, 'w') as file:
            file.write(self._get_video_generator_params_as_json())

    def _save_as_config(self, _):
        with wx.FileDialog(
                self, "保存配置", wildcard="json文件 (*.json)|*.json",
                defaultDir=self.config_dir, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fdg:
            if fdg.ShowModal() == wx.ID_CANCEL:
                return
            save_path = fdg.GetPath()
            try:
                with open(save_path, 'w') as file:
                    file.write(self._get_video_generator_params_as_json())
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % save_path)

    def _load_project_config(self, _):
        with wx.DirDialog(self, "打开项目", defaultPath="~/Movies/data_videos") as fdg:
            if fdg.ShowModal() == wx.ID_CANCEL:
                return
            config_path = f"{fdg.GetPath()}/config.json"
            with open(config_path, 'r') as file:
                params = json.load(file)
            self._load_video_generator_params(params)
            self._add_project_config(config_path)

    @staticmethod
    def _add_compatible_params(params):
        if 'chart_grid_label_color' in params:
            params['tick_label_color'] = params['chart_grid_label_color']
        return params

    def _add_project_config(self, project_config_file):
        project_dir_basename = project_config_file.split('/')[-2]
        config_name = f"项目_{project_dir_basename}"
        self.config_file_info[config_name] = project_config_file
        self.cho_config_list.Insert(config_name, 0)
        self.cho_config_list.SetStringSelection(config_name)

    def _get_video_generator_params(self):
        params = dict()
        params['output_dir'] = self._get_output_dir()
        params['chart_type'] = ChartType[self.cho_chart_type.GetStringSelection()]
        params['csv_path'] = self.fpc_csv_path.GetPath()
        params['statistics_time'] = StatisticsTime[self.cho_statistics_time.GetStringSelection()]
        params['chart_category_icon_position'] = ChartCategoryIconPosition[self.cho_chart_category_icon_position.GetStringSelection()]
        params['category_label_position'] = CategoryLabelPosition[self.cho_category_label_position.GetStringSelection()]
        params['rows_in_column'] = self.spin_rows_in_column.GetValue()
        params['change_indicator_x_offset'] = self.spin_change_indicator_x_offset.GetValue()
        params['is_preview_mode'] = self.chk_is_preview_mode.IsChecked()
        params['is_show_grid'] = self.chk_is_show_grid.IsChecked()
        params['show_value_change_indicator'] = self.chk_show_value_change_indicator.IsChecked()
        params['number_format'] = self.txt_number_format.GetValue().strip()
        params['bar_color_type'] = BarColorType[self.cho_bar_color_type.GetStringSelection()]
        params['bar_color'] = self.cpc_bar_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['background_image_path'] = self.fpc_background_image_path.GetPath()
        params['line_width'] = float(self.tc_line_width.GetValue().strip())
        params['top_categories_group_file'] = self.fpc_top_categories_group_file.GetPath()
        params['preview_frame_count'] = self.spin_preview_frame_count.GetValue()
        params['preview_frame_index'] = self.spin_preview_frame_index.GetValue()
        params['random_color_seed'] = self.spin_random_color_seed.GetValue()
        params['frame_interval'] = self.spin_frame_interval.GetValue()
        params['period_duration'] = self.spin_period_duration.GetValue()
        params['rank_transition_duration'] = self.spin_transition_duration.GetValue()
        params['chart_top_n'] = self.spin_top_n.GetValue()
        params['fill_na_value'] = self.spin_fill_na_value.GetValue()
        params['intermediate_na_fill_method'] = self.cho_intermediate_na_fill_method.GetStringSelection()
        params['chart_category_icon_zoom'] = float(self.tc_icon_zoom.GetValue().strip())
        params['category_icons_dir'] = self.dpc_category_icons_dir.GetPath()
        params['chart_time_font_size'] = self.spin_time_font_size.GetValue()
        params['chart_category_font_size'] = self.spin_category_font_size.GetValue()
        params['rank_number_font_size'] = self.spin_rank_number_font_size.GetValue()
        params['time_font_name'] = self.tc_time_font.GetValue().strip()
        params['category_font_name'] = self.tc_category_font.GetValue().strip()
        params['show_max_and_min'] = self.chk_show_max_and_min.IsChecked()
        params['max_min_area_y_offset'] = float(self.tc_max_min_area_y_offset.GetValue().strip())
        params['max_min_area_first_x1_position'] = float(self.tc_max_min_area_first_x1_position.GetValue().strip())
        params['max_min_area_first_y1_position'] = float(self.tc_max_min_area_first_y1_position.GetValue().strip())
        params['max_min_area_first_x2_position'] = float(self.tc_max_min_area_first_x2_position.GetValue().strip())
        params['max_min_area_first_y2_position'] = float(self.tc_max_min_area_first_y2_position.GetValue().strip())
        params['chart_number_font_size'] = self.spin_number_font_size.GetValue()
        params['arrow_indicator_font_size'] = self.spin_arrow_indicator_font_size.GetValue()
        params['bar_height'] = float(self.tc_bar_height.GetValue().strip())
        params['chart_left_pad'] = float(self.tc_left_pad.GetValue().strip())
        params['chart_right_pad'] = float(self.tc_right_pad.GetValue().strip())
        params['chart_top_pad'] = float(self.tc_top_pad.GetValue().strip())
        params['chart_bottom_pad'] = float(self.tc_bottom_pad.GetValue().strip())
        params['chart_number_color'] = self.cpc_number_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['rank_number_color'] = self.cpc_rank_number_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['chart_category_color'] = self.cpc_category_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['chart_time_color'] = self.cpc_time_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['chart_grid_line_color'] = self.cpc_grid_line_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['tick_label_color'] = self.cpc_tick_label_color.GetColour().GetAsString(flags=wx.C2S_HTML_SYNTAX)
        params['tick_label_font_size'] = self.spin_tick_label_font_size.GetValue()
        params['tick_position'] = self.cho_tick_position.GetStringSelection()
        params['tick_label_format'] = self.tc_tick_label_format.GetValue().strip()
        params['grid_axis'] = self.cho_grid_axis.GetStringSelection()
        params['grid_line_style'] = self.cho_grid_line_style.GetStringSelection()
        time_x, time_y = list(map(float, self.tc_time_position.GetValue().strip().split(',')))
        params['time_x_position'] = time_x
        params['time_y_position'] = time_y
        params['grid_last_column_width'] = float(self.tc_last_column_width.GetValue().strip())
        params['bar_alpha'] = float(self.tc_bar_alpha.GetValue().strip())
        params['grid_bar_x_position'] = float(self.tc_grid_bar_x_position.GetValue().strip())
        params['grid_second_column_x_position'] = float(self.tc_grid_second_column_x_position.GetValue().strip())
        params['icon_x_offset'] = float(self.tc_icon_x_offset.GetValue().strip())
        params['category_x_offset'] = float(self.tc_category_x_offset.GetValue().strip())
        params['number_x_offset'] = float(self.tc_number_x_offset.GetValue().strip())
        params['first_frame_duration'] = self.spin_first_frame_duration.GetValue()
        params['last_frame_duration'] = self.spin_last_frame_duration.GetValue()
        params['enable_category_value_interpolation'] = self.chk_enable_category_value_interpolation.IsChecked()
        params['show_champion_images'] = self.chk_show_champion_images.IsChecked()
        params['champion_images_dir'] = self.dpc_champion_images_dir.GetPath()
        params['champion_image_zoom'] = float(self.tc_champion_image_zoom.GetValue().strip())
        params['champion_image_position'] = list(map(float, self.tc_champion_image_position.GetValue().strip().split(',')))
        params['show_category_bbox'] = self.chk_show_category_bbox.IsChecked()
        params['category_bbox_pad'] = float(self.tc_category_bbox_pad.GetValue().strip())
        params['bbox_line_width'] = float(self.tc_bbox_line_width.GetValue().strip())
        params['bbox_x_offset'] = float(self.tc_bbox_x_offset.GetValue().strip())
        params['progress_callback'] = self._show_progress
        return params

    def _open_output_dir(self, _=None):
        output_dir = self._get_output_dir()
        if not output_dir:
            return
        os.popen(f"open {output_dir}").read()

    def _start_video_generation(self, generator, index):
        VideoGeneratorProcess(generator, index, self.progress_container).start()

    def _show_top_n(self, _):
        params = self._get_video_generator_params()
        with TopCategoriesDialog(params) as dialog:
            dialog.ShowModal()

    def _process_video(self, _):
        try:
            self.btn_process_video.Enable(False)
            params = self._get_video_generator_params()
            with open(f"{self._get_output_dir()}/config.json", 'w') as file:
                file.write(self._get_video_generator_params_as_json())
            video_generator = DataVideoGenerator(**params)

            if video_generator.is_preview_mode:
                video_generator.generate()
                os.popen(f"open -R {video_generator.video_save_path}").read()
            else:
                current_index = len(self.progress_container)
                generator_thread = Thread(target=self._start_video_generation, args=(video_generator, current_index))
                generator_thread.start()
                self.progress_info_container[current_index] = {
                    'name': video_generator.output_dir.split('/')[-1],
                    'start_time': datetime.now().strftime('%H:%M:%S'),
                }
        finally:
            self.btn_process_video.Enable(True)

    def _get_video_sizer(self):
        video_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "视频参数配置")
        pane_list = []

        segment_pane = wx.CollapsiblePane(self, label='基础配置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='输出目录'))
        self.dpc_output_dir = wx.DirPickerCtrl(pane_window)
        grid_sizer.Add(self.dpc_output_dir, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(pane_window, label='csv文件'))
        self.fpc_csv_path = wx.FilePickerCtrl(pane_window, wildcard="csv文件|*.csv")
        grid_sizer.Add(self.fpc_csv_path, flag=wx.EXPAND)

        grid_sizer.Add(wx.StaticText(pane_window, label='表格样式'))
        self.cho_chart_type = wx.Choice(pane_window, choices=list(ChartType.__members__.keys()))
        grid_sizer.Add(self.cho_chart_type)

        grid_sizer.Add(wx.StaticText(pane_window, label='显示上升和下降箭头'))
        self.chk_show_value_change_indicator = wx.CheckBox(pane_window)
        grid_sizer.Add(self.chk_show_value_change_indicator)

        grid_sizer.Add(wx.StaticText(pane_window, label='数据记录时间'))
        self.cho_statistics_time = wx.Choice(pane_window, choices=list(StatisticsTime.__members__.keys()))
        grid_sizer.Add(self.cho_statistics_time)

        grid_sizer.Add(wx.StaticText(pane_window, label='前N名'))
        self.spin_top_n = wx.SpinCtrl(pane_window, value="30")
        grid_sizer.Add(self.spin_top_n)

        grid_sizer.Add(wx.StaticText(pane_window, label='数字格式'))
        self.txt_number_format = wx.TextCtrl(pane_window, value="{x:,.0f}")
        grid_sizer.Add(self.txt_number_format)

        grid_sizer.Add(wx.StaticText(pane_window, label='每一列的行数'))
        self.spin_rows_in_column = wx.SpinCtrl(pane_window, value="10")
        grid_sizer.Add(self.spin_rows_in_column)

        grid_sizer.Add(wx.StaticText(pane_window, label='允许插值模拟'))
        self.chk_enable_category_value_interpolation = wx.CheckBox(pane_window)
        self.chk_enable_category_value_interpolation.SetValue(True)
        grid_sizer.Add(self.chk_enable_category_value_interpolation)

        grid_sizer.Add(wx.StaticText(pane_window, label="条形图透明度"))
        self.tc_bar_alpha = wx.TextCtrl(pane_window, value="0.85")
        grid_sizer.Add(self.tc_bar_alpha)

        grid_sizer.Add(wx.StaticText(pane_window, label='背景图片'))
        self.fpc_background_image_path = wx.FilePickerCtrl(pane_window, wildcard="图片|*.jpg;*.jpeg;*.png")
        grid_sizer.Add(self.fpc_background_image_path)

        grid_sizer.Add(wx.StaticText(pane_window, label='线条宽度'))
        self.tc_line_width = wx.TextCtrl(pane_window, value="2")
        grid_sizer.Add(self.tc_line_width)

        grid_sizer.Add(wx.StaticText(pane_window, label="种类分组配置文件"))
        self.fpc_top_categories_group_file = wx.FilePickerCtrl(pane_window, wildcard="文本|*.txt;*.ini")
        grid_sizer.Add(self.fpc_top_categories_group_file)

        grid_sizer.Add(wx.StaticText(pane_window, label='种类图标位置'))
        self.cho_chart_category_icon_position = wx.Choice(
            pane_window, choices=list(ChartCategoryIconPosition.__members__.keys())
        )
        grid_sizer.Add(self.cho_chart_category_icon_position)

        grid_sizer.Add(wx.StaticText(pane_window, label='种类文字位置'))
        self.cho_category_label_position = wx.Choice(
            pane_window, choices=list(CategoryLabelPosition.__members__.keys())
        )
        grid_sizer.Add(self.cho_category_label_position)

        grid_sizer.Add(wx.StaticText(pane_window, label='种类图标目录'))
        self.dpc_category_icons_dir = wx.DirPickerCtrl(pane_window)
        grid_sizer.Add(self.dpc_category_icons_dir)

        grid_sizer.Add(wx.StaticText(pane_window, label='种类图标缩放比例'))
        self.tc_icon_zoom = wx.TextCtrl(pane_window, value="1")
        grid_sizer.Add(self.tc_icon_zoom)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label="空值填充配置")
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='首尾空值填充'))
        self.spin_fill_na_value = wx.SpinCtrl(pane_window, initial=0, min=-1000, max=1000)
        grid_sizer.Add(self.spin_fill_na_value)

        grid_sizer.Add(wx.StaticText(pane_window, label='中间空值填充'))
        self.cho_intermediate_na_fill_method = wx.Choice(pane_window, choices=['', 'linear', 'ffill', 'bfill'])
        grid_sizer.Add(self.cho_intermediate_na_fill_method)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label="颜色配置")
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='日期颜色'))
        self.cpc_time_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_time_color)

        grid_sizer.Add(wx.StaticText(pane_window, label='数字颜色'))
        self.cpc_number_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_number_color)

        grid_sizer.Add(wx.StaticText(pane_window, label='种类颜色'))
        self.cpc_category_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_category_color)

        grid_sizer.Add(wx.StaticText(pane_window, label='排名序号颜色'))
        self.cpc_rank_number_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_rank_number_color)

        grid_sizer.Add(wx.StaticText(pane_window, label='条形图颜色类型'))
        self.cho_bar_color_type = wx.Choice(pane_window, choices=list(BarColorType.__members__.keys()))
        grid_sizer.Add(self.cho_bar_color_type)

        grid_sizer.Add(wx.StaticText(pane_window, label='颜色随机种子'))
        self.spin_random_color_seed = wx.SpinCtrl(pane_window, value="0", max=1000)
        grid_sizer.Add(self.spin_random_color_seed)

        grid_sizer.Add(wx.StaticText(pane_window, label='条形图填充颜色'))
        self.cpc_bar_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_bar_color)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='坐标轴配置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label="显示网格"))
        self.chk_is_show_grid = wx.CheckBox(pane_window)
        grid_sizer.Add(self.chk_is_show_grid)

        grid_sizer.Add(wx.StaticText(pane_window, label='主轴数值格式'))
        self.tc_tick_label_format = wx.TextCtrl(pane_window, value="{x:.0f}")
        grid_sizer.Add(self.tc_tick_label_format)

        grid_sizer.Add(wx.StaticText(pane_window, label='网格颜色'))
        self.cpc_grid_line_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_grid_line_color)

        grid_sizer.Add(wx.StaticText(pane_window, label='刻度文字颜色'))
        self.cpc_tick_label_color = wx.ColourPickerCtrl(pane_window, style=wx.CLRP_USE_TEXTCTRL)
        grid_sizer.Add(self.cpc_tick_label_color)

        grid_sizer.Add(wx.StaticText(pane_window, label='刻度文字大小'))
        self.spin_tick_label_font_size = wx.SpinCtrl(pane_window, initial=26)
        grid_sizer.Add(self.spin_tick_label_font_size)

        grid_sizer.Add(wx.StaticText(pane_window, label='主轴位置'))
        self.cho_tick_position = wx.Choice(pane_window, choices=['top', 'bottom', 'left', 'right'])
        grid_sizer.Add(self.cho_tick_position)

        grid_sizer.Add(wx.StaticText(pane_window, label='网格所在坐标轴'))
        self.cho_grid_axis = wx.Choice(pane_window, choices=['both', 'x', 'y'])
        grid_sizer.Add(self.cho_grid_axis)

        grid_sizer.Add(wx.StaticText(pane_window, label='网格线风格'))
        self.cho_grid_line_style = wx.Choice(pane_window, choices=['solid', 'dashed', 'dashdot', 'dotted'])
        grid_sizer.Add(self.cho_grid_line_style)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='预览配置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='预览帧下标'))
        self.spin_preview_frame_index = wx.SpinCtrl(pane_window, value="-1", min=-1000, max=5000)
        grid_sizer.Add(self.spin_preview_frame_index)

        grid_sizer.Add(wx.StaticText(pane_window, label='预览帧数量'))
        self.spin_preview_frame_count = wx.SpinCtrl(pane_window, value="0", max=1000)
        grid_sizer.Add(self.spin_preview_frame_count)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='时间配置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='每一帧用时'))
        self.spin_frame_interval = wx.SpinCtrl(pane_window, initial=50, max=1000)
        grid_sizer.Add(self.spin_frame_interval)

        grid_sizer.Add(wx.StaticText(pane_window, label='每个时间段用时'))
        self.spin_period_duration = wx.SpinCtrl(pane_window, initial=2500, max=8000)
        grid_sizer.Add(self.spin_period_duration)

        grid_sizer.Add(wx.StaticText(pane_window, label='排名过渡时间'))
        self.spin_transition_duration = wx.SpinCtrl(pane_window, initial=800, max=3000)
        grid_sizer.Add(self.spin_transition_duration)

        grid_sizer.Add(wx.StaticText(pane_window, label='第一帧持续时间'))
        self.spin_first_frame_duration = wx.SpinCtrl(pane_window, initial=1000, max=10000)
        grid_sizer.Add(self.spin_first_frame_duration)

        grid_sizer.Add(wx.StaticText(pane_window, label='最后一帧持续时间'))
        self.spin_last_frame_duration = wx.SpinCtrl(pane_window, initial=5000, max=10000)
        grid_sizer.Add(self.spin_last_frame_duration)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='冠军图片设置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label="是否显示冠军图片"))
        self.chk_show_champion_images = wx.CheckBox(pane_window)
        grid_sizer.Add(self.chk_show_champion_images)

        grid_sizer.Add(wx.StaticText(pane_window, label="冠军图片目录"))
        self.dpc_champion_images_dir = wx.DirPickerCtrl(pane_window)
        grid_sizer.Add(self.dpc_champion_images_dir)

        grid_sizer.Add(wx.StaticText(pane_window, label="图片缩放比例"))
        self.tc_champion_image_zoom = wx.TextCtrl(pane_window, value="1.0")
        grid_sizer.Add(self.tc_champion_image_zoom)

        grid_sizer.Add(wx.StaticText(pane_window, label="图片位置"))
        self.tc_champion_image_position = wx.TextCtrl(pane_window, value="0,0")
        grid_sizer.Add(self.tc_champion_image_position)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='种类文字边框设置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='是否显示边框'))
        self.chk_show_category_bbox = wx.CheckBox(pane_window)
        grid_sizer.Add(self.chk_show_category_bbox)

        grid_sizer.Add(wx.StaticText(pane_window, label='边框填充'))
        self.tc_category_bbox_pad = wx.TextCtrl(pane_window, value="0.5")
        grid_sizer.Add(self.tc_category_bbox_pad)

        grid_sizer.Add(wx.StaticText(pane_window, label='线条宽度'))
        self.tc_bbox_line_width = wx.TextCtrl(pane_window, value="2")
        grid_sizer.Add(self.tc_bbox_line_width)

        grid_sizer.Add(wx.StaticText(pane_window, label='边框水平偏移'))
        self.tc_bbox_x_offset = wx.TextCtrl(pane_window, value="0")
        grid_sizer.Add(self.tc_bbox_x_offset)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='字体设置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label="时间文字大小"))
        self.spin_time_font_size = wx.SpinCtrl(pane_window, initial=50, max=200)
        grid_sizer.Add(self.spin_time_font_size)

        grid_sizer.Add(wx.StaticText(pane_window, label="排名序号大小"))
        self.spin_rank_number_font_size = wx.SpinCtrl(pane_window, initial=16, max=100)
        grid_sizer.Add(self.spin_rank_number_font_size)

        grid_sizer.Add(wx.StaticText(pane_window, label="数字文字大小"))
        self.spin_number_font_size = wx.SpinCtrl(pane_window, initial=16, max=100)
        grid_sizer.Add(self.spin_number_font_size)

        grid_sizer.Add(wx.StaticText(pane_window, label="上升下降箭头大小"))
        self.spin_arrow_indicator_font_size = wx.SpinCtrl(pane_window, initial=30, max=1000)
        grid_sizer.Add(self.spin_arrow_indicator_font_size)

        grid_sizer.Add(wx.StaticText(pane_window, label="种类文字大小"))
        self.spin_category_font_size = wx.SpinCtrl(pane_window, initial=26, min=0, max=100)
        grid_sizer.Add(self.spin_category_font_size)

        grid_sizer.Add(wx.StaticText(pane_window, label='时间字体'))
        self.tc_time_font = wx.TextCtrl(pane_window, value="Arial Bold")
        grid_sizer.Add(self.tc_time_font)

        grid_sizer.Add(wx.StaticText(pane_window, label='种类字体'))
        self.tc_category_font = wx.TextCtrl(pane_window, value="DIY_category")
        grid_sizer.Add(self.tc_category_font)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='最大值和最小值区域配置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='是否显示最值区域'))
        self.chk_show_max_and_min = wx.CheckBox(pane_window)
        grid_sizer.Add(self.chk_show_max_and_min)

        grid_sizer.Add(wx.StaticText(pane_window, label='相邻种类之间的垂直距离'))
        self.tc_max_min_area_y_offset = wx.TextCtrl(pane_window, value="0.2")
        grid_sizer.Add(self.tc_max_min_area_y_offset)

        grid_sizer.Add(wx.StaticText(pane_window, label='第一个种类的x1值'))
        self.tc_max_min_area_first_x1_position = wx.TextCtrl(pane_window, value="0.9")
        grid_sizer.Add(self.tc_max_min_area_first_x1_position)

        grid_sizer.Add(wx.StaticText(pane_window, label='第一个种类的x2值'))
        self.tc_max_min_area_first_x2_position = wx.TextCtrl(pane_window, value="0.9")
        grid_sizer.Add(self.tc_max_min_area_first_x2_position)

        grid_sizer.Add(wx.StaticText(pane_window, label='第一个种类的y1值'))
        self.tc_max_min_area_first_y1_position = wx.TextCtrl(pane_window, value="0.8")
        grid_sizer.Add(self.tc_max_min_area_first_y1_position)

        grid_sizer.Add(wx.StaticText(pane_window, label='第一个种类的y2值'))
        self.tc_max_min_area_first_y2_position = wx.TextCtrl(pane_window, value="0.75")
        grid_sizer.Add(self.tc_max_min_area_first_y2_position)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='距离配置')
        pane_window = segment_pane.GetPane()
        grid_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(3)

        grid_sizer.Add(wx.StaticText(pane_window, label='表格左间距'))
        self.tc_left_pad = wx.TextCtrl(pane_window, value="0.04")
        grid_sizer.Add(self.tc_left_pad)

        grid_sizer.Add(wx.StaticText(pane_window, label='表格右间距'))
        self.tc_right_pad = wx.TextCtrl(pane_window, value="0.96")
        grid_sizer.Add(self.tc_right_pad)

        grid_sizer.Add(wx.StaticText(pane_window, label='表格上间距'))
        self.tc_top_pad = wx.TextCtrl(pane_window, value="0.9")
        grid_sizer.Add(self.tc_top_pad)

        grid_sizer.Add(wx.StaticText(pane_window, label='表格下间距'))
        self.tc_bottom_pad = wx.TextCtrl(pane_window, value="0.05")
        grid_sizer.Add(self.tc_bottom_pad)

        grid_sizer.Add(wx.StaticText(pane_window, label='条形图高度'))
        self.tc_bar_height = wx.TextCtrl(pane_window, value="0.72")
        grid_sizer.Add(self.tc_bar_height)

        grid_sizer.Add(wx.StaticText(pane_window, label='时间文字的位置'))
        self.tc_time_position = wx.TextCtrl(pane_window, value="0.98,0.12")
        grid_sizer.Add(self.tc_time_position)

        grid_sizer.Add(wx.StaticText(pane_window, label="最后一列宽度"))
        self.tc_last_column_width = wx.TextCtrl(pane_window, value="1")
        grid_sizer.Add(self.tc_last_column_width)

        grid_sizer.Add(wx.StaticText(pane_window, label="第一列条形图的x轴坐标"))
        self.tc_grid_bar_x_position = wx.TextCtrl(pane_window, value="0.84")
        grid_sizer.Add(self.tc_grid_bar_x_position)

        grid_sizer.Add(wx.StaticText(pane_window, label="第二列的x坐标"))
        self.tc_grid_second_column_x_position = wx.TextCtrl(pane_window, value="2")
        grid_sizer.Add(self.tc_grid_second_column_x_position)

        grid_sizer.Add(wx.StaticText(pane_window, label="种类图标的水平间距"))
        self.tc_icon_x_offset = wx.TextCtrl(pane_window, value="0.25")
        grid_sizer.Add(self.tc_icon_x_offset)

        grid_sizer.Add(wx.StaticText(pane_window, label="种类文字的水平间距"))
        self.tc_category_x_offset = wx.TextCtrl(pane_window, value="0.38")
        grid_sizer.Add(self.tc_category_x_offset)

        grid_sizer.Add(wx.StaticText(pane_window, label="数字的水平间距"))
        self.tc_number_x_offset = wx.TextCtrl(pane_window, value="0.38")
        grid_sizer.Add(self.tc_number_x_offset)

        grid_sizer.Add(wx.StaticText(pane_window, label='上升下降箭头的水平间距'))
        self.spin_change_indicator_x_offset = wx.SpinCtrl(pane_window, min=-100, max=1000)
        grid_sizer.Add(self.spin_change_indicator_x_offset)

        pane_window.SetSizer(grid_sizer)
        grid_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        segment_pane = wx.CollapsiblePane(self, label='配置文件管理')
        pane_window = segment_pane.GetPane()
        box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cho_config_list = wx.Choice(pane_window, choices=[])
        self.cho_config_list.SetMinSize((200, -1))
        self.btn_refresh_config_list = wx.Button(pane_window, label='刷新')
        self.btn_save_config = wx.Button(pane_window, label='保存')
        self.btn_save_as_config = wx.Button(pane_window, label='另存为')
        self.btn_open_config_dir = wx.Button(pane_window, label='打开目录')

        box_sizer.AddStretchSpacer()
        box_sizer.Add(self.cho_config_list, flag=wx.ALL, border=5)
        box_sizer.Add(self.btn_refresh_config_list, flag=wx.ALL, border=5)
        box_sizer.Add(self.btn_save_config, flag=wx.ALL, border=5)
        box_sizer.Add(self.btn_save_as_config, flag=wx.ALL, border=5)
        box_sizer.Add(self.btn_open_config_dir, flag=wx.ALL, border=5)
        box_sizer.AddStretchSpacer()

        pane_window.SetSizer(box_sizer)
        box_sizer.SetSizeHints(pane_window)
        pane_list.append(segment_pane)

        for pane in pane_list:
            video_sizer.Add(pane, flag=wx.BOTTOM | wx.GROW, border=0, proportion=0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()

        self.btn_open_csv_frame = wx.Button(self, label="CSV预处理")
        btn_sizer.Add(self.btn_open_csv_frame, flag=wx.ALL, border=5)

        self.btn_load_project_config = wx.Button(self, label="加载项目")
        btn_sizer.Add(self.btn_load_project_config, flag=wx.ALL, border=5)

        self.btn_show_top_n = wx.Button(self, label="前N名")
        btn_sizer.Add(self.btn_show_top_n, flag=wx.ALL, border=5)

        self.chk_is_preview_mode = wx.CheckBox(self, label='预览模式')
        btn_sizer.Add(self.chk_is_preview_mode, flag=wx.ALL, border=5)

        self.btn_process_video = wx.Button(self, label="运行")
        btn_sizer.Add(self.btn_process_video, flag=wx.ALL, border=5)

        self.btn_show_progress = wx.Button(self, label="显示进度")
        btn_sizer.Add(self.btn_show_progress, flag=wx.ALL, border=5)

        self.btn_open_output_dir = wx.Button(self, label="打开输出目录")
        btn_sizer.Add(self.btn_open_output_dir, flag=wx.ALL, border=5)

        btn_sizer.AddStretchSpacer()
        video_sizer.Add(btn_sizer, flag=wx.EXPAND | wx.TOP, border=20)

        return video_sizer


class GUI(wx.App):
    def OnInit(self):
        MainFrame().Show()
        return True


if __name__ == "__main__":
    GUI().MainLoop()
