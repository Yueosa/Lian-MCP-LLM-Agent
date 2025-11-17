import importlib
import pkgutil
import inspect
from types import ModuleType
from typing import Dict, List, Tuple, Callable, Any
from ..base import ToolMetaData


class ToolsMetaLoader:
    """扫描 mylib.mcp.tools 包下的模块，提取 TOOL_METADATA 并构建可调用映射。

    Usage:
        loader = ToolsMetaLoader()
        loader.discover()
        tools = loader.tools_meta  # list of metadata dicts
        callables = loader.callables  # name -> bound callable
    """

    def __init__(self, package: str = "mylib.mcp.tools"):
        self.package = package
        # store ToolMetaData instances
        self.tools_meta: List[ToolMetaData] = []
        self.callables: Dict[str, Callable[..., Any]] = {}
        self._instances: Dict[Tuple[str, str], Any] = {}

    def _iter_package_modules(self) -> List[ModuleType]:
        pkg = importlib.import_module(self.package)
        modules = []
        for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            if name.startswith("__"):
                continue
            full_name = f"{self.package}.{name}"
            try:
                mod = importlib.import_module(full_name)
                modules.append(mod)
            except Exception:
                # 忽略无法导入的模块
                continue
        return modules

    def discover(self) -> List[Dict]:
        """发现所有模块的 TOOL_METADATA 并构建 callables 映射"""
        modules = self._iter_package_modules()
        metas = []
        for mod in modules:
            meta = getattr(mod, "TOOL_METADATA", None)
            if not meta:
                continue
            # meta 应该是列表
            for entry in meta:
                # minimal validation and normalization
                if "name" not in entry or ("module" not in entry and not entry.get("module")) or "method" not in entry:
                    continue

                # normalize legacy keys: 'class' -> 'class_name', 'async' -> 'async_method'
                if "class" in entry and "class_name" not in entry:
                    entry["class_name"] = entry["class"]
                if "async" in entry and "async_method" not in entry:
                    entry["async_method"] = entry["async"]

                try:
                    tm = ToolMetaData(
                        name=entry.get("name"),
                        description=entry.get("description"),
                        parameters=entry.get("parameters"),
                        module=entry.get("module"),
                        class_name=entry.get("class_name"),
                        method=entry.get("method"),
                        async_method=entry.get("async_method", False),
                    )
                    metas.append(tm)
                except Exception:
                    # 如果 metadata 不合法，跳过
                    continue
        self.tools_meta = metas
        self._build_callables()
        return self.tools_meta

    def _get_instance(self, module_name: str, class_name: str):
        key = (module_name, class_name)
        if key in self._instances:
            return self._instances[key]
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        inst = cls()
        self._instances[key] = inst
        return inst

    def _build_callables(self):
        call_map: Dict[str, Callable[..., Any]] = {}
        for meta in self.tools_meta:
            name = meta.name
            module_name = meta.module
            class_name = meta.class_name
            method_name = meta.method
            try:
                inst = self._get_instance(module_name, class_name)
                fn = getattr(inst, method_name)
                call_map[name] = fn
            except Exception:
                # 如果无法构造实例或绑定方法，跳过
                continue
        self.callables = call_map

    def get_tools_list(self) -> List[Dict]:
        """返回与旧接口兼容的工具描述列表（用于 /tools 列表端点）"""
        out = []
        for meta in self.tools_meta:
            m = {
                "name": meta.name,
                "description": meta.description or "",
                "parameters": meta.parameters or {"type": "object", "properties": {}}
            }
            out.append(m)
        return out
