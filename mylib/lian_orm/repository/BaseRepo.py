from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict, Generic, Type
from enum import Enum
from ..database.client import DatabaseClient
from ..mapper.converter import DataConverter
from ..models.core.BaseModel import RelationalModel
from ..models.core.Type import T
from ..schema.metadata import TableMeta


class BaseRepo(ABC, Generic[T]):
    """
    数据库仓库抽象类, 提供统一的CRUD操作接口

    子类需要实现: 
        - get_table_name(): 获取表名
        - 需设置的类变量: 
            - _model_class: 对应的数据模型类
            - _allowed_get_fields: 允许查询的字段列表
            - CREATE_TABLE_SQL: 创建表的SQL语句
    """

    _model_class: Optional[Type[T]] = None
    _allowed_get_fields = []
    CREATE_TABLE_SQL = None
    
    # 操作权限控制
    _can_create = True
    _can_read = True
    _can_update = True
    _can_delete = True

    def __init__(self, db_client: DatabaseClient, table_meta: Optional[TableMeta] = None):
        """
        初始化仓库

        Args:
            db_client: 数据库客户端实例
            table_meta: 表元数据
        """
        self.db = db_client
        self._table_meta = table_meta
        self._verify()

    def _verify(self) -> None:
        if self._model_class is None:
            raise ValueError(f"{self.__class__.__name__} 必须设置 _model_class 类变量")
        if not self._allowed_get_fields:
            raise ValueError(f"{self.__class__.__name__} 必须设置 _allowed_get_fields 类变量")

    def create(self, model_instance: T) -> T:
        """
        创建记录

        Args:
            model_instance: 数据模型实例

        Returns:
            创建后的模型实例 (包含生成的ID) 
        """
        if not self._can_create:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许创建操作")

        # 1. 导出数据
        data = model_instance.model_dump(exclude_unset=True, exclude_none=True)
        
        if hasattr(model_instance, 'id') and model_instance.id is not None:
            data.pop('id', None)
        
        for field in ['created_at', 'updated_at']:
            data.pop(field, None)

        # 2. 数据转换 (Python -> SQL)
        sql_data = DataConverter.python_to_sql(data, self._table_meta)

        if not sql_data:
            raise ValueError("没有可插入的数据")

        # 3. 构建 SQL
        fields = ', '.join(sql_data.keys())
        placeholders = ', '.join(['%s'] * len(sql_data))
        sql = f"INSERT INTO {self.get_table_name()} ({fields}) VALUES ({placeholders}) RETURNING id"

        # 4. 执行
        new_id = self.db.execute_returning(sql, list(sql_data.values()))
        
        if new_id:
            model_instance.id = new_id
            
        return model_instance

    def read(self, **kwargs) -> List[T]:
        """
        读取记录, 支持多字段查询

        Args:
            **kwargs: 查询条件, 支持_allowed_get_fields中的字段

        Returns:
            符合条件的模型实例列表
        """
        if not self._can_read:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许读取操作")

        invalid_fields = [field for field in kwargs.keys() if field not in self._allowed_get_fields]
        if invalid_fields:
            raise ValueError(f"无效的查询字段: {invalid_fields}, 允许的字段: {self._allowed_get_fields}")

        if kwargs:
            conditions = ' AND '.join([f"{field} = %s" for field in kwargs.keys()])
            sql = f"SELECT * FROM {self.get_table_name()} WHERE {conditions}"
            params = list(kwargs.values())
        else:
            sql = f"SELECT * FROM {self.get_table_name()}"
            params = []

        # 1. 执行查询
        results = self.db.fetch_all(sql, params)
        
        instances = []
        for row in results:
            # 2. 数据转换 (SQL -> Python)
            python_data = DataConverter.sql_to_python(row, self._table_meta)
            
            # 3. 实例化模型
            instance = self._model_class(**python_data)
            instances.append(instance)
        
        return instances

    def update(self, id: int, **kwargs) -> bool:
        """
        根据ID更新记录

        Args:
            id: 记录ID
            **kwargs: 要更新的字段和值

        Returns:
            更新是否成功
        """
        if not self._can_update:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许更新操作")

        invalid_fields = [field for field in kwargs.keys() if field not in self._allowed_get_fields]
        if invalid_fields:
            raise ValueError(f"无效的更新字段: {invalid_fields}, 允许的字段: {self._allowed_get_fields}")

        if 'id' in kwargs:
            raise ValueError("不能更新ID字段")

        if not kwargs:
            return True

        # 验证枚举值 (保留原有逻辑)
        for field, value in kwargs.items():
            field_type = getattr(self._model_class, '__annotations__', {}).get(field)
            if field_type is None:
                continue
            if isinstance(field_type, type) and issubclass(field_type, Enum):
                valid_values = [e.value for e in field_type]
                if isinstance(value, Enum):
                    value_to_check = value.value
                else:
                    value_to_check = value
                if value_to_check not in valid_values:
                    raise ValueError(
                        f"字段 '{field}' 的值 '{value}' 不合法, 可选值: {valid_values}"
                    )

        # 1. 数据转换 (Python -> SQL)
        sql_data = DataConverter.python_to_sql(kwargs, self._table_meta)

        # 2. 构建 SQL
        set_clause = ', '.join([f"{k} = %s" for k in sql_data.keys()])
        sql = f"UPDATE {self.get_table_name()} SET {set_clause} WHERE id = %s"

        # 3. 执行
        rowcount = self.db.execute(sql, list(sql_data.values()) + [id])
        return rowcount > 0

    def delete(self, id: int) -> bool:
        """
        根据ID删除记录

        Args:
            id: 记录ID

        Returns:
            删除是否成功
        """
        if not self._can_delete:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许删除操作")

        sql = f"DELETE FROM {self.get_table_name()} WHERE id = %s"

        rowcount = self.db.execute(sql, [id])
        return rowcount > 0

    def get_by_id(self, id: int) -> Optional[T]:
        """
        根据ID获取单条记录

        Args:
            id: 记录ID

        Returns:
            模型实例或None
        """
        results = self.read(id=id)
        return results[0] if results else None

    @abstractmethod
    def get_table_name(self) -> str:
        """
        获取数据库表名, 子类中实现

        Returns:
            表名字符串
        """
        pass

    def create_table(self):
        """
        创建数据库表
        """
        if self.CREATE_TABLE_SQL is None:
            raise ValueError(f"{self.__class__.__name__} 必须设置 CREATE_TABLE_SQL 类变量")

        self.db.execute(self.CREATE_TABLE_SQL)

    def has_field(self, field_name: str) -> bool:
        """
        检查表是否包含指定字段

        Args:
            field_name: 字段名

        Returns:
            bool: 是否包含该字段
        """
        return field_name in self._allowed_get_fields
    
    def read_with_relations(self, relations: Optional[List[str]] = None, **kwargs) -> List[T]:
        """
        读取记录并加载关联对象
        
        Args:
            relations: 要加载的关系列表，None表示加载所有关系
            **kwargs: 查询条件
            
        Returns:
            包含关联对象的模型实例列表
        """
        if not self._can_read:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许读取操作")
        
        # 首先获取基本记录
        instances = self.read(**kwargs)
        
        # 如果没有记录或模型不支持关系，直接返回
        if not instances or not issubclass(self._model_class, RelationalModel):
            return instances
        
        # 获取模型的关系定义
        model_relations = self._model_class.get_relationships()
        
        # 确定要加载的关系
        if relations is None:
            relations_to_load = list(model_relations.keys())
        else:
            relations_to_load = [rel for rel in relations if rel in model_relations]
        
        if not relations_to_load:
            return instances
        
        # 为每个关系加载关联对象
        for relation_name in relations_to_load:
            relation = model_relations[relation_name]
            
            # 根据关系类型加载关联对象
            if relation.relationship_type == "many_to_one":
                self._load_many_to_one_relations(instances, relation_name, relation)
            elif relation.relationship_type == "one_to_many":
                self._load_one_to_many_relations(instances, relation_name, relation)
            elif relation.relationship_type == "one_to_one":
                self._load_one_to_one_relations(instances, relation_name, relation)
        
        return instances
    
    def _load_many_to_one_relations(self, instances: List[T], relation_name: str, relation: Any) -> None:
        """加载多对一关系（例如: TaskStep.task）"""
        # 获取目标模型的 Repo
        target_repo = self._get_related_repo(relation.to)
        if not target_repo:
            return
        
        # 获取外键字段名
        foreign_key_field = relation.foreign_key
        if not foreign_key_field:
            foreign_key_field = f"{relation.to.lower()}_id"
        
        # 收集所有外键值
        foreign_key_values = set()
        for instance in instances:
            fk_value = getattr(instance, foreign_key_field, None)
            if fk_value is not None:
                foreign_key_values.add(fk_value)
        
        if not foreign_key_values:
            return
        
        # 批量查询关联对象
        related_objects = {}
        for fk_value in foreign_key_values:
            results = target_repo.read(id=fk_value)
            if results:
                related_objects[fk_value] = results[0]
        
        # 设置关联对象
        for instance in instances:
            fk_value = getattr(instance, foreign_key_field, None)
            if fk_value in related_objects:
                instance.set_related_object(relation_name, related_objects[fk_value])
    
    def _load_one_to_many_relations(self, instances: List[T], relation_name: str, relation: Any) -> None:
        """加载一对多关系（例如: Task.task_steps）"""
        # 获取目标模型的 Repo
        target_repo = self._get_related_repo(relation.to)
        if not target_repo:
            return
        
        # 推断外键字段名（在目标表中）
        source_table_name = self.get_table_name().rstrip('s')
        foreign_key_field = f"{source_table_name}_id"
        
        if not target_repo.has_field(foreign_key_field):
            return
        
        primary_key_values = [instance.id for instance in instances if hasattr(instance, 'id')]
        
        if not primary_key_values:
            return
        
        all_related_objects = []
        for pk_value in primary_key_values:
            results = target_repo.read(**{foreign_key_field: pk_value})
            all_related_objects.extend([(pk_value, obj) for obj in results])
        
        related_objects_map = {}
        for pk_value, obj in all_related_objects:
            if pk_value not in related_objects_map:
                related_objects_map[pk_value] = []
            related_objects_map[pk_value].append(obj)
        
        for instance in instances:
            if hasattr(instance, 'id'):
                related_list = related_objects_map.get(instance.id, [])
                instance.set_related_object(relation_name, related_list)
    
    def _load_one_to_one_relations(self, instances: List[T], relation_name: str, relation: Any) -> None:
        """加载一对一关系"""
        self._load_many_to_one_relations(instances, relation_name, relation)
    
    def _get_related_repo(self, model_name: str) -> Optional['BaseRepo']:
        """获取关联模型的 Repo 实例"""
        try:
            from . import MemoryLogRepo, TasksRepo, TaskStepsRepo, ToolCallsRepo
            
            repo_map = {
                'MemoryLog': MemoryLogRepo,
                'Task': TasksRepo,
                'TaskStep': TaskStepsRepo,
                'ToolCall': ToolCallsRepo,
            }
            
            repo_class = repo_map.get(model_name)
            if repo_class:
                return repo_class(self.db)
        except ImportError:
            pass
        
        return None
    
    def join_query(self, 
                    join_table: str,
                    join_condition: str,
                    select_fields: Optional[List[str]] = None,
                    join_type: str = "INNER",
                   **where_conditions) -> List[Dict[str, Any]]:
        """执行 JOIN 查询"""
        if not self._can_read:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许读取操作")
        
        if select_fields:
            select_clause = ", ".join(select_fields)
        else:
            select_clause = f"{self.get_table_name()}.*, {join_table}.*"
        
        sql = f"SELECT {select_clause} FROM {self.get_table_name()} "
        sql += f"{join_type} JOIN {join_table} ON {join_condition}"
        
        if where_conditions:
            where_parts = []
            params = []
            for field, value in where_conditions.items():
                where_parts.append(f"{field} = %s")
                params.append(value)
            sql += " WHERE " + " AND ".join(where_parts)
        else:
            params = []
        
        return self.db.fetch_all(sql, params)
