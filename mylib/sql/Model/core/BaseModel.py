"""
基础模型类 - 支持外键关系和关联对象加载

提供 RelationalModel 基类，支持定义外键和关系，
以及在 Python 端进行关联对象的管理和访问。
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from .Enum import relationship, on_update, on_delete
from .Type import RelatedData


class RelationshipField:
    """关系字段定义类
    
    用于在模型中声明一对多、多对一等关系，支持延迟加载关联对象。
    """
    
    def __init__(self, 
                    to: str, 
                    relationship_type: relationship = relationship.one_to_many,
                    back_populates: Optional[str] = None,
                    foreign_key: Optional[str] = None,
                    on_update: on_delete = on_update.CASCADE,
                    on_delete: on_delete = on_delete.CASCADE):
        """初始化关系字段
        
        Args:
            to: 目标模型名称
            relationship_type: 关系类型
                - "one_to_one": 一对一
                - "one_to_many": 一对多
                - "many_to_one": 多对一
            back_populates: 反向关系字段名
            foreign_key: 外键字段名 (对于 many_to_one 关系)
        
        Example:
            Task 模型里:
            task_step = RelationshipField(
                "TaskStep", "one_to_many", back_populates="task"
            )
            TaskStep 模型里:
            task = RelationshipField(
                "Task", "many_to_one", back_populates="task_step", foreign_key="task_id"
            )
        """
        self.to = to
        self.relationship_type = relationship_type
        self.back_populates = back_populates
        self.foreign_key = foreign_key
        self.on_update = on_update
        self.on_delete = on_delete


class RelationalModel(BaseModel):
    """支持关系的基础模型类
    
    继承此类的模型可以:
    1. 定义外键字段 (使用 ForeignKey)
    2. 定义关系字段 (使用 Relationship)
    3. 访问关联对象
    4. 导出包含关联对象的字典
    """
    
    # 类变量，用于定义外键和关系
    __relationships__: Dict[str, RelationshipField] = {}
    __table_name__: Optional[str] = None
    
    # 存储已加载的关联对象 (实例级别)
    _related_cache: Dict[str, RelatedData] = {}
    
    def __init__(self, **data):
        """初始化模型实例"""
        super().__init__(**data)
        object.__setattr__(self, '_related_cache', {})
    
    def __init_subclass__(cls, **kwargs):
        """子类初始化时处理外键和关系定义"""
        super().__init_subclass__(**kwargs)
        
        if not hasattr(cls, '__relationships__') or cls.__relationships__ is RelationalModel.__relationships__:
            cls.__relationships__ = {}
        else:
            cls.__relationships__ = cls.__relationships__.copy()
        
        """
        旧处理方法是使用 dir() 和 getattr() 方法实现
            dir() 可能会获取到多余的信息
            getattr() 会触发对象的 __get__() 方法, 容易产生副作用
        """
        # for field_name in dir(cls):
        #     if field_name.startswith('_'):
        #         continue
        #         
        #     try:
        #         field_value = getattr(cls, field_name)
        #         
        #         if isinstance(field_value, ForeignKeyField):
        #             cls.__foreign_keys__[field_name] = field_value
        #         
        #         elif isinstance(field_value, RelationshipField):
        #             cls.__relationships__[field_name] = field_value
        #     except AttributeError:
        #         pass
        annotations = cls.__dict__.get('__annotations__', {})

        for name in annotations:
            value = cls.__dict__.get(name, None)

            if isinstance(value, RelationshipField):
                cls.__relationships__[name] = value
    
    @classmethod
    def _extract_relationships_from_fields(cls):
        """从 Pydantic Field 的 description 中提取 Relationship 定义"""
        if hasattr(cls, 'model_fields'):
            for field_name, field_info in cls.model_fields.items():
                if hasattr(field_info, 'description') and isinstance(field_info.description, RelationshipField):
                    cls.__relationships__[field_name] = field_info.description
    
    @classmethod
    def get_table_name(cls) -> str:
        """获取表名
        
        Returns:
            表名字符串
        """
        if cls.__table_name__:
            return cls.__table_name__
        
        # 默认使用类名的小写形式
        return cls.__name__.lower()
    
    @classmethod
    def get_relationships(cls) -> Dict[str, RelationshipField]:
        """获取所有关系定义
        
        Returns:
            关系字段名到 RelationshipField 的映射
        """
        return cls.__relationships__.copy()
    
    @classmethod
    def get_relationship_fields(cls) -> List[str]:
        """获取所有关系字段名
        
        Returns:
            关系字段名列表
        """
        return list(cls.__relationships__.keys())
    
    def get_related_object(self, field_name: str) -> RelatedData:
        """获取指定关联对象（如果已加载）
        
        Args:
            field_name: 关系字段名
            
        Returns:
            关联对象或 None
        """
        return self._related_cache.get(field_name)
    
    def get_related_objects(self) -> Dict[str, RelatedData]:
        """获取所有已加载的关联对象
        
        Returns:
            关系字段名到关联对象的映射
        """
        return self._related_cache.copy()
    
    def set_related_object(self, field_name: str, obj: RelatedData) -> None:
        """设置关联对象
        
        Args:
            field_name: 关系字段名
            obj: 关联对象（单个对象或列表）
            
        Raises:
            ValueError: 如果字段名不是有效的关系字段
        """
        if field_name not in self.get_relationship_fields():
            raise ValueError(f"'{field_name}' 不是有效的关系字段")
        
        self._related_cache[field_name] = obj
    
    def clear_related_objects(self) -> None:
        """清除所有已加载的关联对象"""
        self._related_cache.clear()
    
    def has_related_object(self, field_name: str) -> bool:
        """检查是否已加载指定的关联对象
        
        Args:
            field_name: 关系字段名
            
        Returns:
            是否已加载
        """
        return field_name in self._related_cache
    
    @staticmethod
    def _truncate(value: Any, length: int = 30) -> str:
        """辅助方法：截断过长的字段内容用于显示
        
        Args:
            value: 要显示的字段值
            length: 截断长度，默认 30
            
        Returns:
            截断后的字符串
        """
        if value is None:
            return "None"
        
        s = str(value)
        if len(s) > length:
            return s[:length] + "..."
        return s
    
    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True


__all__ = [
    'RelationalModel', 
    'RelationshipField',
]
