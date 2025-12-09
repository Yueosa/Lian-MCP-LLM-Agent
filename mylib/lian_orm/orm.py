import inspect
import importlib
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, TYPE_CHECKING

from .config import load_sql_config
from .database.pool import PostgreSQLConnectionPool
from .database.client import DatabaseClient
from .schema.manager import SchemaManager
from .repository import MemoryLogRepo, TasksRepo, TaskStepsRepo, ToolCallsRepo

if TYPE_CHECKING:
    from .repository import MemoryLogRepo, TasksRepo, TaskStepsRepo, ToolCallsRepo


class Sql:
    """ORM 抽象层的顶层接口类
    
    提供数据库连接和表操作方法。
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
            self.cfg = load_sql_config(config_path=config_path)
        else:
            self.cfg = load_sql_config()
        
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
        
        # 创建数据库客户端
        self.db_client = DatabaseClient(self.connection_pool)
        
        # 加载Schema
        sql_file_path = Path(__file__).parent / "schema" / "localfile" / "LML_SQL.sql"
        self.schema_manager = SchemaManager(str(sql_file_path))
        
        # 存储已加载的Repo实例
        self._repos: Dict[str, Any] = {}
        
        # 动态加载所有Repo类
        self._load_repos()

    @property
    def memory_log(self) -> "MemoryLogRepo":
        return self._repos.get("memory_log")

    @property
    def tasks(self) -> "TasksRepo":
        return self._repos.get("tasks")

    @property
    def task_steps(self) -> "TaskStepsRepo":
        return self._repos.get("task_steps")

    @property
    def tool_calls(self) -> "ToolCallsRepo":
        return self._repos.get("tool_calls")
    
    def _load_repos(self):
        """动态加载所有的Repo类
        
        从Repo目录加载所有继承自BaseRepo的类, 并创建实例
        """
        repo_modules = [
            "MemoryLogRepo", "TasksRepo", "TaskStepsRepo", "ToolCallsRepo"
        ]
        
        for repo_name in repo_modules:
            try:
                # 注意：这里 package 需要根据实际包名调整
                module = importlib.import_module(f".repository.{repo_name}", package="mylib.lian_orm")
                
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if name == repo_name and hasattr(cls, 'get_table_name'):
                        # 获取表元数据
                        table_name = cls(self.db_client).get_table_name() # 临时实例化获取表名，或者改为类方法
                        # 更好的方式是实例化一次
                        
                        # 尝试从 SchemaManager 获取 TableMeta
                        table_meta = None
                        try:
                            table_meta = self.schema_manager.get_table(table_name)
                        except ValueError:
                            pass
                        
                        # 传入 db_client 和 table_meta
                        instance = cls(self.db_client, table_meta=table_meta)
                        self._repos[table_name] = instance
            except ImportError as e:
                print(f"Failed to load repo {repo_name}: {e}")
                pass
    
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
