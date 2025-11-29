from pathlib import Path
from typing import Optional
from mylib.config import ConfigLoader

def load_sql_config(config_path: Optional[str] = None):
    """加载 SQL 配置文件"""
    if config_path:
        return ConfigLoader(config_path=config_path)
    
    # 默认路径: 当前目录下的 sql_config.toml
    default_config = Path(__file__).parent / "sql_config.toml"
    return ConfigLoader(config_path=str(default_config))
