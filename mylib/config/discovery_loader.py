import json
import toml
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import fnmatch


from .base import ConfigDictWrapper


class DiscoveryLoader:
    """负责从 TOML/JSON 文件中自动发现并注册配置节"""
    
    def __init__(self, search_path: str, ignore_files: Optional[Set[str]] = None):
        self.search_path = search_path
        self.discovered_sections: Dict[str, Any] = {}
        self.loaded_files: List[str] = []
        self.ignore_files = ignore_files
        
    def discover(self) -> Dict[str, Any]:
        """自动发现并加载配置文件和配置节"""
        config_files = self._find_config_files()
        
        for file_path in config_files:
            self._load_config_file(file_path)
            
        return self.discovered_sections
    
    def _find_config_files(self) -> List[Path]:
        """查找配置文件"""
        config_files = []
        path = Path(self.search_path)
        
        if not path.exists():
            print(f"Warning: 搜索路径不存在: {path}")
            return config_files
            
        # 优先查找 toml 文件
        toml_files = list(path.glob("*.toml"))
        toml_files = [f for f in toml_files if not any(fnmatch.fnmatch(f.name, pattern) for pattern in self.ignore_files)]
        config_files.extend(toml_files)
        
        # 然后查找 json 文件
        json_files = list(path.glob("*.json"))
        config_files.extend(json_files)
        
        print(f"找到 {len(config_files)} 个配置文件: {[f.name for f in config_files]}")
        return config_files
    
    def _load_config_file(self, file_path: Path) -> None:
        """加载单个配置文件"""
        try:
            file_path_str = str(file_path)
            
            if file_path.suffix == '.toml':
                # 使用 with open 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                data = toml.loads(content)
                source_tag = f"toml:{file_path.name}"
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                source_tag = f"json:{file_path.name}"
            else:
                return
                
            self.loaded_files.append(file_path_str)
            self._process_config_data(data, source_tag)
            print(f"✅ 成功加载配置文件: {file_path.name}")
            
        except Exception as e:
            print(f"❌ 加载配置文件失败 {file_path}: {e}")
    
    def _process_config_data(self, data: Dict[str, Any], source_tag: str) -> None:
        """处理配置数据"""
        if not isinstance(data, dict):
            print(f"⚠️  配置文件数据不是字典格式: {source_tag}")
            return
            
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                # 包装配置节以便链式访问
                wrapper = ConfigDictWrapper(section_data, f"{source_tag}.{section_name}")
                self.discovered_sections[section_name] = {
                    'data': wrapper,
                    'source': source_tag,
                    'raw_data': section_data
                }
                print(f"  📦 发现配置节: {section_name}")
            else:
                print(f"  ⚠️  跳过非字典配置节: {section_name} (类型: {type(section_data).__name__})")
