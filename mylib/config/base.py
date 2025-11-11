from typing import Any


class ConfigDictWrapper:
    """
    配置字典包装器
    支持链式访问嵌套的字典和列表

    支持的方法:
        (1) get() <- dict
        (2) items() <- dict
        (3) keys() <- dict
        (4) values() <- dict
        (5) to_dict() -> dict
    """
    def __init__(self, data: Any, path: str = ""):
        self._data = data
        self._path = path

    def __getattr__(self, name: str) -> Any:
        """通过属性访问字典键"""
        if name == 'raw':
            return self._data
            
        if isinstance(self._data, dict) and name in self._data:
            value = self._data[name]
            new_path = f"{self._path}.{name}" if self._path else name
            return self._wrap_value(value, new_path)
            
        raise AttributeError(f"'{self._path}' has no attribute '{name}'")

    def __getitem__(self, key: Any) -> Any:
        """通过索引访问列表或字典"""
        if isinstance(self._data, (dict, list)):
            if (isinstance(self._data, dict) and key in self._data) or (isinstance(self._data, list) and 0 <= key < len(self._data)):
                value = self._data[key]
                new_path = f"{self._path}[{key}]"
                return self._wrap_value(value, new_path)
        raise KeyError(f"'{self._path}' has no key/index '{key}'")

    def __repr__(self) -> str:
        return f"ConfigDictWrapper({self._data})"

    def __str__(self) -> str:
        return str(self._data)

    def __len__(self) -> int:
        return len(self._data) if hasattr(self._data, '__len__') else 0

    def __iter__(self):
        """支持迭代操作"""
        if isinstance(self._data, list):
            for i, item in enumerate(self._data):
                yield self._wrap_value(item, f"{self._path}[{i}]")
        elif isinstance(self._data, dict):
            for key in self._data:
                yield self._wrap_value(self._data[key], f"{self._path}.{key}")
        else:
            raise TypeError(f"'{self._path}' is not iterable")

    def _wrap_value(self, value: Any, path: str) -> Any:
        """包装值，如果是字典或列表则返回包装器，否则直接返回值"""
        if isinstance(value, (dict, list)):
            return ConfigDictWrapper(value, path)
        return value

    def get(self, key: Any, default: Any = None) -> Any:
        """类似字典的 get 方法"""
        if isinstance(self._data, dict):
            value = self._data.get(key, default)
            if value is default:
                return default
            new_path = f"{self._path}.{key}" if self._path else key
            return self._wrap_value(value, new_path)
        return default

    def items(self):
        """类似字典的 items 方法"""
        if isinstance(self._data, dict):
            for k, v in self._data.items():
                yield k, self._wrap_value(v, f"{self._path}.{k}")
        else:
            raise TypeError(f"'{self._path}' is not a dictionary")

    def keys(self):
        """类似字典的 keys 方法"""
        if isinstance(self._data, dict):
            return self._data.keys()
        raise TypeError(f"'{self._path}' is not a dictionary")

    def values(self):
        """类似字典的 values 方法"""
        if isinstance(self._data, dict):
            for v in self._data.values():
                yield self._wrap_value(v, f"{self._path}[value]")
        else:
            raise TypeError(f"'{self._path}' is not a dictionary")

    def to_dict(self):
        """获取原始字典"""
        return self._data
