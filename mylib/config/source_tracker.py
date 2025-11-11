from typing import List, Dict


class SourceTracker:
    """统一管理配置属性的来源追踪"""
    def __init__(self):
        self.map: Dict[str, str] = {}
        self.discovered_attrs: List[str] = []

    def record(self, name: str, source: str) -> None:
        """记录属性来源"""
        self.map[name] = source
        if source.startswith("discovery"):
            self.discovered_attrs.append(name)

    def summary(self) -> None:
        """打印所有追踪信息"""
        print("[SourceTracker] 属性来源追踪:")
        for k, v in self.map.items():
            print(f"  - {k}: {v}")
        if self.discovered_attrs:
            print(f"  [自动发现] {', '.join(self.discovered_attrs)}")
