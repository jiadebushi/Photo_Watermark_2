"""
Photo Watermark 2 - 主应用程序
图片水印工具的GUI界面和核心逻辑
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
from pathlib import Path
from PIL import Image, ImageTk
from typing import Optional, List, Dict, Any
import threading

from image_processor import ImageProcessor
from watermark_manager import WatermarkManager
from config_manager import ConfigManager


class PhotoWatermarkApp:
    """主应用程序类"""
    
    def __init__(self):
        """初始化应用程序"""
        self.root = tk.Tk()
        self.root.title("Photo Watermark 2 - 图片水印工具")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # 初始化核心组件
        self.image_processor = ImageProcessor()
        self.watermark_manager = WatermarkManager()
        self.config_manager = ConfigManager()
        
        # 界面变量
        self.current_image = None
        self.preview_image = None
        self.selected_image_index = 0
        
        # 创建界面
        self.create_widgets()
        self.setup_drag_drop()
        self.load_last_settings()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧面板（图片列表）
        self.create_image_list_panel(main_frame)
        
        # 创建中央面板（预览区域）
        self.create_preview_panel(main_frame)
        
        # 创建右侧面板（水印设置）
        self.create_watermark_panel(main_frame)
        
        # 创建底部面板（操作按钮）
        self.create_control_panel(main_frame)
    
    def create_image_list_panel(self, parent):
        """创建图片列表面板"""
        # 图片列表框架
        list_frame = ttk.LabelFrame(parent, text="图片列表", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        # 按钮框架
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 导入按钮
        ttk.Button(button_frame, text="选择图片", 
                  command=self.select_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="选择文件夹", 
                  command=self.select_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="清空列表", 
                  command=self.clear_images).pack(side=tk.LEFT)
        
        # 图片列表
        self.image_listbox = tk.Listbox(list_frame, width=30, height=20)
        self.image_listbox.pack(fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.image_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_listbox.config(yscrollcommand=scrollbar.set)
    
    def create_preview_panel(self, parent):
        """创建预览面板"""
        # 预览框架
        preview_frame = ttk.LabelFrame(parent, text="预览", padding=10)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', width=400, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 预览控制按钮
        control_frame = ttk.Frame(preview_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="上一张", 
                  command=self.previous_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="下一张", 
                  command=self.next_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="刷新预览", 
                  command=self.refresh_preview).pack(side=tk.LEFT)
    
    def create_watermark_panel(self, parent):
        """创建水印设置面板"""
        # 水印设置框架
        watermark_frame = ttk.LabelFrame(parent, text="水印设置", padding=10)
        watermark_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 创建滚动区域
        canvas = tk.Canvas(watermark_frame, width=300)
        scrollbar = ttk.Scrollbar(watermark_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 水印类型选择
        type_frame = ttk.LabelFrame(scrollable_frame, text="水印类型", padding=5)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.watermark_type = tk.StringVar(value="text")
        ttk.Radiobutton(type_frame, text="文本水印", variable=self.watermark_type, 
                       value="text", command=self.on_watermark_type_change).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="图片水印", variable=self.watermark_type, 
                       value="image", command=self.on_watermark_type_change).pack(anchor=tk.W)
        
        # 文本水印设置
        self.create_text_watermark_settings(scrollable_frame)
        
        # 图片水印设置
        self.create_image_watermark_settings(scrollable_frame)
        
        # 通用设置
        self.create_common_settings(scrollable_frame)
        
        # 位置设置
        self.create_position_settings(scrollable_frame)
        
        # 模板管理
        self.create_template_settings(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_text_watermark_settings(self, parent):
        """创建文本水印设置"""
        text_frame = ttk.LabelFrame(parent, text="文本设置", padding=5)
        text_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文本内容
        ttk.Label(text_frame, text="文本内容:").pack(anchor=tk.W)
        self.text_content = tk.StringVar(value="Watermark")
        ttk.Entry(text_frame, textvariable=self.text_content, 
                 command=self.on_watermark_change).pack(fill=tk.X, pady=(0, 5))
        
        # 字体设置
        font_frame = ttk.Frame(text_frame)
        font_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(font_frame, text="字体:").pack(side=tk.LEFT)
        self.font_family = tk.StringVar(value="Arial")
        self.font_combo = ttk.Combobox(font_frame, textvariable=self.font_family, 
                                     width=15, state="readonly")
        self.font_combo.pack(side=tk.RIGHT)
        self.font_combo.bind('<<ComboboxSelected>>', self.on_watermark_change)
        
        # 字体大小
        size_frame = ttk.Frame(text_frame)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(size_frame, text="字体大小:").pack(side=tk.LEFT)
        self.font_size = tk.IntVar(value=24)
        size_spinbox = ttk.Spinbox(size_frame, from_=8, to=200, width=10,
                                  textvariable=self.font_size, command=self.on_watermark_change)
        size_spinbox.pack(side=tk.RIGHT)
        
        # 字体颜色
        color_frame = ttk.Frame(text_frame)
        color_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(color_frame, text="字体颜色:").pack(side=tk.LEFT)
        self.font_color = tk.StringVar(value="#FFFFFF")
        color_button = ttk.Button(color_frame, text="选择颜色", 
                                 command=self.choose_font_color)
        color_button.pack(side=tk.RIGHT)
        
        # 样式选项
        style_frame = ttk.Frame(text_frame)
        style_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.shadow_var = tk.BooleanVar()
        ttk.Checkbutton(style_frame, text="阴影", variable=self.shadow_var,
                       command=self.on_watermark_change).pack(side=tk.LEFT)
        
        self.outline_var = tk.BooleanVar()
        ttk.Checkbutton(style_frame, text="描边", variable=self.outline_var,
                       command=self.on_watermark_change).pack(side=tk.LEFT)
    
    def create_image_watermark_settings(self, parent):
        """创建图片水印设置"""
        image_frame = ttk.LabelFrame(parent, text="图片设置", padding=5)
        image_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 图片选择
        ttk.Label(image_frame, text="水印图片:").pack(anchor=tk.W)
        path_frame = ttk.Frame(image_frame)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.image_path = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.image_path, state="readonly")
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(path_frame, text="选择", command=self.select_watermark_image).pack(side=tk.RIGHT)
        
        # 缩放比例
        scale_frame = ttk.Frame(image_frame)
        scale_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(scale_frame, text="缩放比例:").pack(side=tk.LEFT)
        self.image_scale = tk.DoubleVar(value=1.0)
        scale_spinbox = ttk.Spinbox(scale_frame, from_=0.1, to=5.0, increment=0.1,
                                   width=10, textvariable=self.image_scale, 
                                   command=self.on_watermark_change)
        scale_spinbox.pack(side=tk.RIGHT)
    
    def create_common_settings(self, parent):
        """创建通用设置"""
        common_frame = ttk.LabelFrame(parent, text="通用设置", padding=5)
        common_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 透明度
        opacity_frame = ttk.Frame(common_frame)
        opacity_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(opacity_frame, text="透明度:").pack(side=tk.LEFT)
        self.opacity = tk.IntVar(value=80)
        opacity_scale = ttk.Scale(opacity_frame, from_=0, to=100, 
                                 variable=self.opacity, orient=tk.HORIZONTAL,
                                 command=self.on_watermark_change)
        opacity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 旋转角度
        rotation_frame = ttk.Frame(common_frame)
        rotation_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(rotation_frame, text="旋转角度:").pack(side=tk.LEFT)
        self.rotation = tk.IntVar(value=0)
        rotation_scale = ttk.Scale(rotation_frame, from_=-180, to=180, 
                                  variable=self.rotation, orient=tk.HORIZONTAL,
                                  command=self.on_watermark_change)
        rotation_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
    
    def create_position_settings(self, parent):
        """创建位置设置"""
        position_frame = ttk.LabelFrame(parent, text="位置设置", padding=5)
        position_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 九宫格位置选择
        positions = [
            ("左上", "top_left"), ("上中", "top_center"), ("右上", "top_right"),
            ("左中", "center_left"), ("中心", "center"), ("右中", "center_right"),
            ("左下", "bottom_left"), ("下中", "bottom_center"), ("右下", "bottom_right")
        ]
        
        self.position = tk.StringVar(value="bottom_right")
        
        for i, (label, value) in enumerate(positions):
            btn = ttk.Radiobutton(position_frame, text=label, variable=self.position,
                                 value=value, command=self.on_position_change)
            row = i // 3
            col = i % 3
            btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)
    
    def create_template_settings(self, parent):
        """创建模板设置"""
        template_frame = ttk.LabelFrame(parent, text="模板管理", padding=5)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模板名称
        ttk.Label(template_frame, text="模板名称:").pack(anchor=tk.W)
        self.template_name = tk.StringVar()
        ttk.Entry(template_frame, textvariable=self.template_name).pack(fill=tk.X, pady=(0, 5))
        
        # 模板按钮
        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(template_btn_frame, text="保存模板", 
                  command=self.save_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(template_btn_frame, text="加载模板", 
                  command=self.load_template).pack(side=tk.LEFT)
        
        # 模板列表
        ttk.Label(template_frame, text="已保存的模板:").pack(anchor=tk.W)
        self.template_listbox = tk.Listbox(template_frame, height=4)
        self.template_listbox.pack(fill=tk.X, pady=(0, 5))
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        
        # 模板操作按钮
        template_op_frame = ttk.Frame(template_frame)
        template_op_frame.pack(fill=tk.X)
        
        ttk.Button(template_op_frame, text="删除模板", 
                  command=self.delete_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(template_op_frame, text="刷新列表", 
                  command=self.refresh_template_list).pack(side=tk.LEFT)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 导出设置框架
        export_frame = ttk.LabelFrame(control_frame, text="导出设置", padding=5)
        export_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 输出文件夹
        output_frame = ttk.Frame(export_frame)
        output_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(output_frame, text="输出文件夹:").pack(side=tk.LEFT)
        self.output_folder = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_folder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        ttk.Button(output_frame, text="选择", command=self.select_output_folder).pack(side=tk.RIGHT)
        
        # 命名规则
        naming_frame = ttk.Frame(export_frame)
        naming_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(naming_frame, text="命名规则:").pack(side=tk.LEFT)
        self.naming_rule = tk.StringVar(value="original")
        ttk.Radiobutton(naming_frame, text="原名", variable=self.naming_rule, value="original").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(naming_frame, text="前缀", variable=self.naming_rule, value="prefix").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(naming_frame, text="后缀", variable=self.naming_rule, value="suffix").pack(side=tk.LEFT, padx=(5, 0))
        
        # 前缀/后缀输入
        prefix_frame = ttk.Frame(export_frame)
        prefix_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(prefix_frame, text="前缀:").pack(side=tk.LEFT)
        self.prefix = tk.StringVar(value="wm_")
        ttk.Entry(prefix_frame, textvariable=self.prefix, width=10).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(prefix_frame, text="后缀:").pack(side=tk.LEFT)
        self.suffix = tk.StringVar(value="_watermarked")
        ttk.Entry(prefix_frame, textvariable=self.suffix, width=15).pack(side=tk.LEFT, padx=(5, 0))
        
        # 输出格式和质量
        format_frame = ttk.Frame(export_frame)
        format_frame.pack(fill=tk.X)
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT)
        self.output_format = tk.StringVar(value="JPEG")
        ttk.Radiobutton(format_frame, text="JPEG", variable=self.output_format, value="JPEG").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(format_frame, text="PNG", variable=self.output_format, value="PNG").pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(format_frame, text="质量:").pack(side=tk.LEFT, padx=(20, 0))
        self.quality = tk.IntVar(value=95)
        ttk.Scale(format_frame, from_=1, to=100, variable=self.quality, 
                 orient=tk.HORIZONTAL, length=100).pack(side=tk.LEFT, padx=(5, 0))
        
        # 操作按钮框架
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(action_frame, text="批量导出", command=self.batch_export).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="导出当前", command=self.export_current).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="重置设置", command=self.reset_settings).pack(fill=tk.X)
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        # Windows下的拖拽功能需要额外的库支持
        # 这里先禁用，用户可以通过按钮选择文件
        pass
    
    def load_last_settings(self):
        """加载上次的设置"""
        # 加载默认水印配置
        default_config = self.config_manager.get_default_watermark_config()
        self.update_ui_from_config(default_config)
        
        # 加载上次的输出文件夹
        last_output = self.config_manager.get_setting('last_output_folder')
        if last_output:
            self.output_folder.set(last_output)
        
        # 刷新模板列表
        self.refresh_template_list()
        
        # 加载系统字体
        self.load_system_fonts()
    
    def load_system_fonts(self):
        """加载系统字体"""
        fonts = self.watermark_manager.get_available_fonts()
        self.font_combo['values'] = fonts
        if fonts and self.font_family.get() not in fonts:
            self.font_family.set(fonts[0])
    
    def update_ui_from_config(self, config):
        """从配置更新UI"""
        self.watermark_type.set(config.get('type', 'text'))
        self.text_content.set(config.get('text', 'Watermark'))
        self.font_family.set(config.get('font_family', 'Arial'))
        self.font_size.set(config.get('font_size', 24))
        self.font_color.set(config.get('font_color', '#FFFFFF'))
        self.opacity.set(config.get('opacity', 80))
        self.rotation.set(config.get('rotation', 0))
        self.position.set(config.get('position', 'bottom_right'))
        self.image_path.set(config.get('image_path', ''))
        self.image_scale.set(config.get('image_scale', 1.0))
        self.shadow_var.set(config.get('shadow', False))
        self.outline_var.set(config.get('outline', False))
    
    def get_current_config(self):
        """获取当前配置"""
        return {
            'type': self.watermark_type.get(),
            'text': self.text_content.get(),
            'font_family': self.font_family.get(),
            'font_size': self.font_size.get(),
            'font_color': self.font_color.get(),
            'opacity': self.opacity.get(),
            'rotation': self.rotation.get(),
            'position': self.position.get(),
            'image_path': self.image_path.get(),
            'image_scale': self.image_scale.get(),
            'shadow': self.shadow_var.get(),
            'outline': self.outline_var.get(),
            'outline_color': '#000000',
            'outline_width': 2
        }
    
    def select_images(self):
        """选择图片文件"""
        file_paths = self.image_processor.select_images(self.root)
        if file_paths:
            self.add_images(file_paths)
    
    def select_folder(self):
        """选择图片文件夹"""
        folder_path = self.image_processor.select_folder(self.root)
        if folder_path:
            added_count = self.image_processor.add_images_from_folder(folder_path)
            if added_count > 0:
                self.refresh_image_list()
                messagebox.showinfo("导入成功", f"成功导入 {added_count} 张图片")
            else:
                messagebox.showwarning("导入失败", "文件夹中没有找到支持的图片格式")
    
    def on_drop(self, event):
        """处理拖拽事件"""
        files = self.root.tk.splitlist(event.data)
        image_files = [f for f in files if self.image_processor.is_supported_image(f)]
        if image_files:
            self.add_images(image_files)
    
    def add_images(self, file_paths):
        """添加图片到列表"""
        added_count = 0
        for file_path in file_paths:
            if self.image_processor.add_image(file_path):
                added_count += 1
        
        if added_count > 0:
            self.refresh_image_list()
            if added_count < len(file_paths):
                messagebox.showwarning("部分导入失败", 
                                     f"成功导入 {added_count} 张图片，{len(file_paths) - added_count} 张图片格式不支持")
        else:
            messagebox.showerror("导入失败", "没有成功导入任何图片")
    
    def refresh_image_list(self):
        """刷新图片列表"""
        self.image_listbox.delete(0, tk.END)
        images = self.image_processor.get_image_list()
        for i, image_info in enumerate(images):
            self.image_listbox.insert(tk.END, f"{i+1}. {image_info['filename']}")
        
        # 如果有图片，选中第一张
        if images:
            self.image_listbox.selection_set(0)
            self.on_image_select(None)
    
    def on_image_select(self, event):
        """图片选择事件"""
        selection = self.image_listbox.curselection()
        if selection:
            index = selection[0]
            self.image_processor.set_current_image(index)
            self.selected_image_index = index
            self.refresh_preview()
    
    def previous_image(self):
        """上一张图片"""
        if self.selected_image_index > 0:
            self.selected_image_index -= 1
            self.image_listbox.selection_clear(0, tk.END)
            self.image_listbox.selection_set(self.selected_image_index)
            self.image_processor.set_current_image(self.selected_image_index)
            self.refresh_preview()
    
    def next_image(self):
        """下一张图片"""
        images = self.image_processor.get_image_list()
        if self.selected_image_index < len(images) - 1:
            self.selected_image_index += 1
            self.image_listbox.selection_clear(0, tk.END)
            self.image_listbox.selection_set(self.selected_image_index)
            self.image_processor.set_current_image(self.selected_image_index)
            self.refresh_preview()
    
    def clear_images(self):
        """清空图片列表"""
        if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
            self.image_processor.clear_images()
            self.refresh_image_list()
            self.preview_canvas.delete("all")
    
    def refresh_preview(self):
        """刷新预览"""
        current_image = self.image_processor.get_current_image()
        if current_image:
            # 更新水印配置
            config = self.get_current_config()
            self.watermark_manager.update_config(config)
            
            # 生成预览图片
            preview = self.watermark_manager.preview_watermark(current_image)
            self.display_preview(preview)
    
    def display_preview(self, image):
        """显示预览图片"""
        # 计算适合画布的尺寸
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # 画布还没有初始化，延迟刷新
            self.root.after(100, self.refresh_preview)
            return
        
        # 计算缩放比例
        img_width, img_height = image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # 不放大图片
        
        # 缩放图片
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 转换为Tkinter格式
        self.preview_image = ImageTk.PhotoImage(resized_image)
        
        # 清空画布并显示图片
        self.preview_canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_image)
    
    def on_watermark_type_change(self):
        """水印类型改变"""
        self.on_watermark_change()
    
    def on_watermark_change(self, *args):
        """水印设置改变"""
        self.refresh_preview()
    
    def on_position_change(self):
        """位置改变"""
        self.on_watermark_change()
    
    def choose_font_color(self):
        """选择字体颜色"""
        color = colorchooser.askcolor(color=self.font_color.get(), title="选择字体颜色")
        if color[1]:  # color[1] 是十六进制颜色值
            self.font_color.set(color[1])
            self.on_watermark_change()
    
    def select_watermark_image(self):
        """选择水印图片"""
        file_path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有图片", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.image_path.set(file_path)
            self.on_watermark_change()
    
    def save_template(self):
        """保存模板"""
        template_name = self.template_name.get().strip()
        if not template_name:
            messagebox.showerror("错误", "请输入模板名称")
            return
        
        config = self.get_current_config()
        if self.config_manager.save_template(template_name, config):
            messagebox.showinfo("成功", f"模板 '{template_name}' 保存成功")
            self.refresh_template_list()
            self.template_name.set("")
        else:
            messagebox.showerror("错误", "保存模板失败")
    
    def load_template(self):
        """加载模板"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请选择要加载的模板")
            return
        
        template_name = self.template_listbox.get(selection[0])
        template = self.config_manager.load_template(template_name)
        if template:
            self.update_ui_from_config(template)
            self.on_watermark_change()
            messagebox.showinfo("成功", f"模板 '{template_name}' 加载成功")
        else:
            messagebox.showerror("错误", "加载模板失败")
    
    def delete_template(self):
        """删除模板"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请选择要删除的模板")
            return
        
        template_name = self.template_listbox.get(selection[0])
        if messagebox.askyesno("确认", f"确定要删除模板 '{template_name}' 吗？"):
            if self.config_manager.delete_template(template_name):
                messagebox.showinfo("成功", f"模板 '{template_name}' 删除成功")
                self.refresh_template_list()
            else:
                messagebox.showerror("错误", "删除模板失败")
    
    def refresh_template_list(self):
        """刷新模板列表"""
        self.template_listbox.delete(0, tk.END)
        templates = self.config_manager.list_templates()
        for template_name in templates:
            self.template_listbox.insert(tk.END, template_name)
    
    def on_template_select(self, event):
        """模板选择事件"""
        selection = self.template_listbox.curselection()
        if selection:
            template_name = self.template_listbox.get(selection[0])
            self.template_name.set(template_name)
    
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def batch_export(self):
        """批量导出"""
        images = self.image_processor.get_image_list()
        if not images:
            messagebox.showerror("错误", "没有图片可导出")
            return
        
        output_folder = self.output_folder.get().strip()
        if not output_folder:
            messagebox.showerror("错误", "请选择输出文件夹")
            return
        
        # 在新线程中执行导出
        def export_thread():
            try:
                # 更新水印配置
                config = self.get_current_config()
                self.watermark_manager.update_config(config)
                
                # 批量应用水印并导出
                results = {
                    'success_count': 0,
                    'failed_count': 0,
                    'failed_files': []
                }
                
                for i, image_info in enumerate(images):
                    try:
                        # 应用水印
                        watermarked = self.watermark_manager.preview_watermark(image_info['image'])
                        
                        # 生成输出文件名
                        original_name = Path(image_info['file_path']).stem
                        original_ext = Path(image_info['file_path']).suffix
                        
                        naming_rule = self.naming_rule.get()
                        if naming_rule == 'prefix':
                            new_name = f"{self.prefix.get()}{original_name}{original_ext}"
                        elif naming_rule == 'suffix':
                            new_name = f"{original_name}{self.suffix.get()}{original_ext}"
                        else:
                            new_name = f"{original_name}{original_ext}"
                        
                        # 确保输出格式扩展名正确
                        if self.output_format.get() == 'JPEG' and not new_name.lower().endswith(('.jpg', '.jpeg')):
                            new_name = f"{Path(new_name).stem}.jpg"
                        elif self.output_format.get() == 'PNG' and not new_name.lower().endswith('.png'):
                            new_name = f"{Path(new_name).stem}.png"
                        
                        output_file_path = Path(output_folder) / new_name
                        
                        # 保存图片
                        if self.image_processor.save_image(watermarked, str(output_file_path), 
                                                         self.output_format.get(), self.quality.get()):
                            results['success_count'] += 1
                        else:
                            results['failed_count'] += 1
                            results['failed_files'].append(image_info['filename'])
                            
                    except Exception as e:
                        results['failed_count'] += 1
                        results['failed_files'].append(image_info['filename'])
                        print(f"导出图片失败: {image_info['filename']}, 错误: {e}")
                
                # 在主线程中显示结果
                self.root.after(0, lambda: self.show_export_results(results))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("导出失败", f"批量导出过程中发生错误: {e}"))
        
        # 显示进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("导出进度")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 居中显示
        progress_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        ttk.Label(progress_window, text="正在导出图片，请稍候...").pack(pady=20)
        
        # 启动导出线程
        export_thread = threading.Thread(target=export_thread)
        export_thread.daemon = True
        export_thread.start()
        
        # 延迟关闭进度窗口
        def close_progress():
            try:
                progress_window.destroy()
            except:
                pass
        
        progress_window.after(1000, close_progress)
    
    def show_export_results(self, results):
        """显示导出结果"""
        message = f"导出完成！\n成功: {results['success_count']} 张\n失败: {results['failed_count']} 张"
        if results['failed_files']:
            message += f"\n\n失败的文件:\n" + "\n".join(results['failed_files'][:5])
            if len(results['failed_files']) > 5:
                message += f"\n... 还有 {len(results['failed_files']) - 5} 个文件"
        
        messagebox.showinfo("导出结果", message)
    
    def export_current(self):
        """导出当前图片"""
        current_image = self.image_processor.get_current_image()
        if not current_image:
            messagebox.showerror("错误", "没有选中的图片")
            return
        
        output_folder = self.output_folder.get().strip()
        if not output_folder:
            messagebox.showerror("错误", "请选择输出文件夹")
            return
        
        try:
            # 更新水印配置
            config = self.get_current_config()
            self.watermark_manager.update_config(config)
            
            # 应用水印
            watermarked = self.watermark_manager.preview_watermark(current_image)
            
            # 生成输出文件名
            current_info = self.image_processor.get_current_image_info()
            original_name = Path(current_info['file_path']).stem
            original_ext = Path(current_info['file_path']).suffix
            
            naming_rule = self.naming_rule.get()
            if naming_rule == 'prefix':
                new_name = f"{self.prefix.get()}{original_name}{original_ext}"
            elif naming_rule == 'suffix':
                new_name = f"{original_name}{self.suffix.get()}{original_ext}"
            else:
                new_name = f"{original_name}{original_ext}"
            
            # 确保输出格式扩展名正确
            if self.output_format.get() == 'JPEG' and not new_name.lower().endswith(('.jpg', '.jpeg')):
                new_name = f"{Path(new_name).stem}.jpg"
            elif self.output_format.get() == 'PNG' and not new_name.lower().endswith('.png'):
                new_name = f"{Path(new_name).stem}.png"
            
            output_file_path = Path(output_folder) / new_name
            
            # 保存图片
            if self.image_processor.save_image(watermarked, str(output_file_path), 
                                             self.output_format.get(), self.quality.get()):
                messagebox.showinfo("成功", f"图片已导出到: {output_file_path}")
            else:
                messagebox.showerror("错误", "导出图片失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出过程中发生错误: {e}")
    
    def reset_settings(self):
        """重置设置"""
        if messagebox.askyesno("确认", "确定要重置所有设置吗？"):
            # 重置为默认配置
            default_config = self.config_manager.default_settings["default_watermark"]
            self.update_ui_from_config(default_config)
            self.on_watermark_change()
            messagebox.showinfo("成功", "设置已重置")
    
    def on_closing(self):
        """窗口关闭事件"""
        # 保存当前设置
        config = self.get_current_config()
        self.config_manager.update_default_watermark_config(config)
        self.config_manager.set_setting('last_output_folder', self.output_folder.get())
        
        # 清理资源
        self.config_manager.cleanup()
        
        # 关闭窗口
        self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


def main():
    """主函数"""
    try:
        app = PhotoWatermarkApp()
        app.run()
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        messagebox.showerror("错误", f"应用程序启动失败: {e}")


if __name__ == "__main__":
    main()