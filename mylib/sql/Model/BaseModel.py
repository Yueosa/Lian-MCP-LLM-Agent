"""
基础模型类 - 支持外键关系和关联对象加载

提供 RelationalModel 基类，支持定义外键和关系，
以及在 Python 端进行关联对象的管理和访问。
"""

from typing import Dict, Any, List, Optional, Type, Union, get_type_hints, get_args, get_origin
from pydantic import BaseModel, Field
from datetime import datetime


class ForeignKeyField:
    """外键字段定义类
    
    用于在模型中声明外键关系，提供 Python 端的外键约束信息。
    """
    
    def __init__(self, 
                    to: str, 
                    related_name: Optional[str] = None,
                    on_delete: str = "CASCADE",
                    on_update: str = "CASCADE"):
        """初始化外键字段
        
        Args:
            to: 目标模型名称，格式为 "ModelName" 或 "app.ModelName"
            related_name: 反向关系字段名
            on_delete: 删除策略 (CASCADE, SET NULL, RESTRICT, NO ACTION)
            on_update: 更新策略 (CASCADE, SET NULL, RESTRICT, NO ACTION)
        
        Example:
            task_id: int = ForeignKey("Task", related_name="task_steps")
        """
        self.to = to
        self.related_name = related_name
        self.on_delete = on_delete
        self.on_update = on_update


class RelationshipField:
    """关系字段定义类
    
    用于在模型中声明一对多、多对一等关系，支持延迟加载关联对象。
    """
    
    def __init__(self, 
                    to: str, 
                    relationship_type: str = "one_to_many",
                    back_populates: Optional[str] = None,
                    foreign_key: Optional[str] = None):
        """初始化关系字段
        
        Args:
            to: 目标模型名称
            relationship_type: 关系类型
                - "one_to_one": 一对一
                - "one_to_many": 一对多
                - "many_to_one": 多对一
                - "many_to_many": 多对多 (暂不支持)
            back_populates: 反向关系字段名
            foreign_key: 外键字段名 (对于 many_to_one 关系)
        
        Example:
            task_steps: Optional[List["TaskStep"]] = Relationship(
                "TaskStep", "one_to_many", back_populates="task"
            )
        """
        self.to = to
        self.relationship_type = relationship_type
        self.back_populates = back_populates
        self.foreign_key = foreign_key


