import json
import toml
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import fnmatch

from .base import ConfigDictWrapper

from mylib.kit import Loutput


class DiscoveryLoader:
    """负责从 TOML/JSON 文件中自动发现并注册配置节"""
    
    def __init__(self, search_path: str, ignore_files: Optional[Set[str]] = None):
        self.search_path = search_path
        self.discovered_sections: Dict[str, Any] = {}
        self.loaded_files: List[str] = []
        self.ignore_files = ignore_files
        self.is_single_file_mode = False

        self.lo = Loutput()
        
    def discover(self) -> Dict[str, Any]:
        """自动发现并加载配置文件和配置节"""
        path = Path(self.search_path)
        if path.is_file():
            self.is_single_file_mode = True
            config_files = [path]
            self.lo.lput(f"📄 单文件模式: 加载 {path.name}", font_color="cyan")
        else:
            config_files = self._find_config_files()
        
        for file_path in config_files:
            self._load_config_file(file_path)
            
        return self.discovered_sections
    
    def _find_config_files(self) -> List[Path]:
        """查找配置文件"""
        config_files = []
        path = Path(self.search_path)
        
        if not path.exists():
            self.lo.lput(f"⚠️  警告: 搜索路径不存在: {path}", font_color="yellow")
            return config_files
        
        if not path.is_dir():
            self.lo.lput(f"⚠️  警告: 路径不是目录: {path}", font_color="yellow")
            return config_files
            
        toml_files = list(path.glob("*.toml"))
        toml_files = [f for f in toml_files if not any(fnmatch.fnmatch(f.name, pattern) for pattern in self.ignore_files)]
        config_files.extend(toml_files)
        
        json_files = list(path.glob("*.json"))
        config_files.extend(json_files)
        
        self.lo.lput(f"🔍 找到 {len(config_files)} 个配置文件: {[f.name for f in config_files]}", font_color="cyan")
        return config_files
    
    def _load_config_file(self, file_path: Path) -> None:
        """加载单个配置文件"""
        try:
            file_path_str = str(file_path)
            
            if file_path.suffix == '.toml':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                data = toml.loads(content)
                source_tag = f"toml:{file_path_str}"
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                source_tag = f"json:{file_path_str}"
            else:
                return
                
            self.loaded_files.append(file_path_str)
            self.lo.lput(f"✅ 配置文件加载完成:", )
            self.lo.lput(f"{file_path}", font_color="red")
            self._process_config_data(data, source_tag)
            
        except Exception as e:
            self.lo.lput(f"✅ 配置文件加载失败:", )
            self.lo.lput(f"{file_path}", font_color="red")
            self.lo.lput(e, font_color="yellow")
    
    def _process_config_data(self, data: Dict[str, Any], source_tag: str) -> None:
        """处理配置数据"""
        if not isinstance(data, dict):
            self.lo.lput(f"⚠️  配置文件数据不是字典格式: {source_tag}", font_color="black")
            return
            
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                wrapper = ConfigDictWrapper(section_data, f"{source_tag}.{section_name}")
                self.discovered_sections[section_name] = {
                    'data': wrapper,
                    'source': source_tag,
                    'raw_data': section_data
                }
                self.lo.lput(f"  📦 发现配置节: {section_name}", font_color="blue")
            else:
                self.lo.lput(f"  ⚠️  跳过非字典配置节: {section_name} (类型: {type(section_data).__name__})", font_color="magenta")
