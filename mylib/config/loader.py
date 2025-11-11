import os
import inspect
from typing import Optional, Any, Dict, Set

from .base import ConfigDictWrapper
from .summary import Summary
from .discovery_loader import DiscoveryLoader


class ConfigLoader:
    """
    配置加载器 - 自动发现模式
    自动扫描调用脚本所在目录的 TOML/JSON 配置文件
    """
    
    def __init__(self, 
                    config_path: Optional[str] = None,
                    search_subdirs: bool = False,
                    ignore_files: Optional[Set[str]] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 指定配置文件路径, 如为None则自动发现
            search_subdirs: 是否搜索子目录
        """
        self._search_subdirs = search_subdirs
        self._discovered_attrs: Dict[str, str] = {}
        self.ignore_files = ignore_files or {'pyproject.toml'}
        
        self.search_path = self._init_path(config_path)
        

        self._load_discovery()
        
        self.summary = Summary(self)
    
    def _get_caller_frame(self):
        """获取调用者帧"""
        stack = inspect.stack()
        for frame_info in stack[2:]:
            if 'config' not in frame_info.filename or 'loader.py' not in frame_info.filename:
                return frame_info
        return stack[2]
    
    def __getattr__(self, name: str) -> Any:
        """动态访问配置节"""
        if name in self._discovered_attrs:
            for section_info in self.discovery_loader.discovered_sections.values():
                if section_info['data']._path.split('.')[0] == name:
                    return section_info['data']
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """设置属性，记录发现的配置节"""
        super().__setattr__(name, value)
        
        if (not name.startswith('_') and 
            hasattr(self, '_discovered_attrs') and 
            name not in ['config_path', 'search_path', 'summary', 'discovery_loader'] and
            isinstance(value, ConfigDictWrapper)):
            source = getattr(value, '_path', 'unknown').split('.')[0]
            self._discovered_attrs[name] = source
    
    def _init_path(self, config_path: str):
        if config_path:
            if not os.path.isabs(config_path):
                caller_frame = self._get_caller_frame()
                caller_file = caller_frame.filename
                caller_dir = os.path.dirname(os.path.abspath(caller_file))
                resolved_path = os.path.abspath(os.path.join(caller_dir, config_path))
            else:
                resolved_path = config_path
            
            if os.path.isfile(resolved_path):
                self.config_path = resolved_path
                search_path = os.path.dirname(resolved_path)
            else:
                self.config_path = resolved_path
                search_path = resolved_path
        else:
            caller_frame = self._get_caller_frame()
            caller_file = caller_frame.filename
            search_path = os.path.dirname(os.path.abspath(caller_file))
            self.config_path = search_path
        return search_path

    def _load_discovery(self) -> None:
        """自动发现配置模式"""
        self.discovery_loader = DiscoveryLoader(self.search_path, self.ignore_files)
        discovered_data = self.discovery_loader.discover()
        
        for section_name, section_info in discovered_data.items():
            wrapper = section_info['data']
            setattr(self, section_name, wrapper)
    
    def get_discovered_attrs(self) -> Dict[str, str]:
        """获取所有发现的属性及其来源"""
        return self._discovered_attrs.copy()

    def show_config(self, simple: bool = False) -> None:
        """显示配置摘要
        
        Args:
            simple: 是否显示简化版摘要
        """
        if simple:
            self.summary.show_simple()
        else:
            self.summary.show()
    
    # ------------------- 全局单例模式 -------------------
    _global_instance: Optional["ConfigLoader"] = None

    @classmethod
    def init_global(cls, 
                    config_path: Optional[str] = None,
                    search_subdirs: bool = False) -> "ConfigLoader":
        """初始化全局实例"""
        if cls._global_instance is None:
            cls._global_instance = cls(config_path=config_path, search_subdirs=search_subdirs)
        return cls._global_instance

    @classmethod
    def get_global(cls) -> "ConfigLoader":
        """获取全局实例"""
        if cls._global_instance is None:
            raise RuntimeError("ConfigLoader 未初始化，请先调用 init_global()")
        return cls._global_instance
