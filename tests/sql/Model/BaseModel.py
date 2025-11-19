from typing import Dict, Any, List, Optional, Type, Union, get_type_hints
from pydantic import BaseModel, Field
from datetime import datetime


class ForeignKeyField:
    """外键字段定义类"""
    
    def __init__(self, 
                    to: str, 
                    related_name: Optional[str] = None,
                    on_delete: str = "CASCADE",
                    on_update: str = "CASCADE"):
        """初始化外键字段
        
        Args:
            to: 目标模型名称，格式为 "ModelName" 或 "app.ModelName"
            related_name: 反向关系字段名
            on_delete: 删除策略
            on_update: 更新策略
        """
        self.to = to
        self.related_name = related_name
        self.on_delete = on_delete
        self.on_update = on_update


class RelationshipField:
    """关系字段定义类"""
    
    def __init__(self, 
                    to: str, 
                    relationship_type: str = "one_to_many",
                    back_populates: Optional[str] = None):
        """初始化关系字段
        
        Args:
            to: 目标模型名称
            relationship_type: 关系类型: one_to_one, one_to_many, many_to_many
            back_populates: 反向关系字段名
        """
        self.to = to
        self.relationship_type = relationship_type
        self.back_populates = back_populates


class RelationalModel(BaseModel):
    """支持关系的基础模型类"""
    
    # 类变量，用于定义外键和关系
    __foreign_keys__: Dict[str, ForeignKeyField] = {}
    __relationships__: Dict[str, RelationshipField] = {}
    __table_name__: Optional[str] = None
    
    def __init_subclass__(cls, **kwargs):
        """子类初始化时处理外键和关系定义"""
        super().__init_subclass__(**kwargs)
        
        # 初始化类变量
        if not hasattr(cls, '__foreign_keys__'):
            cls.__foreign_keys__ = {}
        if not hasattr(cls, '__relationships__'):
            cls.__relationships__ = {}
        
        # 从类型注解中提取外键和关系
        type_hints = get_type_hints(cls)
        
        for field_name, field_type in type_hints.items():
            # 检查是否是外键字段
            if hasattr(cls, field_name):
                field_value = getattr(cls, field_name)
                if isinstance(field_value, ForeignKeyField):
                    cls.__foreign_keys__[field_name] = field_value
            
            # 检查是否是关系字段
            if hasattr(cls, field_name):
                field_value = getattr(cls, field_name)
                if isinstance(field_value, RelationshipField):
                    cls.__relationships__[field_name] = field_value
    
    @classmethod
    def get_table_name(cls) -> str:
        """获取表名"""
        if cls.__table_name__:
            return cls.__table_name__
        
        # 默认使用类名的小写形式
        return cls.__name__.lower()
    
    @classmethod
    def get_foreign_keys(cls) -> Dict[str, ForeignKeyField]:
        """获取所有外键定义"""
        return cls.__foreign_keys__
    
    @classmethod
    def get_relationships(cls) -> Dict[str, RelationshipField]:
        """获取所有关系定义"""
        return cls.__relationships__
    
    @classmethod
    def get_foreign_key_columns(cls) -> List[str]:
        """获取所有外键列名"""
        return list(cls.__foreign_keys__.keys())
    
    @classmethod
    def get_relationship_fields(cls) -> List[str]:
        """获取所有关系字段名"""
        return list(cls.__relationships__.keys())
    
    def get_related_objects(self) -> Dict[str, Any]:
        """获取关联对象（如果已加载）"""
        related_objects = {}
        
        for field_name in self.get_relationship_fields():
            if hasattr(self, field_name):
                related_objects[field_name] = getattr(self, field_name)
        
        return related_objects
    
    def set_related_object(self, field_name: str, obj: Any) -> None:
        """设置关联对象"""
        if field_name in self.get_relationship_fields():
            setattr(self, field_name, obj)
    
    def to_dict_with_relations(self, exclude_relations: bool = False) -> Dict[str, Any]:
        """转换为字典，包含关联对象
        
        Args:
            exclude_relations: 是否排除关联对象
            
        Returns:
            包含关联对象的字典
        """
        data = self.model_dump()
        
        if not exclude_relations:
            for field_name, related_obj in self.get_related_objects().items():
                if related_obj is not None:
                    if isinstance(related_obj, list):
                        data[field_name] = [item.model_dump() if hasattr(item, 'model_dump') else item 
                                            for item in related_obj]
                    else:
                        data[field_name] = related_obj.model_dump() if hasattr(related_obj, 'model_dump') else related_obj
        
        return data


def ForeignKey(to: str, 
                related_name: Optional[str] = None,
                on_delete: str = "CASCADE",
                on_update: str = "CASCADE") -> Any:
    """定义外键字段的便捷函数
    
    Args:
        to: 目标模型名称
        related_name: 反向关系字段名
        on_delete: 删除策略
        on_update: 更新策略
        
    Returns:
        外键字段定义
    """
    return Field(
        default=None,
        description=f"外键，关联到 {to}",
        json_schema_extra={"foreign_key": to}
    )


def Relationship(to: str, 
                relationship_type: str = "one_to_many",
                back_populates: Optional[str] = None) -> Any:
    """定义关系字段的便捷函数
    
    Args:
        to: 目标模型名称
        relationship_type: 关系类型
        back_populates: 反向关系字段名
        
    Returns:
        关系字段定义
    """
    return Field(
        default=None,
        description=f"关系到 {to}",
        exclude=True,  # 排除在序列化之外
        json_schema_extra={"relationship": to, "type": relationship_type}
    )
