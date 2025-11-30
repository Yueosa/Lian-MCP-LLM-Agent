from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .loader import ConfigLoader

from mylib.kit import Loutput


class Summary:
    """配置摘要显示工具"""
    
    def __init__(self, parent: "ConfigLoader"):
        self.parent = parent
        self.lo = Loutput()
    
    def show(self) -> None:
        """显示完整配置摘要"""
        self._show_header()
        self._show_discovery_summary()
        self._show_config_sections()
        self._show_loaded_files()
        self._show_usage_examples()
    
    def _show_header(self) -> None:
        """显示头部信息"""
        self.lo.lput("\n🔧 ConfigLoader 配置摘要", font_color="cyan")
        self.lo.lput(f"📁 搜索路径: {self.parent.search_path}", font_color="magenta")
    
    def _show_discovery_summary(self) -> None:
        """显示自动发现摘要"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        self.lo.lput("\n🔍 自动发现配置节:", font_color="cyan")
        if discovered_attrs:
            for attr_name, source in discovered_attrs.items():
                self.lo.lput(f"   ✅ {attr_name}", font_color="green")
                self.lo.lput(f"      ← 来源: {source}", font_color="blue")
        else:
            self.lo.lput("   ⚠️  未发现任何配置节", font_color="yellow")
    
    def _show_config_sections(self) -> None:
        """显示配置节详情"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        if not discovered_attrs:
            return
            
        self.lo.lput("\n📋 配置节详情:", font_color="cyan")
        
        for attr_name in discovered_attrs.keys():
            section = getattr(self.parent, attr_name, None)
            if section and hasattr(section, 'to_dict'):
                section_data = section.to_dict()
                self.lo.lput(f"   🗂️  {attr_name}:", font_color="magenta")
                
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:47] + "..."
                        self.lo.lput(f"      {key}: {value_str}", font_color="green")
                else:
                    self.lo.lput(f"      {section_data}", font_color="green")
    
    def _show_loaded_files(self) -> None:
        """显示加载的文件"""
        if hasattr(self.parent, 'discovery_loader'):
            loaded_files = self.parent.discovery_loader.loaded_files
            
            self.lo.lput("\n📄 加载的配置文件:", font_color="cyan")
            if loaded_files:
                for file_path in loaded_files:
                    self.lo.lput(f"   ✅ {file_path}", font_color="green")
            else:
                self.lo.lput("   ⚠️  未加载任何配置文件", font_color="yellow")
    
    def _show_usage_examples(self) -> None:
        """显示使用示例"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        if discovered_attrs:
            self.lo.lput("\n💡 使用示例:", font_color="cyan")
            example_attr = list(discovered_attrs.keys())[0]
            section = getattr(self.parent, example_attr, None)
            
            if section and hasattr(section, 'to_dict'):
                section_data = section.to_dict()
                if isinstance(section_data, dict) and section_data:
                    example_key = list(section_data.keys())[0]
                    self.lo.lput(f"   # 访问配置:", font_color="blue")
                    self.lo.lput(f"   config.{example_attr}.{example_key}", font_color="green")
                    self.lo.lput(f"   config.{example_attr}.get('{example_key}')", font_color="green")
                    self.lo.lput(f"   config.{example_attr}.to_dict()", font_color="green")

    def show_simple(self) -> None:
        """显示简化版摘要"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        self.lo.lput("📋 配置摘要:", font_color="cyan")
        self.lo.lput(f"搜索路径: {self.parent.search_path}", font_color="magenta")
        
        if discovered_attrs:
            self.lo.lput(f"发现 {len(discovered_attrs)} 个配置节:", font_color="green")
            for attr_name in discovered_attrs.keys():
                self.lo.lput(f"  - {attr_name}", font_color="blue")
        else:
            self.lo.lput("未发现配置节", font_color="yellow")
        
        if hasattr(self.parent, 'discovery_loader'):
            loaded_files = self.parent.discovery_loader.loaded_files
            if loaded_files:
                self.lo.lput(f"加载 {len(loaded_files)} 个文件", font_color="green")
