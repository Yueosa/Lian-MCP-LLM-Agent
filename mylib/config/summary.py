from typing import TYPE_CHECKING
from mylib.utils import Printer

if TYPE_CHECKING:
    from .loader import ConfigLoader


class Summary:
    """配置摘要显示工具"""
    
    def __init__(self, parent: "ConfigLoader"):
        self.parent = parent
        self.printer = Printer()
    
    def show(self) -> None:
        """显示完整配置摘要"""
        self._show_header()
        self._show_discovery_summary()
        self._show_config_sections()
        self._show_loaded_files()
        self._show_usage_examples()
    
    def _show_header(self) -> None:
        """显示头部信息"""
        self.printer.cprint("cyan", "🔧 ConfigLoader 配置摘要")
        self.printer.cprint("magenta", f"📁 搜索路径: {self.parent.search_path}")
    
    def _show_discovery_summary(self) -> None:
        """显示自动发现摘要"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        self.printer.cprint("cyan", "\n🔍 自动发现配置节:")
        if discovered_attrs:
            for attr_name, source in discovered_attrs.items():
                self.printer.cprint("green", f"   ✅ {attr_name}")
                self.printer.cprint("blue", f"      ← 来源: {source}")
        else:
            self.printer.cprint("yellow", "   ⚠️  未发现任何配置节")
    
    def _show_config_sections(self) -> None:
        """显示配置节详情"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        if not discovered_attrs:
            return
            
        self.printer.cprint("cyan", "\n📋 配置节详情:")
        
        for attr_name in discovered_attrs.keys():
            section = getattr(self.parent, attr_name, None)
            if section and hasattr(section, 'to_dict'):
                section_data = section.to_dict()
                self.printer.cprint("magenta", f"   🗂️  {attr_name}:")
                
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:47] + "..."
                        self.printer.cprint("green", f"      {key}: {value_str}")
                else:
                    self.printer.cprint("green", f"      {section_data}")
    
    def _show_loaded_files(self) -> None:
        """显示加载的文件"""
        if hasattr(self.parent, 'discovery_loader'):
            loaded_files = self.parent.discovery_loader.loaded_files
            
            self.printer.cprint("cyan", "\n📄 加载的配置文件:")
            if loaded_files:
                for file_path in loaded_files:
                    self.printer.cprint("green", f"   ✅ {file_path}")
            else:
                self.printer.cprint("yellow", "   ⚠️  未加载任何配置文件")
    
    def _show_usage_examples(self) -> None:
        """显示使用示例"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        if discovered_attrs:
            self.printer.cprint("cyan", "\n💡 使用示例:")
            example_attr = list(discovered_attrs.keys())[0]
            section = getattr(self.parent, example_attr, None)
            
            if section and hasattr(section, 'to_dict'):
                section_data = section.to_dict()
                if isinstance(section_data, dict) and section_data:
                    example_key = list(section_data.keys())[0]
                    self.printer.cprint("blue", f"   # 访问配置:")
                    self.printer.cprint("green", f"   config.{example_attr}.{example_key}")
                    self.printer.cprint("green", f"   config.{example_attr}.get('{example_key}')")
                    self.printer.cprint("green", f"   config.{example_attr}.to_dict()")

    def show_simple(self) -> None:
        """显示简化版摘要"""
        discovered_attrs = self.parent.get_discovered_attrs()
        
        self.printer.cprint("cyan", "📋 配置摘要:")
        self.printer.cprint("magenta", f"搜索路径: {self.parent.search_path}")
        
        if discovered_attrs:
            self.printer.cprint("green", f"发现 {len(discovered_attrs)} 个配置节:")
            for attr_name in discovered_attrs.keys():
                self.printer.cprint("blue", f"  - {attr_name}")
        else:
            self.printer.cprint("yellow", "未发现配置节")
        
        if hasattr(self.parent, 'discovery_loader'):
            loaded_files = self.parent.discovery_loader.loaded_files
            if loaded_files:
                self.printer.cprint("green", f"加载 {len(loaded_files)} 个文件")
