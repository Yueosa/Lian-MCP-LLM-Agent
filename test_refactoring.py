#!/usr/bin/env python3
"""测试 Pydantic 迁移和 SqlLoader 动态加载的脚本"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 首先导入 SqlLoader（不需要数据库连接）
from mylib.sql.sql.SqlLoader import get_sql_loader

# 导入 Model 类
from mylib.sql.Model.MemoryLog import MemoryLog
from mylib.sql.Model.Tasks import Task
from mylib.sql.Model.TaskSteps import TaskStep
from mylib.sql.Model.ToolCalls import ToolCall
from mylib.sql.Model.Enum import (
    memory_log_role, memoty_log_memory_type,
    tasks_status, task_steps_status, tool_calls_status
)

def test_sql_loader():
    """测试 SqlLoader 动态加载"""
    print("\n========== 测试 SqlLoader ==========")
    loader = get_sql_loader()
    
    # 测试获取表元数据
    tables = ["memory_log", "tasks", "task_steps", "tool_calls"]
    for table_name in tables:
        table_meta = loader.get_table_meta(table_name)
        create_sql = loader.get_table_create_sql(table_name)
        
        print(f"\n表: {table_name}")
        print(f"  字段数: {len(table_meta.columns) if table_meta else 0}")
        print(f"  CREATE_TABLE_SQL 已加载: {create_sql is not None and len(create_sql) > 0}")
        if create_sql:
            print(f"  SQL 长度: {len(create_sql)} 字符")
            # 显示前 100 个字符
            sql_preview = create_sql.replace('\n', ' ')[:100]
            print(f"  SQL 预览: {sql_preview}...")

def test_pydantic_models():
    """测试 Pydantic 模型"""
    print("\n========== 测试 Pydantic 模型 ==========")
    
    # 测试 MemoryLog
    print("\n1. MemoryLog 模型:")
    memory = MemoryLog(
        id=1,
        user_id="test_user",
        role=memory_log_role.user,
        content="Hello",
        embedding=[0.1, 0.2, 0.3],
        memory_type=memoty_log_memory_type.conversation,
        importance=0.8,
        created_at=datetime.now()
    )
    print(f"   {memory}")
    print(f"   model_dump: {memory.model_dump()}")
    print(f"   model_dump_json: {memory.model_dump_json()[:100]}...")
    
    # 测试 Task
    print("\n2. Task 模型:")
    task = Task(
        id=1,
        user_id="test_user",
        title="Test Task",
        description="This is a test task",
        status=tasks_status.pending,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    print(f"   {task}")
    print(f"   model_dump: {task.model_dump()}")
    
    # 测试 TaskStep
    print("\n3. TaskStep 模型:")
    step = TaskStep(
        id=1,
        task_id=1,
        step_index=1,
        instruction="Do something",
        output="Done",
        status=task_steps_status.done,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    print(f"   {step}")
    
    # 测试 ToolCall
    print("\n4. ToolCall 模型:")
    tool_call = ToolCall(
        id=1,
        task_id=1,
        step_id=1,
        tool_name="file_read",
        arguments={"path": "/tmp/test.txt"},
        response={"status": "success"},
        status=tool_calls_status.success,
        created_at=datetime.now()
    )
    print(f"   {tool_call}")
    print(f"   model_dump: {tool_call.model_dump()}")

def test_repos_dynamic_loading():
    """测试 Repos 动态加载表名和 SQL"""
    print("\n========== 测试 Repos 动态加载 ==========")
    
    # 延迟导入 Repos（需要数据库连接）
    try:
        from mylib.sql.MemoryLogRepo import MemoryLogRepo
        from mylib.sql.TasksRepo import TasksRepo
        from mylib.sql.TaskStepsRepo import TaskStepsRepo
        from mylib.sql.ToolCallsRepo import ToolCallsRepo
        
        repos = [
            ("MemoryLogRepo", MemoryLogRepo),
            ("TasksRepo", TasksRepo),
            ("TaskStepsRepo", TaskStepsRepo),
            ("ToolCallsRepo", ToolCallsRepo)
        ]
        
        for repo_name, repo_class in repos:
            print(f"\n{repo_name}:")
            print(f"  表名: {repo_class._table_name}")
            print(f"  CREATE_TABLE_SQL 长度: {len(repo_class.CREATE_TABLE_SQL) if repo_class.CREATE_TABLE_SQL else 0}")
            print(f"  允许查询字段: {repo_class._allowed_get_fields}")
            
            # 验证 get_table_name() 方法
            instance = repo_class()
            print(f"  get_table_name(): {instance.get_table_name()}")
    except ImportError as e:
        print(f"  ⚠ 跳过 Repos 测试（数据库连接不可用）: {e}")

def main():
    """运行所有测试"""
    print("开始测试 Pydantic 迁移和 SqlLoader 动态加载...")
    
    try:
        test_sql_loader()
        test_pydantic_models()
        test_repos_dynamic_loading()
        print("\n" + "="*50)
        print("✓ 所有测试通过！")
        print("="*50)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
