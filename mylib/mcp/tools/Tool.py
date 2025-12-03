"""
Tool - MCP 工具加载器

负责发现、加载和管理所有工具，提供统一的工具查询和调用接口。
"""

import importlib
import pkgutil
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToolMetaData:
    """工具元数据"""
    name: str
    description: str
    parameters: Dict[str, Any]
    module: str
    class_name: str
    method: str
    async_method: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "module": self.module,
            "class_name": self.class_name,
            "method": self.method,
            "async_method": self.async_method
        }


class ToolLoader:
    """
    MCP 工具加载器
    
    扫描 mylib.mcp.tools 包下的子模块，提取 TOOL_METADATA 并构建可调用映射。
    
    Usage:
        loader = ToolLoader()
        loader.discover()
        
        # 获取所有工具列表
        tools = loader.get_tools_list()
        
        # 获取单个工具元数据
        meta = loader.get_tool_meta("file_read")
        
        # 调用工具
        result = await loader.call("file_read", file_path="/path/to/file")
    """
    
    _instance: Optional["ToolLoader"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, package: str = "mylib.mcp.tools"):
        if self._initialized:
            return
        
        self.package = package
        self.tools_meta: List[ToolMetaData] = []
        self.callables: Dict[str, Callable[..., Any]] = {}
        self._instances: Dict[Tuple[str, str], Any] = {}
        self._initialized = True
    
    def _iter_package_modules(self):
        """遍历包内所有子模块"""
        pkg = importlib.import_module(self.package)
        modules = []
        
        for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            if name.startswith("__") or name == "Tool":
                continue
            
            full_name = f"{self.package}.{name}"
            
            try:
                if ispkg:
                    # 对于子包，尝试导入其 __init__
                    mod = importlib.import_module(full_name)
                    modules.append(mod)
                else:
                    # 对于单文件模块
                    mod = importlib.import_module(full_name)
                    modules.append(mod)
            except Exception as e:
                print(f"[ToolLoader] 无法导入模块 {full_name}: {e}")
                continue
        
        return modules
    
    def discover(self) -> List[ToolMetaData]:
        """
        发现所有工具的元数据并构建 callables 映射
        
        Returns:
            工具元数据列表
        """
        modules = self._iter_package_modules()
        metas = []
        
        for mod in modules:
            meta_list = getattr(mod, "TOOL_METADATA", None)
            if not meta_list:
                continue
            
            for entry in meta_list:
                # 验证必需字段
                required_fields = ["name", "module", "method", "class_name"]
                if not all(entry.get(f) for f in required_fields):
                    continue
                
                try:
                    tm = ToolMetaData(
                        name=entry.get("name"),
                        description=entry.get("description", ""),
                        parameters=entry.get("parameters", {"type": "object", "properties": {}}),
                        module=entry.get("module"),
                        class_name=entry.get("class_name"),
                        method=entry.get("method"),
                        async_method=entry.get("async_method", False)
                    )
                    metas.append(tm)
                except Exception as e:
                    print(f"[ToolLoader] 解析工具元数据失败: {e}")
                    continue
        
        self.tools_meta = metas
        self._build_callables()
        return self.tools_meta
    
    def _get_instance(self, module_name: str, class_name: str):
        """获取或创建工具类实例"""
        key = (module_name, class_name)
        if key in self._instances:
            return self._instances[key]
        
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        inst = cls()
        self._instances[key] = inst
        return inst
    
    def _build_callables(self):
        """构建工具名到可调用方法的映射"""
        call_map: Dict[str, Callable[..., Any]] = {}
        
        for meta in self.tools_meta:
            try:
                inst = self._get_instance(meta.module, meta.class_name)
                fn = getattr(inst, meta.method)
                call_map[meta.name] = fn
            except Exception as e:
                print(f"[ToolLoader] 无法绑定工具 {meta.name}: {e}")
                continue
        
        self.callables = call_map
    
    def get_tools_list(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的简要描述列表（供 API 端点使用）
        
        Returns:
            [{"name": str, "description": str, "parameters": dict}, ...]
        """
        return [
            {
                "name": meta.name,
                "description": meta.description,
                "parameters": meta.parameters
            }
            for meta in self.tools_meta
        ]
    
    def get_tool_meta(self, name: str) -> Optional[ToolMetaData]:
        """
        获取指定工具的完整元数据
        
        Args:
            name: 工具名称
            
        Returns:
            ToolMetaData 或 None
        """
        for meta in self.tools_meta:
            if meta.name == name:
                return meta
        return None
    
    def get_tool_callable(self, name: str) -> Optional[Callable]:
        """
        获取指定工具的可调用方法
        
        Args:
            name: 工具名称
            
        Returns:
            可调用方法或 None
        """
        return self.callables.get(name)
    
    async def call(self, name: str, **kwargs) -> Any:
        """
        调用指定工具
        
        Args:
            name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 工具不存在
            Exception: 工具执行错误
        """
        fn = self.callables.get(name)
        if fn is None:
            raise ValueError(f"工具不存在: {name}")
        
        meta = self.get_tool_meta(name)
        if meta and meta.async_method:
            return await fn(**kwargs)
        else:
            return fn(**kwargs)
    
    def reload(self):
        """重新加载所有工具"""
        self.tools_meta = []
        self.callables = {}
        self._instances = {}
        self.discover()


# 便捷函数
_loader: Optional[ToolLoader] = None

def get_tool_loader() -> ToolLoader:
    """获取工具加载器单例"""
    global _loader
    if _loader is None:
        _loader = ToolLoader()
        _loader.discover()
    return _loader


def get_tools_list() -> List[Dict[str, Any]]:
    """获取所有工具列表"""
    return get_tool_loader().get_tools_list()


def get_tool_meta(name: str) -> Optional[Dict[str, Any]]:
    """获取指定工具的元数据"""
    meta = get_tool_loader().get_tool_meta(name)
    return meta.to_dict() if meta else None


async def call_tool(name: str, **kwargs) -> Any:
    """调用指定工具"""
    return await get_tool_loader().call(name, **kwargs)
