"""
配置管理模块
处理水印模板的保存、加载和用户设置的持久化存储
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件夹路径
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.templates_file = self.config_dir / "templates.json"
        self.settings_file = self.config_dir / "settings.json"
        
        # 默认设置
        self.default_settings = {
            "last_watermark_template": None,
            "last_output_folder": "",
            "last_input_folder": "",
            "default_watermark": {
                "type": "text",
                "text": "Watermark",
                "font_family": "Arial",
                "font_size": 24,
                "font_color": "#FFFFFF",
                "opacity": 80,
                "position": "bottom_right",
                "rotation": 0,
                "image_path": "",
                "image_scale": 1.0
            }
        }
        
        # 加载设置
        self.settings = self.load_settings()
        self.templates = self.load_templates()
    
    def load_settings(self) -> Dict[str, Any]:
        """加载用户设置"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 合并默认设置，确保所有必要的键都存在
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)
                return merged_settings
            except (json.JSONDecodeError, IOError):
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """保存用户设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def load_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载水印模板"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_templates(self) -> bool:
        """保存水印模板"""
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """设置值"""
        self.settings[key] = value
    
    def save_template(self, name: str, template: Dict[str, Any]) -> bool:
        """
        保存水印模板
        
        Args:
            name: 模板名称
            template: 模板数据
            
        Returns:
            bool: 保存是否成功
        """
        self.templates[name] = template
        return self.save_templates()
    
    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        加载水印模板
        
        Args:
            name: 模板名称
            
        Returns:
            Dict: 模板数据，如果不存在返回None
        """
        return self.templates.get(name)
    
    def delete_template(self, name: str) -> bool:
        """
        删除水印模板
        
        Args:
            name: 模板名称
            
        Returns:
            bool: 删除是否成功
        """
        if name in self.templates:
            del self.templates[name]
            return self.save_templates()
        return False
    
    def list_templates(self) -> List[str]:
        """
        获取所有模板名称列表
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self.templates.keys())
    
    def get_default_watermark_config(self) -> Dict[str, Any]:
        """获取默认水印配置"""
        return self.settings.get("default_watermark", self.default_settings["default_watermark"]).copy()
    
    def update_default_watermark_config(self, config: Dict[str, Any]) -> None:
        """更新默认水印配置"""
        self.settings["default_watermark"] = config.copy()
    
    def export_template(self, name: str, file_path: str) -> bool:
        """
        导出模板到文件
        
        Args:
            name: 模板名称
            file_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        if name not in self.templates:
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({name: self.templates[name]}, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def import_template(self, file_path: str) -> bool:
        """
        从文件导入模板
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            bool: 导入是否成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_templates = json.load(f)
            
            # 合并导入的模板
            for name, template in imported_templates.items():
                self.templates[name] = template
            
            return self.save_templates()
        except (json.JSONDecodeError, IOError):
            return False
    
    def cleanup(self) -> None:
        """清理资源，保存所有数据"""
        self.save_settings()
        self.save_templates()
