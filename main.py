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

# 尝试导入拖拽库
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    print("警告: tkinterdnd2 未安装，拖拽功能将不可用")
    print("安装方法: pip install tkinterdnd2")

from image_processor import ImageProcessor
from watermark_manager import WatermarkManager
from config_manager import ConfigManager


class PhotoWatermarkApp:
    """主应用程序类"""
    
    def __init__(self):
        """初始化应用程序"""
        # 根据是否有拖拽库支持创建不同的根窗口
        if DRAG_DROP_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
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
        self.watermark_type = tk.StringVar(value="text")
        
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
        
        # 创建可调整大小的PanedWindow
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建左侧面板（图片列表）
        self.create_image_list_panel(self.paned_window)
        
        # 创建中央面板（预览区域）
        self.create_preview_panel(self.paned_window)
        
        # 创建右侧面板（水印设置）
        self.create_watermark_panel(self.paned_window)
        
        # 创建底部面板（操作按钮）
        self.create_control_panel(main_frame)
    
    def create_image_list_panel(self, parent):
        """创建图片列表面板"""
        # 图片列表框架
        list_frame = ttk.LabelFrame(parent, text="图片列表", padding=10)
        self.paned_window.add(list_frame, weight=1)
        
        # 按钮框架
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 导入按钮
        ttk.Button(button_frame, text="选择单张", 
                  command=self.select_single_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="批量选择", 
                  command=self.select_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="选择文件夹", 
                  command=self.select_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="清空列表", 
                  command=self.clear_images).pack(side=tk.LEFT)
        
        # 图片列表（使用Treeview显示缩略图）
        self.image_tree = ttk.Treeview(list_frame, columns=('name',), show='tree headings', height=20)
        self.image_tree.heading('#0', text='缩略图', anchor='w')
        self.image_tree.heading('name', text='文件名', anchor='w')
        self.image_tree.column('#0', width=60, minwidth=60)
        self.image_tree.column('name', width=200, minwidth=100)
        
        # 设置行高以容纳缩略图
        style = ttk.Style()
        style.configure("Treeview", rowheight=60)  # 设置行高为60像素，适配50像素缩略图
        
        self.image_tree.pack(fill=tk.BOTH, expand=True)
        self.image_tree.bind('<<TreeviewSelect>>', self.on_image_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.image_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_tree.config(yscrollcommand=scrollbar.set)
    
    def create_preview_panel(self, parent):
        """创建预览面板"""
        # 预览框架
        preview_frame = ttk.LabelFrame(parent, text="预览", padding=10)
        self.paned_window.add(preview_frame, weight=2)
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', width=400, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件用于拖拽水印
        self.preview_canvas.bind('<ButtonPress-1>', self.on_watermark_drag_start)
        self.preview_canvas.bind('<B1-Motion>', self.on_watermark_drag_motion)
        self.preview_canvas.bind('<ButtonRelease-1>', self.on_watermark_drag_end)
        
        # 水印拖拽状态
        self.watermark_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.custom_watermark_position = None  # (x, y) 相对于图片的位置
        
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
        self.paned_window.add(watermark_frame, weight=1)
        
        # 创建Notebook（Tab页）
        self.notebook = ttk.Notebook(watermark_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建文本水印Tab
        self.create_text_watermark_tab()
        
        # 创建图片水印Tab
        self.create_image_watermark_tab()
        
        # 绑定Tab切换事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
    
    def create_text_watermark_tab(self):
        """创建文本水印Tab页"""
        # 创建滚动区域
        text_tab = ttk.Frame(self.notebook)
        self.notebook.add(text_tab, text="文本水印")
        
        canvas = tk.Canvas(text_tab, width=300)
        scrollbar = ttk.Scrollbar(text_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 文本水印设置
        self.create_text_watermark_settings(scrollable_frame)
        
        # 通用设置
        self.create_common_settings(scrollable_frame)
        
        # 位置设置
        self.create_position_settings(scrollable_frame)
        
        # 模板管理
        self.create_template_settings(scrollable_frame, "text")
        
        # 导出设置
        self.create_export_settings(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮
        self._bind_mousewheel(canvas)
    
    def create_image_watermark_tab(self):
        """创建图片水印Tab页"""
        # 创建滚动区域
        image_tab = ttk.Frame(self.notebook)
        self.notebook.add(image_tab, text="图片水印")
        
        canvas = tk.Canvas(image_tab, width=300)
        scrollbar = ttk.Scrollbar(image_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 图片水印设置
        self.create_image_watermark_settings(scrollable_frame)
        
        # 通用设置（图片水印也需要）
        self.create_common_settings_for_image(scrollable_frame)
        
        # 位置设置（图片水印也需要）
        self.create_position_settings_for_image(scrollable_frame)
        
        # 模板管理（图片水印独立）
        self.create_template_settings(scrollable_frame, "image")
        
        # 导出设置（共用）
        self.create_export_settings_for_image(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮
        self._bind_mousewheel(canvas)
    
    def _bind_mousewheel(self, canvas):
        """绑定鼠标滚轮事件"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def on_tab_changed(self, event):
        """Tab切换事件"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            self.watermark_type.set("text")
        else:
            self.watermark_type.set("image")
        self.on_watermark_change()
    
    def create_text_watermark_settings(self, parent):
        """创建文本水印设置"""
        text_frame = ttk.LabelFrame(parent, text="文本设置", padding=5)
        text_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文本内容
        ttk.Label(text_frame, text="文本内容:").pack(anchor=tk.W)
        self.text_content = tk.StringVar(value="Watermark")
        text_entry = ttk.Entry(text_frame, textvariable=self.text_content)
        text_entry.pack(fill=tk.X, pady=(0, 5))
        text_entry.bind('<KeyRelease>', self.on_watermark_change)
        
        # 字体设置
        font_frame = ttk.Frame(text_frame)
        font_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(font_frame, text="字体:").pack(side=tk.LEFT)
        self.font_family = tk.StringVar(value="Arial")
        self.font_combo = ttk.Combobox(font_frame, textvariable=self.font_family, 
                                     width=15, state="readonly")
        self.font_combo.pack(side=tk.RIGHT)
        self.font_combo.bind('<<ComboboxSelected>>', self.on_watermark_change)
        
        # 字体样式（粗体、斜体）
        style_frame = ttk.Frame(text_frame)
        style_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(style_frame, text="样式:").pack(side=tk.LEFT)
        self.font_bold = tk.BooleanVar()
        ttk.Checkbutton(style_frame, text="粗体", variable=self.font_bold,
                       command=self.on_watermark_change).pack(side=tk.LEFT, padx=(5, 0))
        
        self.font_italic = tk.BooleanVar()
        ttk.Checkbutton(style_frame, text="斜体", variable=self.font_italic,
                       command=self.on_watermark_change).pack(side=tk.LEFT, padx=(10, 0))
        
        # 字体大小
        size_frame = ttk.Frame(text_frame)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(size_frame, text="字体大小:").pack(side=tk.LEFT)
        self.font_size = tk.IntVar(value=24)
        size_spinbox = ttk.Spinbox(size_frame, from_=8, to=200, width=10,
                                  textvariable=self.font_size)
        size_spinbox.pack(side=tk.RIGHT)
        size_spinbox.bind('<KeyRelease>', self.on_watermark_change)
        size_spinbox.bind('<ButtonRelease-1>', self.on_watermark_change)
        
        # 字体颜色
        color_frame = ttk.Frame(text_frame)
        color_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(color_frame, text="字体颜色:").pack(side=tk.LEFT)
        self.font_color = tk.StringVar(value="#FFFFFF")
        
        # 创建颜色显示和选择按钮
        color_display_frame = ttk.Frame(color_frame)
        color_display_frame.pack(side=tk.RIGHT)
        
        # 颜色预览框
        self.color_preview = tk.Frame(color_display_frame, width=20, height=20, 
                                     bg=self.font_color.get(), relief="sunken", bd=2)
        self.color_preview.pack(side=tk.LEFT, padx=(0, 5))
        
        # 颜色值标签
        self.color_label = ttk.Label(color_display_frame, text=self.font_color.get())
        self.color_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 选择颜色按钮
        color_button = ttk.Button(color_display_frame, text="选择颜色", 
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
                                   width=10, textvariable=self.image_scale)
        scale_spinbox.pack(side=tk.RIGHT)
        scale_spinbox.bind('<KeyRelease>', self.on_watermark_change)
        scale_spinbox.bind('<ButtonRelease-1>', self.on_watermark_change)
        
        # 添加说明标签
        ttk.Label(image_frame, text="💡 支持PNG透明图片", 
                 font=('', 8), foreground='gray').pack(anchor=tk.W, pady=(5, 0))
    
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
        
        # 添加自定义位置选项
        ttk.Radiobutton(position_frame, text="自定义（拖拽）", variable=self.position,
                       value="custom", command=self.on_position_change).grid(row=3, column=0, columnspan=3, padx=2, pady=2, sticky=tk.W)
        
        # 添加提示标签
        ttk.Label(position_frame, text="💡 可在预览图上拖拽水印", 
                 font=('', 8), foreground='gray').grid(row=4, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)
    
    def create_common_settings_for_image(self, parent):
        """创建图片水印的通用设置"""
        common_frame = ttk.LabelFrame(parent, text="通用设置", padding=5)
        common_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 透明度（复用文本水印的opacity变量）
        opacity_frame = ttk.Frame(common_frame)
        opacity_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(opacity_frame, text="透明度:").pack(side=tk.LEFT)
        opacity_scale = ttk.Scale(opacity_frame, from_=0, to=100, 
                                 variable=self.opacity, orient=tk.HORIZONTAL,
                                 command=self.on_watermark_change)
        opacity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 旋转角度（复用rotation变量）
        rotation_frame = ttk.Frame(common_frame)
        rotation_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(rotation_frame, text="旋转角度:").pack(side=tk.LEFT)
        rotation_scale = ttk.Scale(rotation_frame, from_=-180, to=180, 
                                  variable=self.rotation, orient=tk.HORIZONTAL,
                                  command=self.on_watermark_change)
        rotation_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
    
    def create_position_settings_for_image(self, parent):
        """创建图片水印的位置设置"""
        position_frame = ttk.LabelFrame(parent, text="位置设置", padding=5)
        position_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 九宫格位置选择（复用position变量）
        positions = [
            ("左上", "top_left"), ("上中", "top_center"), ("右上", "top_right"),
            ("左中", "center_left"), ("中心", "center"), ("右中", "center_right"),
            ("左下", "bottom_left"), ("下中", "bottom_center"), ("右下", "bottom_right")
        ]
        
        for i, (label, value) in enumerate(positions):
            btn = ttk.Radiobutton(position_frame, text=label, variable=self.position,
                                 value=value, command=self.on_position_change)
            row = i // 3
            col = i % 3
            btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)
        
        # 添加自定义位置选项
        ttk.Radiobutton(position_frame, text="自定义（拖拽）", variable=self.position,
                       value="custom", command=self.on_position_change).grid(row=3, column=0, columnspan=3, padx=2, pady=2, sticky=tk.W)
        
        # 添加提示标签
        ttk.Label(position_frame, text="💡 可在预览图上拖拽水印", 
                 font=('', 8), foreground='gray').grid(row=4, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)
    
    def create_export_settings_for_image(self, parent):
        """创建图片水印的导出设置"""
        # 直接调用导出设置创建函数（共用同一组变量）
        self.create_export_settings(parent)
    
    def create_template_settings(self, parent, watermark_type="text"):
        """创建模板设置"""
        template_frame = ttk.LabelFrame(parent, text="模板管理", padding=5)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 根据类型使用不同的变量
        if watermark_type == "text":
            # 文本水印模板
            ttk.Label(template_frame, text="选择模板:").pack(anchor=tk.W)
            self.template_name_text = tk.StringVar()
            self.template_combo_text = ttk.Combobox(template_frame, textvariable=self.template_name_text, 
                                              state="readonly", width=20)
            self.template_combo_text.pack(fill=tk.X, pady=(0, 5))
            self.template_combo_text.bind('<<ComboboxSelected>>', lambda e: self.on_template_select("text"))
            
            # 新模板名称输入
            ttk.Label(template_frame, text="新模板名称:").pack(anchor=tk.W)
            self.new_template_name_text = tk.StringVar()
            new_template_entry = ttk.Entry(template_frame, textvariable=self.new_template_name_text)
            new_template_entry.pack(fill=tk.X, pady=(0, 5))
            
            # 模板按钮
            template_btn_frame = ttk.Frame(template_frame)
            template_btn_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Button(template_btn_frame, text="保存模板", 
                      command=lambda: self.save_template("text")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(template_btn_frame, text="加载模板", 
                      command=lambda: self.load_template("text")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(template_btn_frame, text="删除模板", 
                      command=lambda: self.delete_template("text")).pack(side=tk.LEFT)
        else:
            # 图片水印模板
            ttk.Label(template_frame, text="选择模板:").pack(anchor=tk.W)
            self.template_name_image = tk.StringVar()
            self.template_combo_image = ttk.Combobox(template_frame, textvariable=self.template_name_image, 
                                                state="readonly", width=20)
            self.template_combo_image.pack(fill=tk.X, pady=(0, 5))
            self.template_combo_image.bind('<<ComboboxSelected>>', lambda e: self.on_template_select("image"))
            
            # 新模板名称输入
            ttk.Label(template_frame, text="新模板名称:").pack(anchor=tk.W)
            self.new_template_name_image = tk.StringVar()
            new_template_entry = ttk.Entry(template_frame, textvariable=self.new_template_name_image)
            new_template_entry.pack(fill=tk.X, pady=(0, 5))
            
            # 模板按钮
            template_btn_frame = ttk.Frame(template_frame)
            template_btn_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Button(template_btn_frame, text="保存模板", 
                      command=lambda: self.save_template("image")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(template_btn_frame, text="加载模板", 
                      command=lambda: self.load_template("image")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(template_btn_frame, text="删除模板", 
                      command=lambda: self.delete_template("image")).pack(side=tk.LEFT)
    
    def create_export_settings(self, parent):
        """创建导出设置"""
        export_frame = ttk.LabelFrame(parent, text="导出设置", padding=5)
        export_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输出文件夹
        ttk.Label(export_frame, text="输出文件夹:").pack(anchor=tk.W)
        output_frame = ttk.Frame(export_frame)
        output_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.output_folder = tk.StringVar()
        self.output_folder_entry = ttk.Entry(output_frame, textvariable=self.output_folder, state="readonly")
        self.output_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="选择", command=self.select_output_folder).pack(side=tk.RIGHT)
        
        # 导出图片命名
        ttk.Label(export_frame, text="导出图片命名:").pack(anchor=tk.W)
        naming_frame = ttk.Frame(export_frame)
        naming_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.naming_rule = tk.StringVar(value="original")
        ttk.Radiobutton(naming_frame, text="原名", variable=self.naming_rule, value="original").pack(side=tk.LEFT)
        ttk.Radiobutton(naming_frame, text="前缀", variable=self.naming_rule, value="prefix").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(naming_frame, text="后缀", variable=self.naming_rule, value="suffix").pack(side=tk.LEFT, padx=(10, 0))
        
        # 前缀/后缀输入
        prefix_frame = ttk.Frame(export_frame)
        prefix_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(prefix_frame, text="前缀:").pack(side=tk.LEFT)
        self.prefix = tk.StringVar(value="wm_")
        ttk.Entry(prefix_frame, textvariable=self.prefix, width=10).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(prefix_frame, text="后缀:").pack(side=tk.LEFT)
        self.suffix = tk.StringVar(value="_watermarked")
        ttk.Entry(prefix_frame, textvariable=self.suffix, width=15).pack(side=tk.LEFT, padx=(5, 0))
        
        # 输出格式
        ttk.Label(export_frame, text="输出格式:").pack(anchor=tk.W)
        format_frame = ttk.Frame(export_frame)
        format_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.output_format = tk.StringVar(value="JPEG")
        ttk.Radiobutton(format_frame, text="JPEG", variable=self.output_format, 
                       value="JPEG", command=self.on_format_change).pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="PNG", variable=self.output_format, 
                       value="PNG", command=self.on_format_change).pack(side=tk.LEFT, padx=(10, 0))
        
        # 质量设置（仅JPEG格式显示）
        self.quality_frame = ttk.Frame(export_frame)
        self.quality_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.quality_frame, text="质量:").pack(side=tk.LEFT)
        self.quality = tk.IntVar(value=95)
        self.quality_scale = ttk.Scale(self.quality_frame, from_=1, to=100, variable=self.quality, 
                                     orient=tk.HORIZONTAL, length=100)
        self.quality_scale.pack(side=tk.LEFT, padx=(5, 0))
        
        self.quality_label = ttk.Label(self.quality_frame, text="95")
        self.quality_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 绑定质量变化事件
        self.quality_scale.bind('<Motion>', self.on_quality_change)
        
        # 初始化格式显示
        self.on_format_change()
        
        # 图片尺寸调整
        ttk.Label(export_frame, text="图片尺寸调整:").pack(anchor=tk.W)
        size_frame = ttk.Frame(export_frame)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.resize_enabled = tk.BooleanVar()
        ttk.Checkbutton(size_frame, text="调整尺寸", variable=self.resize_enabled,
                       command=self.on_resize_toggle).pack(side=tk.LEFT)
        
        self.resize_frame = ttk.Frame(export_frame)
        self.resize_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 百分比调整（单独一行）
        percentage_frame = ttk.Frame(self.resize_frame)
        percentage_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.resize_method = tk.StringVar(value="percentage")
        ttk.Radiobutton(percentage_frame, text="按百分比:", variable=self.resize_method, 
                       value="percentage", command=self.on_resize_method_change).pack(side=tk.LEFT)
        self.resize_percentage = tk.IntVar(value=100)
        ttk.Spinbox(percentage_frame, from_=10, to=500, width=8,
                   textvariable=self.resize_percentage).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(percentage_frame, text="%").pack(side=tk.LEFT, padx=(2, 0))
        
        # 宽高调整（一行）
        size_wh_frame = ttk.Frame(self.resize_frame)
        size_wh_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Radiobutton(size_wh_frame, text="宽高:", variable=self.resize_method, 
                       value="width_height", command=self.on_resize_method_change).pack(side=tk.LEFT)
        
        ttk.Label(size_wh_frame, text="宽:").pack(side=tk.LEFT, padx=(5, 0))
        self.resize_width = tk.IntVar(value=800)
        width_spinbox = ttk.Spinbox(size_wh_frame, from_=10, to=10000, width=8,
                   textvariable=self.resize_width, command=self.on_width_change)
        width_spinbox.pack(side=tk.LEFT, padx=(2, 0))
        width_spinbox.bind('<Return>', lambda e: self.on_width_change())
        width_spinbox.bind('<KeyRelease>', lambda e: self.on_width_change())
        
        ttk.Label(size_wh_frame, text="高:").pack(side=tk.LEFT, padx=(10, 0))
        self.resize_height = tk.IntVar(value=600)
        height_spinbox = ttk.Spinbox(size_wh_frame, from_=10, to=10000, width=8,
                   textvariable=self.resize_height, command=self.on_height_change)
        height_spinbox.pack(side=tk.LEFT, padx=(2, 0))
        height_spinbox.bind('<Return>', lambda e: self.on_height_change())
        height_spinbox.bind('<KeyRelease>', lambda e: self.on_height_change())
        
        # 保持宽高比选项
        self.keep_aspect_ratio = tk.BooleanVar(value=True)
        ttk.Checkbutton(size_wh_frame, text="保持比例", variable=self.keep_aspect_ratio).pack(side=tk.LEFT, padx=(10, 0))
        
        # 初始化尺寸调整显示
        self.on_resize_toggle()
        
        # 导出按钮
        export_btn_frame = ttk.Frame(export_frame)
        export_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(export_btn_frame, text="批量导出", command=self.batch_export).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_btn_frame, text="导出当前", command=self.export_current).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_btn_frame, text="重置设置", command=self.reset_settings).pack(side=tk.LEFT)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        # 现在控制面板只包含简单的状态信息
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 状态标签
        self.status_label = ttk.Label(control_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        if not DRAG_DROP_AVAILABLE:
            print("拖拽功能不可用，请使用按钮导入图片")
            return
        
        try:
            # 为整个窗口注册拖拽目标
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
            
            # 为图片列表区域注册拖拽
            self.image_tree.drop_target_register(DND_FILES)
            self.image_tree.dnd_bind('<<Drop>>', self.on_drop)
            
            # 为预览区域注册拖拽
            self.preview_canvas.drop_target_register(DND_FILES)
            self.preview_canvas.dnd_bind('<<Drop>>', self.on_drop)
            
            print("✓ 拖拽功能已启用")
            self.status_label.config(text="就绪 - 支持拖拽导入")
        except Exception as e:
            print(f"拖拽功能设置失败: {e}")
    
    def on_drop(self, event):
        """处理拖拽放下事件"""
        try:
            # 获取拖拽的文件路径
            files = event.data
            
            # 处理不同格式的路径数据
            if isinstance(files, str):
                # 处理Windows路径格式
                if files.startswith('{') and files.endswith('}'):
                    # 多个文件用{}包裹
                    files = files[1:-1].split('} {')
                else:
                    # 单个文件
                    files = [files]
            elif isinstance(files, tuple):
                files = list(files)
            else:
                files = [files]
            
            # 清理路径（移除可能的引号）
            clean_files = []
            for f in files:
                f = f.strip().strip('"').strip("'")
                if f:
                    clean_files.append(f)
            
            # 过滤出图片文件
            image_files = [f for f in clean_files if self.image_processor.is_supported_image(f)]
            
            if image_files:
                self.add_images(image_files)
                self.status_label.config(text=f"已通过拖拽导入 {len(image_files)} 张图片")
            else:
                messagebox.showwarning("导入失败", "拖拽的文件中没有支持的图片格式")
                
        except Exception as e:
            print(f"拖拽导入失败: {e}")
            messagebox.showerror("错误", f"拖拽导入失败: {str(e)}")
    
    def load_last_settings(self):
        """加载上次的设置"""
        # 加载默认水印配置
        default_config = self.config_manager.get_default_watermark_config()
        self.update_ui_from_config(default_config)
        
        # 加载上次的输出文件夹
        last_output = self.config_manager.get_setting('last_output_folder')
        if last_output:
            self.output_folder.set(last_output)
        
        # 刷新模板列表（文本和图片）
        if hasattr(self, 'template_combo_text'):
            self.refresh_template_list("text")
        if hasattr(self, 'template_combo_image'):
            self.refresh_template_list("image")
        
        # 加载系统字体
        self.load_system_fonts()
    
    def load_system_fonts(self):
        """加载系统字体"""
        fonts = self.watermark_manager.get_available_fonts()
        
        # 临时解绑事件，避免在加载字体列表时触发刷新
        self.font_combo.unbind('<<ComboboxSelected>>')
        
        # 更新字体列表
        self.font_combo['values'] = fonts
        if fonts and self.font_family.get() not in fonts:
            self.font_family.set(fonts[0])
        
        # 重新绑定事件
        self.font_combo.bind('<<ComboboxSelected>>', self.on_watermark_change)
    
    def update_ui_from_config(self, config):
        """从配置更新UI"""
        self.watermark_type.set(config.get('type', 'text'))
        self.text_content.set(config.get('text', 'Watermark'))
        self.font_family.set(config.get('font_family', 'Arial'))
        self.font_size.set(config.get('font_size', 24))
        
        # 更新颜色设置
        color_value = config.get('font_color', '#FFFFFF')
        self.font_color.set(color_value)
        # 更新颜色显示（如果组件已创建）
        if hasattr(self, 'color_preview'):
            self.color_preview.config(bg=color_value)
        if hasattr(self, 'color_label'):
            self.color_label.config(text=color_value)
        
        self.opacity.set(config.get('opacity', 80))
        self.rotation.set(config.get('rotation', 0))
        self.position.set(config.get('position', 'bottom_right'))
        self.image_path.set(config.get('image_path', ''))
        self.image_scale.set(config.get('image_scale', 1.0))
        self.shadow_var.set(config.get('shadow', False))
        self.outline_var.set(config.get('outline', False))
        
        # 更新字体样式
        if hasattr(self, 'font_bold'):
            self.font_bold.set(config.get('font_bold', False))
        if hasattr(self, 'font_italic'):
            self.font_italic.set(config.get('font_italic', False))
        
        # 恢复自定义位置
        if 'custom_position' in config:
            self.custom_watermark_position = tuple(config['custom_position'])
        else:
            self.custom_watermark_position = None
    
    def get_current_config(self):
        """获取当前配置"""
        config = {
            'type': self.watermark_type.get(),
            'text': self.text_content.get(),
            'font_family': self.font_family.get(),
            'font_size': self.font_size.get(),
            'font_bold': self.font_bold.get(),
            'font_italic': self.font_italic.get(),
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
        
        # 如果是自定义位置，保存坐标
        if self.position.get() == 'custom' and self.custom_watermark_position:
            config['custom_position'] = self.custom_watermark_position
        
        return config
    
    def select_single_image(self):
        """选择单张图片文件"""
        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("PNG文件", "*.png"),
                ("BMP文件", "*.bmp"),
                ("TIFF文件", "*.tiff *.tif"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.add_images([file_path])
    
    def select_images(self):
        """批量选择图片文件"""
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
        # 清空现有项目
        for item in self.image_tree.get_children():
            self.image_tree.delete(item)
        
        images = self.image_processor.get_image_list()
        
        for i, image_info in enumerate(images):
            # 创建缩略图
            thumbnail = image_info['thumbnail']
            if thumbnail:
                # 调整缩略图大小
                thumbnail = thumbnail.resize((50, 50), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(thumbnail)
                
                # 插入到树形控件
                item_id = self.image_tree.insert('', 'end', 
                                               image=photo, 
                                               text=f"{i+1}",
                                               values=(image_info['filename'],))
                
                # 保存图片引用防止被垃圾回收
                if not hasattr(self, 'thumbnails'):
                    self.thumbnails = []
                self.thumbnails.append(photo)
        
        # 如果有图片，选中第一张
        if images:
            first_item = self.image_tree.get_children()[0]
            self.image_tree.selection_set(first_item)
            self.on_image_select(None)
    
    def on_image_select(self, event):
        """图片选择事件"""
        selection = self.image_tree.selection()
        if selection:
            # 获取选中项目的索引
            item = selection[0]
            index = self.image_tree.index(item)
            self.image_processor.set_current_image(index)
            self.selected_image_index = index
            self.refresh_preview()
    
    def previous_image(self):
        """上一张图片"""
        if self.selected_image_index > 0:
            self.selected_image_index -= 1
            # 更新树形控件选择
            children = self.image_tree.get_children()
            if self.selected_image_index < len(children):
                self.image_tree.selection_set(children[self.selected_image_index])
                self.image_processor.set_current_image(self.selected_image_index)
                self.refresh_preview()
    
    def next_image(self):
        """下一张图片"""
        images = self.image_processor.get_image_list()
        if self.selected_image_index < len(images) - 1:
            self.selected_image_index += 1
            # 更新树形控件选择
            children = self.image_tree.get_children()
            if self.selected_image_index < len(children):
                self.image_tree.selection_set(children[self.selected_image_index])
                self.image_processor.set_current_image(self.selected_image_index)
                self.refresh_preview()
    
    def clear_images(self):
        """清空图片列表"""
        if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
            self.image_processor.clear_images()
            # 清空缩略图引用
            if hasattr(self, 'thumbnails'):
                self.thumbnails.clear()
            self.refresh_image_list()
            self.preview_canvas.delete("all")
    
    def refresh_preview(self):
        """刷新预览"""
        current_image = self.image_processor.get_current_image()
        if current_image:
            # 更新水印配置
            config = self.get_current_config()
            self.watermark_manager.update_config(config)
            
            # 生成预览图片，使用自定义位置
            if self.custom_watermark_position and self.position.get() == 'custom':
                preview = self.watermark_manager.preview_watermark_with_position(
                    current_image, 
                    self.custom_watermark_position
                )
            else:
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
        # 如果切换到预设位置，清除自定义位置
        self.custom_watermark_position = None
        self.on_watermark_change()
    
    def on_watermark_drag_start(self, event):
        """水印拖拽开始"""
        # 检查是否点击在水印区域
        if not self.image_processor.get_current_image():
            return
        
        self.watermark_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # 切换到自定义位置模式
        self.position.set('custom')
    
    def on_watermark_drag_motion(self, event):
        """水印拖拽移动"""
        if not self.watermark_dragging:
            return
        
        # 计算鼠标移动距离
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # 更新拖拽起始点
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # 计算水印在原图上的位置
        current_image = self.image_processor.get_current_image()
        if current_image:
            # 获取画布和图片的尺寸信息
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            img_width, img_height = current_image.size
            
            # 计算缩放比例
            scale_x = canvas_width / img_width if img_width > 0 else 1
            scale_y = canvas_height / img_height if img_height > 0 else 1
            scale = min(scale_x, scale_y, 1.0)
            
            # 计算显示的图片尺寸
            display_width = int(img_width * scale)
            display_height = int(img_height * scale)
            
            # 计算图片在画布上的偏移
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2
            
            # 将画布坐标转换为原图坐标
            if self.custom_watermark_position is None:
                # 首次拖拽，从当前位置开始
                image_x = int((event.x - offset_x) / scale) if scale > 0 else event.x
                image_y = int((event.y - offset_y) / scale) if scale > 0 else event.y
                self.custom_watermark_position = (image_x, image_y)
            else:
                # 继续拖拽，更新位置
                image_dx = int(dx / scale) if scale > 0 else dx
                image_dy = int(dy / scale) if scale > 0 else dy
                old_x, old_y = self.custom_watermark_position
                new_x = old_x + image_dx
                new_y = old_y + image_dy
                
                # 限制在图片范围内
                new_x = max(0, min(new_x, img_width))
                new_y = max(0, min(new_y, img_height))
                
                self.custom_watermark_position = (new_x, new_y)
            
            # 刷新预览
            self.refresh_preview()
    
    def on_watermark_drag_end(self, event):
        """水印拖拽结束"""
        self.watermark_dragging = False
    
    def on_format_change(self):
        """输出格式改变"""
        if self.output_format.get() == "JPEG":
            # 显示质量设置
            for widget in self.quality_frame.winfo_children():
                widget.pack()
        else:
            # 隐藏质量设置
            for widget in self.quality_frame.winfo_children():
                widget.pack_forget()
    
    def on_quality_change(self, event=None):
        """质量变化"""
        quality_value = int(self.quality.get())
        self.quality_label.config(text=str(quality_value))
    
    def on_resize_toggle(self):
        """尺寸调整开关"""
        if self.resize_enabled.get():
            # 显示尺寸调整选项
            for widget in self.resize_frame.winfo_children():
                widget.pack()
            # 更新为当前图片尺寸
            self.update_resize_values()
        else:
            # 隐藏尺寸调整选项
            for widget in self.resize_frame.winfo_children():
                widget.pack_forget()
    
    def on_resize_method_change(self):
        """调整方式改变"""
        pass  # 方法改变时无需特殊处理
    
    def update_resize_values(self):
        """更新尺寸值为当前图片尺寸"""
        current_image = self.image_processor.get_current_image()
        if current_image:
            width, height = current_image.size
            self.resize_width.set(width)
            self.resize_height.set(height)
            self.original_aspect_ratio = width / height if height > 0 else 1
    
    def on_width_change(self):
        """宽度改变时，如果保持比例则自动调整高度"""
        if self.keep_aspect_ratio.get() and hasattr(self, 'original_aspect_ratio'):
            try:
                new_width = self.resize_width.get()
                if new_width > 0:
                    new_height = int(new_width / self.original_aspect_ratio)
                    # 使用标志位防止递归
                    if not hasattr(self, '_updating_height') or not self._updating_height:
                        self._updating_height = True
                        self.resize_height.set(new_height)
                        self._updating_height = False
            except tk.TclError:
                pass  # 输入无效时忽略
    
    def on_height_change(self):
        """高度改变时，如果保持比例则自动调整宽度"""
        if self.keep_aspect_ratio.get() and hasattr(self, 'original_aspect_ratio'):
            try:
                new_height = self.resize_height.get()
                if new_height > 0:
                    new_width = int(new_height * self.original_aspect_ratio)
                    # 使用标志位防止递归
                    if not hasattr(self, '_updating_width') or not self._updating_width:
                        self._updating_width = True
                        self.resize_width.set(new_width)
                        self._updating_width = False
            except tk.TclError:
                pass  # 输入无效时忽略
    
    def choose_font_color(self):
        """选择字体颜色"""
        current_color = self.font_color.get()
        
        # 调用颜色选择器
        color = colorchooser.askcolor(color=current_color, title="选择字体颜色")
        
        # 处理返回的颜色值
        if color is None or (color[0] is None and color[1] is None):
            # 用户点击了取消
            return
        
        hex_color = None
        
        # 优先使用十六进制值（如果存在）
        if color[1]:
            hex_color = color[1].upper()
        # 否则使用RGB值转换
        elif color[0]:
            rgb_color = color[0]
            # 确保RGB值在0-255范围内并转换为整数
            r = max(0, min(255, int(round(rgb_color[0]))))
            g = max(0, min(255, int(round(rgb_color[1]))))
            b = max(0, min(255, int(round(rgb_color[2]))))
            hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
        
        # 更新颜色设置
        if hex_color:
            self.font_color.set(hex_color)
            # 更新颜色预览框和标签
            try:
                self.color_preview.config(bg=hex_color)
                self.color_label.config(text=hex_color)
            except tk.TclError:
                # 如果颜色格式错误，尝试修正
                if hex_color.startswith('#'):
                    self.color_preview.config(bg=hex_color)
                    self.color_label.config(text=hex_color)
            
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
    
    def save_template(self, watermark_type="text"):
        """保存模板"""
        if watermark_type == "text":
            template_name = self.new_template_name_text.get().strip()
            prefix = "文本_"
        else:
            template_name = self.new_template_name_image.get().strip()
            prefix = "图片_"
        
        if not template_name:
            messagebox.showerror("错误", "请输入新模板名称")
            return
        
        # 添加类型前缀
        full_template_name = prefix + template_name
        
        config = self.get_current_config()
        config['_watermark_type'] = watermark_type  # 标记模板类型
        
        if self.config_manager.save_template(full_template_name, config):
            messagebox.showinfo("成功", f"模板 '{template_name}' 保存成功")
            self.refresh_template_list(watermark_type)
            if watermark_type == "text":
                self.new_template_name_text.set("")
            else:
                self.new_template_name_image.set("")
        else:
            messagebox.showerror("错误", "保存模板失败")
    
    def load_template(self, watermark_type="text"):
        """加载模板"""
        if watermark_type == "text":
            template_name = self.template_name_text.get().strip()
            prefix = "文本_"
        else:
            template_name = self.template_name_image.get().strip()
            prefix = "图片_"
        
        if template_name == '暂无模板' or not template_name:
            return
        
        # 如果模板名没有前缀，添加前缀
        full_name = template_name if template_name.startswith(prefix) else prefix + template_name
        
        template = self.config_manager.load_template(full_name)
        if template:
            self.update_ui_from_config(template)
            self.on_watermark_change()
            messagebox.showinfo("成功", f"模板 '{template_name}' 加载成功")
        else:
            messagebox.showerror("错误", "加载模板失败")
    
    def delete_template(self, watermark_type="text"):
        """删除模板"""
        if watermark_type == "text":
            template_name = self.template_name_text.get().strip()
            prefix = "文本_"
        else:
            template_name = self.template_name_image.get().strip()
            prefix = "图片_"
        
        if not template_name or template_name == '暂无模板':
            messagebox.showerror("错误", "请选择要删除的模板")
            return
        
        # 如果模板名没有前缀，添加前缀
        full_name = template_name if template_name.startswith(prefix) else prefix + template_name
        
        if messagebox.askyesno("确认", f"确定要删除模板 '{template_name}' 吗？"):
            if self.config_manager.delete_template(full_name):
                messagebox.showinfo("成功", f"模板 '{template_name}' 删除成功")
                self.refresh_template_list(watermark_type)
                if watermark_type == "text":
                    self.template_name_text.set("")
                else:
                    self.template_name_image.set("")
            else:
                messagebox.showerror("错误", "删除模板失败")
    
    def refresh_template_list(self, watermark_type="text"):
        """刷新模板列表"""
        prefix = "文本_" if watermark_type == "text" else "图片_"
        all_templates = self.config_manager.list_templates()
        
        # 过滤出对应类型的模板
        templates = [t[len(prefix):] for t in all_templates if t.startswith(prefix)]
        
        if watermark_type == "text":
            combo = self.template_combo_text
        else:
            combo = self.template_combo_image
        
        if templates:
            combo['values'] = templates
        else:
            combo['values'] = ['暂无模板']
            combo.set('')
    
    def on_template_select(self, watermark_type="text"):
        """模板选择事件"""
        if watermark_type == "text":
            template_name = self.template_name_text.get().strip()
        else:
            template_name = self.template_name_image.get().strip()
        
        # 如果选择的是"暂无模板"提示，则忽略
        if template_name == '暂无模板' or not template_name:
            return
        
        # 自动加载模板
        self.load_template(watermark_type)
    
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
        
        # 检查是否导出到原文件夹
        if self._is_same_folder(output_folder):
            if not messagebox.askyesno("警告", "输出文件夹与原图片文件夹相同，可能会覆盖原图。是否继续？"):
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
                        # 应用水印（使用自定义位置）
                        if self.custom_watermark_position and self.position.get() == 'custom':
                            watermarked = self.watermark_manager.preview_watermark_with_position(
                                image_info['image'], 
                                self.custom_watermark_position
                            )
                        else:
                            watermarked = self.watermark_manager.preview_watermark(image_info['image'])
                        
                        # 调整图片尺寸
                        if self.resize_enabled.get():
                            watermarked = self._resize_image(watermarked)
                        
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
        
        # 检查是否导出到原文件夹
        current_info = self.image_processor.get_current_image_info()
        if current_info:
            output_path = Path(output_folder).resolve()
            image_path = Path(current_info['file_path']).parent.resolve()
            if output_path == image_path:
                if not messagebox.askyesno("警告", "输出文件夹与原图片文件夹相同，可能会覆盖原图。是否继续？"):
                    return
        
        try:
            # 更新水印配置
            config = self.get_current_config()
            self.watermark_manager.update_config(config)
            
            # 应用水印（使用自定义位置）
            if self.custom_watermark_position and self.position.get() == 'custom':
                watermarked = self.watermark_manager.preview_watermark_with_position(
                    current_image, 
                    self.custom_watermark_position
                )
            else:
                watermarked = self.watermark_manager.preview_watermark(current_image)
            
            # 调整图片尺寸
            if self.resize_enabled.get():
                watermarked = self._resize_image(watermarked)
            
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
    
    def _is_same_folder(self, output_folder):
        """检查输出文件夹是否与原图片文件夹相同"""
        images = self.image_processor.get_image_list()
        if not images:
            return False
        
        output_path = Path(output_folder).resolve()
        for image_info in images:
            image_path = Path(image_info['file_path']).parent.resolve()
            if output_path == image_path:
                return True
        return False
    
    def _resize_image(self, image):
        """调整图片尺寸"""
        if not self.resize_enabled.get():
            return image
        
        method = self.resize_method.get()
        
        if method == "percentage":
            percentage = self.resize_percentage.get()
            new_size = (int(image.width * percentage / 100), int(image.height * percentage / 100))
        elif method == "width_height":
            new_size = (self.resize_width.get(), self.resize_height.get())
        else:
            return image
        
        return image.resize(new_size, Image.Resampling.LANCZOS)
    
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