class RelationalModel(BaseModel):
    """支持关系的基础模型类
    
    继承此类的模型可以:
    1. 定义外键字段 (使用 ForeignKey)
    2. 定义关系字段 (使用 Relationship)
    3. 访问关联对象
    4. 导出包含关联对象的字典
    """
    
    # 类变量，用于定义外键和关系
    __foreign_keys__: Dict[str, ForeignKeyField] = {}
    __relationships__: Dict[str, RelationshipField] = {}
    __table_name__: Optional[str] = None
    
    # 存储已加载的关联对象 (实例级别)
    _related_cache: Dict[str, Any] = {}
    
    def __init__(self, **data):
        """初始化模型实例"""
        super().__init__(**data)
        # 每个实例都有自己的关联对象缓存
        object.__setattr__(self, '_related_cache', {})
    
    def __init_subclass__(cls, **kwargs):
        """子类初始化时处理外键和关系定义"""
        super().__init_subclass__(**kwargs)
        
        # 初始化类变量 (继承父类的定义)
        if not hasattr(cls, '__foreign_keys__') or cls.__foreign_keys__ is RelationalModel.__foreign_keys__:
            cls.__foreign_keys__ = {}
        else:
            cls.__foreign_keys__ = cls.__foreign_keys__.copy()
            
        if not hasattr(cls, '__relationships__') or cls.__relationships__ is RelationalModel.__relationships__:
            cls.__relationships__ = {}
        else:
            cls.__relationships__ = cls.__relationships__.copy()
        
        # 从字段中提取外键和关系定义
        for field_name in dir(cls):
            if field_name.startswith('_'):
                continue
                
            try:
                field_value = getattr(cls, field_name)
                
                # 检查是否是外键字段
                if isinstance(field_value, ForeignKeyField):
                    cls.__foreign_keys__[field_name] = field_value
                
                # 检查是否是关系字段
                elif isinstance(field_value, RelationshipField):
                    cls.__relationships__[field_name] = field_value
            except AttributeError:
                pass
    
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
    def get_foreign_keys(cls) -> Dict[str, ForeignKeyField]:
        """获取所有外键定义
        
        Returns:
            外键字段名到 ForeignKeyField 的映射
        """
        return cls.__foreign_keys__.copy()
    
    @classmethod
    def get_relationships(cls) -> Dict[str, RelationshipField]:
        """获取所有关系定义
        
        Returns:
            关系字段名到 RelationshipField 的映射
        """
        return cls.__relationships__.copy()
    
    @classmethod
    def get_foreign_key_columns(cls) -> List[str]:
        """获取所有外键列名
        
        Returns:
            外键字段名列表
        """
        return list(cls.__foreign_keys__.keys())
    
    @classmethod
    def get_relationship_fields(cls) -> List[str]:
        """获取所有关系字段名
        
        Returns:
            关系字段名列表
        """
        return list(cls.__relationships__.keys())
    
    def get_related_object(self, field_name: str) -> Optional[Any]:
        """获取指定关联对象（如果已加载）
        
        Args:
            field_name: 关系字段名
            
        Returns:
            关联对象或 None
        """
        return self._related_cache.get(field_name)
    
    def get_related_objects(self) -> Dict[str, Any]:
        """获取所有已加载的关联对象
        
        Returns:
            关系字段名到关联对象的映射
        """
        return self._related_cache.copy()
    
    def set_related_object(self, field_name: str, obj: Any) -> None:
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
    
    def to_dict_with_relations(self, exclude_relations: bool = False, 
                                include_relations: Optional[List[str]] = None) -> Dict[str, Any]:
        """转换为字典，可选择包含关联对象
        
        Args:
            exclude_relations: 是否排除所有关联对象
            include_relations: 要包含的关系字段列表, None 表示包含所有已加载的关系
            
        Returns:
            包含或不包含关联对象的字典
        """
        data = self.model_dump()
        
        for field_name in self.get_relationship_fields():
            data.pop(field_name, None)
        
        if not exclude_relations:
            relations_to_include = include_relations if include_relations else list(self._related_cache.keys())
            
            for field_name in relations_to_include:
                if field_name in self._related_cache:
                    related_obj = self._related_cache[field_name]
                    
                    if related_obj is not None:
                        if isinstance(related_obj, list):
                            data[field_name] = [
                                item.to_dict_with_relations(exclude_relations=False) 
                                if isinstance(item, RelationalModel) 
                                else (item.model_dump() if hasattr(item, 'model_dump') else item)
                                for item in related_obj
                            ]
                        else:
                            if isinstance(related_obj, RelationalModel):
                                data[field_name] = related_obj.to_dict_with_relations(exclude_relations=False)
                            elif hasattr(related_obj, 'model_dump'):
                                data[field_name] = related_obj.model_dump()
                            else:
                                data[field_name] = related_obj
        
        return data
    
    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True


# 便捷函数，用于在模型定义中声明外键和关系
def ForeignKey(to: str, 
                related_name: Optional[str] = None,
                on_delete: str = "CASCADE",
                on_update: str = "CASCADE") -> ForeignKeyField:
    """创建外键字段定义
    
    Args:
        to: 目标模型名称
        related_name: 反向关系字段名
        on_delete: 删除策略
        on_update: 更新策略
        
    Returns:
        ForeignKeyField 实例
        
    Example:
        class TaskStep(RelationalModel):
            task_id: int = ForeignKey("Task", related_name="task_steps")
    """
    return ForeignKeyField(to, related_name, on_delete, on_update)


def Relationship(to: str, 
                    relationship_type: str = "one_to_many",
                    back_populates: Optional[str] = None,
                    foreign_key: Optional[str] = None) -> RelationshipField:
    """创建关系字段定义
    
    Args:
        to: 目标模型名称
        relationship_type: 关系类型
        back_populates: 反向关系字段名
        foreign_key: 外键字段名
        
    Returns:
        RelationshipField 实例
        
    Example:
        class Task(RelationalModel):
            task_steps: Optional[List["TaskStep"]] = Relationship(
                "TaskStep", "one_to_many", back_populates="task"
            )
    """
    return RelationshipField(to, relationship_type, back_populates, foreign_key)


__all__ = [
    'RelationalModel', 
    'ForeignKeyField', 
    'RelationshipField',
    'ForeignKey',
    'Relationship'
]
