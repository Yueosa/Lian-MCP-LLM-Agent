import importlib
import inspect
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

from mylib.config import ConfigLoader
from .Repo.DBPool import PostgreSQLConnectionPool
from .Sql.SqlLoader import get_sql_loader


class Sql:
    """ORM 抽象层的顶层接口类
    
    提供数据库连接和动态的表操作方法，支持通过 Create_{表名}, Read_{表名}, Update_{表名}, Delete_{表名} 进行操作。
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                    dbname: Optional[str] = None, user: Optional[str] = None, 
                    passwd: Optional[str] = None, config_path: Optional[str] = None):
        """初始化数据库连接
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            dbname: 数据库名称
            user: 数据库用户名
            passwd: 数据库密码
            config_path: 配置文件路径
        """
        if config_path:
            self.cfg = ConfigLoader(config_path=config_path)
        else:
            default_config = Path(__file__).parent / "config" / "sql_config.toml"
            self.cfg = ConfigLoader(config_path=str(default_config))
        
        self.host = host or getattr(self.cfg.Postgresql, 'host', None)
        self.port = port or getattr(self.cfg.Postgresql, 'port', 5432)
        self.dbname = dbname or getattr(self.cfg.Postgresql, 'dbname', None)
        self.user = user or getattr(self.cfg.Postgresql, 'user', None)
        self.password = passwd or getattr(self.cfg.Postgresql, 'password', None)
        
        required = ["host", "port", "dbname", "user", "password"]
        missing = [name for name, val in zip(required, [self.host, self.port, self.dbname, self.user, self.password]) if not val]

        if missing:
            raise ValueError(f"数据库连接参数不完整, 请提供{missing}")
        
        # 创建数据库连接池
        self.connection_pool = PostgreSQLConnectionPool(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        
        # 加载SQL定义
        self.sql_loader = get_sql_loader()
        
        # 存储已加载的Repo实例
        self._repos: Dict[str, Any] = {}
        
        # 动态加载所有Repo类
        self._load_repos()
    
    def _load_repos(self):
        """动态加载所有的Repo类
        
        从Repo目录加载所有继承自BaseRepo的类, 并创建实例
        """
        repo_modules = [
            "MemoryLogRepo", "TasksRepo", "TaskStepsRepo", "ToolCallsRepo"
        ]
        
        for repo_name in repo_modules:
            try:
                module = importlib.import_module(f".Repo.{repo_name}", package="mylib.sql")
                
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if name == repo_name and hasattr(cls, 'get_table_name'):
                        instance = cls(self.connection_pool)
                        table_name = instance.get_table_name()
                        self._repos[table_name] = instance
            except ImportError:
                pass
    
    def __getattr__(self, name: str) -> Callable:
        """动态生成表操作方法
        
        支持 Create_{表名}, Read_{表名}, Update_{表名}, Delete_{表名} 格式的方法调用
        
        Args:
            name: 方法名
            
        Returns:
            对应的操作函数
            
        Raises:
            AttributeError: 如果方法名格式不正确或表不存在
        """
        if name.startswith(('Create_', 'Read_', 'Update_', 'Delete_')):
            operation, table_name = name.split('_', 1)
            
            table_name = table_name.lower()
            
            if table_name not in self._repos:
                raise AttributeError(f"表 '{table_name}' 不存在或未加载对应的Repo")
            
            repo = self._repos[table_name]
            
            if operation == 'Create':
                def create(model_instance):
                    """创建记录
                    
                    Args:
                        model_instance: pydantic模型实例
                        
                    Returns:
                        创建后的模型实例
                    """
                    return repo.create(model_instance)
                
                return create
            
            elif operation == 'Read':
                def read(**kwargs):
                    """读取记录
                    
                    支持通过_allowed_get_fields中的字段进行查询
                    
                    Returns:
                        查询结果列表
                    """
                    return repo.read(**kwargs)
                
                return read
            
            elif operation == 'Update':
                def update(id, **kwargs):
                    """更新记录
                    
                    Args:
                        id: 记录ID
                        **kwargs: 要更新的字段和值
                        
                    Returns:
                        更新是否成功
                    """
                    return repo.update(id, **kwargs)
                
                return update
            
            elif operation == 'Delete':
                def delete(id):
                    """删除记录
                    
                    Args:
                        id: 记录ID
                        
                    Returns:
                        删除是否成功
                    """
                    return repo.delete(id)
                
                return delete
        
        raise AttributeError(f"'{self.__class__.__name__}' 对象没有属性 '{name}'")
    
    def get_supported_tables(self) -> List[str]:
        """获取所有支持的表名
        
        Returns:
            表名列表
        """
        return list(self._repos.keys())
    
    def get_table_fields(self, table_name: str) -> Dict[str, Any]:
        """获取特定表的所有字段信息
        
        Args:
            table_name: 表名
            
        Returns:
            字段信息字典，包含字段名、类型等
            
        Raises:
            ValueError: 如果表不存在
        """
        if table_name not in self._repos:
            raise ValueError(f"表 '{table_name}' 不存在")
        
        repo = self._repos[table_name]
        model_class = repo._model_class
        
        fields_info = {}
        for field_name, field_info in model_class.model_fields.items():
            fields_info[field_name] = {
                "type": str(field_info.annotation),
                "description": field_info.description or "",
                "required": field_info.is_required(),
                "default": field_info.default if field_info.default is not field_info.default_factory else "<factory>"
            }
        
        return fields_info
    
    def get_table_create_sql(self, table_name: str) -> str:
        """获取创建表的SQL语句
        
        Args:
            table_name: 表名
            
        Returns:
            创建表的SQL语句
            
        Raises:
            ValueError: 如果表不存在或没有创建SQL
        """
        if table_name not in self._repos:
            raise ValueError(f"表 '{table_name}' 不存在")
        
        repo = self._repos[table_name]
        if not repo.CREATE_TABLE_SQL:
            raise ValueError(f"表 '{table_name}' 没有创建SQL语句")
        
        return repo.CREATE_TABLE_SQL
    
    def test_connect(self):
        """测试数据库连接
        
        Returns:
            连接是否成功
        """
        try:
            conn = self.connection_pool.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"数据库连接成功! PostgreSQL 版本: {version}")
            self.connection_pool.release_connection(conn)
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def __del__(self):
        """析构函数，关闭连接池"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.clear_connections()


if __name__ == "__main__":
    try:
        sql = Sql()
        sql.test_connect()
        print(f"支持的表名: {sql.get_supported_tables()}")
        if sql.get_supported_tables():
            first_table = sql.get_supported_tables()[0]
            print(f"\n表 '{first_table}' 的字段信息:")
            for field_name, field_info in sql.get_table_fields(first_table).items():
                print(f"  {field_name}: {field_info}")
    except Exception as e:
        print(f"测试失败: {e}")
