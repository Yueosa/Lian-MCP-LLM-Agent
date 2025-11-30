"""
SQL ORM 模块完整功能测试与使用教程

这个测试文件同时作为 SQL ORM 模块的使用教程，展示了所有主要功能的使用方法。

测试覆盖: 
1. 数据库连接与配置
2. 基本 CRUD 操作
3. 外键关系定义
4. 关系查询（一对多、多对一）
5. 选择性关系加载
6. JOIN 多表联合查询
7. 批量操作
8. 事务处理
9. 高级查询
10. 数据导出

作者: Lian
创建日期: 2025-11-24
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mylib.lian_orm import Sql
from mylib.lian_orm.Model import Task, TaskStep, ToolCall, MemoryLog
from mylib.lian_orm.Model.Enum import tasks_status, task_steps_status, tool_calls_status
from mylib.kit import Loutput

# 初始化
lo = Loutput()
sql = Sql()

# 用于统计测试结果
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def test_section(title: str):
    """测试章节标题"""
    lo.lput(f"\n{'='*60}", font_color="cyan")
    lo.lput(f"  {title}", font_color="cyan_high")
    lo.lput(f"{'='*60}", font_color="cyan")

def test_case(name: str, success: bool, message: str = ""):
    """记录测试用例结果"""
    if success:
        test_results["passed"] += 1
        lo.lput(f"✓ {name}", font_color="green")
        if message:
            lo.lput(f"  {message}", font_color="white")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(name)
        lo.lput(f"✗ {name}", font_color="red")
        if message:
            lo.lput(f"  错误: {message}", font_color="red")

def cleanup_test_data():
    """清理所有测试数据"""
    try:
        existing_tasks = sql.Read_tasks(user_id="test_sql_tutorial")
        for task in existing_tasks:
            sql.Delete_tasks(task.id)
        existing_memory = sql.Read_memory_log(user_id="test_sql_tutorial")
        for mem in existing_memory:
            sql.Delete_memory_log(mem.id)
        return len(existing_tasks) + len(existing_memory)
    except:
        return 0


# ============================================================
# 第一部分: 数据库连接与配置
# ============================================================
test_section("第一部分: 数据库连接与配置")

lo.lput("\n【测试 1.1】数据库连接测试", font_color="yellow")
lo.lput("说明: 测试基本的数据库连接功能", font_color="white")
lo.lput("代码: sql.test_connect()", font_color="gray")

try:
    connected = sql.test_connect()
    test_case("数据库连接", connected, "PostgreSQL 连接成功")
except Exception as e:
    test_case("数据库连接", False, str(e))

lo.lput("\n【测试 1.2】查看支持的表", font_color="yellow")
lo.lput("说明: 获取所有已加载的数据表列表", font_color="white")
lo.lput("代码: sql.get_supported_tables()", font_color="gray")

try:
    tables = sql.get_supported_tables()
    test_case("获取表列表", len(tables) > 0, f"找到 {len(tables)} 个表: {tables}")
except Exception as e:
    test_case("获取表列表", False, str(e))

lo.lput("\n【测试 1.3】查看表字段信息", font_color="yellow")
lo.lput("说明: 获取指定表的所有字段定义和类型", font_color="white")
lo.lput("代码: sql.get_table_fields('tasks')", font_color="gray")

try:
    fields = sql.get_table_fields('tasks')
    lo.lput(f"  tasks 表字段: ", font_color="white")
    for field_name, info in list(fields.items()):
        lo.lput(f"    - {field_name}: {info['type']}", font_color="gray")
    test_case("获取字段信息", len(fields) > 0, f"共 {len(fields)} 个字段")
except Exception as e:
    test_case("获取字段信息", False, str(e))


# ============================================================
# 第二部分: 基本 CRUD 操作
# ============================================================
test_section("第二部分: 基本 CRUD 操作（Create, Read, Update, Delete）")

# 清理旧数据
cleanup_count = cleanup_test_data()
lo.lput(f"\n清理了 {cleanup_count} 条旧测试数据\n", font_color="yellow")

lo.lput("【测试 2.1】创建记录 (Create)", font_color="yellow")
lo.lput("说明: 使用 Pydantic 模型创建新记录", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  task = Task(user_id='test', title='新任务', status=tasks_status.pending)", font_color="gray")
lo.lput("  created = sql.Create_tasks(task)", font_color="gray")

created_task = None
try:
    task = Task(
        user_id="test_sql_tutorial",
        title="完整测试任务",
        description="这是一个用于测试 SQL ORM 所有功能的任务",
        status=tasks_status.pending
    )
    created_task = sql.Create_tasks(task)
    test_case(
        "创建任务记录", 
        created_task.id is not None,
        f"任务 ID: {created_task.id}, 标题: '{created_task.title}'"
    )
except Exception as e:
    test_case("创建任务记录", False, str(e))

lo.lput("\n【测试 2.2】读取记录 (Read)", font_color="yellow")
lo.lput("说明: 根据条件查询记录，支持多字段组合查询", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  # 查询所有记录", font_color="gray")
lo.lput("  all_tasks = sql.Read_tasks()", font_color="gray")
lo.lput("  # 单字段查询", font_color="gray")
lo.lput("  user_tasks = sql.Read_tasks(user_id='test')", font_color="gray")
lo.lput("  # 多字段查询", font_color="gray")
lo.lput("  pending = sql.Read_tasks(user_id='test', status='pending')", font_color="gray")

try:
    # 根据 ID 查询
    tasks_by_id = sql.Read_tasks(id=created_task.id)
    test_case("根据 ID 查询", len(tasks_by_id) == 1, f"查询到 {len(tasks_by_id)} 条记录")
    
    # 根据 user_id 查询
    tasks_by_user = sql.Read_tasks(user_id="test_sql_tutorial")
    test_case("根据 user_id 查询", len(tasks_by_user) >= 1, f"查询到 {len(tasks_by_user)} 条记录")
    
    # 多条件组合查询
    tasks_combined = sql.Read_tasks(user_id="test_sql_tutorial", status="pending")
    test_case("多条件组合查询", len(tasks_combined) >= 1, f"查询到 {len(tasks_combined)} 条记录")
except Exception as e:
    test_case("读取记录", False, str(e))

lo.lput("\n【测试 2.3】更新记录 (Update)", font_color="yellow")
lo.lput("说明: 根据 ID 更新记录的字段值", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  success = sql.Update_tasks(task_id, status='running', title='新标题')", font_color="gray")

try:
    # 更新单个字段
    success1 = sql.Update_tasks(created_task.id, status=tasks_status.running)
    
    # 验证更新
    updated_task = sql.Read_tasks(id=created_task.id)[0]
    test_case(
        "更新任务状态", 
        updated_task.status == tasks_status.running,
        f"状态已更新为: {updated_task.status.value}"
    )
    
    # 更新多个字段
    success2 = sql.Update_tasks(
        created_task.id, 
        status=tasks_status.done,
        description="已完成的任务描述"
    )
    
    updated_task2 = sql.Read_tasks(id=created_task.id)[0]
    test_case(
        "更新多个字段",
        updated_task2.status == tasks_status.done,
        f"状态: {updated_task2.status.value}, 描述已更新"
    )
except Exception as e:
    test_case("更新记录", False, str(e))

lo.lput("\n【测试 2.4】枚举值处理", font_color="yellow")
lo.lput("说明: ORM 自动处理枚举类型的转换", font_color="white")
lo.lput("支持的枚举类型: ", font_color="gray")
lo.lput("  - tasks_status: pending, running, done, failed", font_color="gray")
lo.lput("  - task_steps_status: pending, running, done, failed", font_color="gray")
lo.lput("  - tool_calls_status: success, failed", font_color="gray")

try:
    # 使用枚举对象
    task_enum = Task(
        user_id="test_sql_tutorial",
        title="枚举测试任务",
        status=tasks_status.pending  # 使用枚举对象
    )
    created_enum = sql.Create_tasks(task_enum)
    
    # 使用字符串值
    sql.Update_tasks(created_enum.id, status="running")  # 使用字符串
    
    updated = sql.Read_tasks(id=created_enum.id)[0]
    test_case(
        "枚举类型处理",
        updated.status == tasks_status.running,
        "枚举和字符串均可正确处理"
    )
    
    # 清理
    sql.Delete_tasks(created_enum.id)
except Exception as e:
    test_case("枚举类型处理", False, str(e))


# ============================================================
# 第三部分: 外键关系与关联查询
# ============================================================
test_section("第三部分: 外键关系与关联查询")

lo.lput("\n【测试 3.1】创建带外键的记录", font_color="yellow")
lo.lput("说明: 创建具有外键关联的子记录", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  step = TaskStep(task_id=task.id, step_index=1, instruction='步骤1')", font_color="gray")
lo.lput("  created_step = sql.Create_task_steps(step)", font_color="gray")

created_steps = []
try:
    # 重置任务状态为 pending
    sql.Update_tasks(created_task.id, status=tasks_status.pending)
    
    # 创建多个步骤
    steps_data = [
        {"step_index": 1, "instruction": "初始化项目环境", "status": task_steps_status.done},
        {"step_index": 2, "instruction": "加载配置文件", "status": task_steps_status.done},
        {"step_index": 3, "instruction": "连接数据库", "status": task_steps_status.running},
        {"step_index": 4, "instruction": "执行业务逻辑", "status": task_steps_status.pending},
    ]
    
    for step_data in steps_data:
        step = TaskStep(task_id=created_task.id, **step_data)
        created_step = sql.Create_task_steps(step)
        created_steps.append(created_step)
    
    test_case("创建关联步骤", len(created_steps) == 4, f"成功创建 {len(created_steps)} 个步骤")
except Exception as e:
    test_case("创建关联步骤", False, str(e))

lo.lput("\n【测试 3.2】基本关系查询（不加载关联）", font_color="yellow")
lo.lput("说明: 标准查询不会自动加载关联对象，需要显式调用", font_color="white")
lo.lput("代码: task = sql.Read_tasks(id=task_id)[0]", font_color="gray")

try:
    task = sql.Read_tasks(id=created_task.id)[0]
    related_count = len(task.get_related_objects())
    test_case(
        "基本查询不加载关联",
        related_count == 0,
        f"关联对象数量: {related_count}（符合预期）"
    )
except Exception as e:
    test_case("基本查询不加载关联", False, str(e))

lo.lput("\n【测试 3.3】加载所有关联对象", font_color="yellow")
lo.lput("说明: 使用 Read_With_Relations 自动加载所有定义的关联对象", font_color="white")
lo.lput("代码: tasks = sql.Read_tasks_With_Relations(id=task_id)", font_color="gray")
lo.lput("特点: ", font_color="gray")
lo.lput("  - 批量加载，避免 N+1 查询问题", font_color="gray")
lo.lput("  - 支持一对多、多对一、一对一关系", font_color="gray")
lo.lput("  - 自动根据模型定义加载所有关系", font_color="gray")

try:
    tasks_with_relations = sql.Read_tasks_With_Relations(id=created_task.id)
    task = tasks_with_relations[0]
    
    # 获取关联的步骤
    steps = task.get_related_object("task_steps")
    test_case(
        "加载一对多关系（步骤）",
        steps is not None and len(steps) == 4,
        f"加载了 {len(steps) if steps else 0} 个关联步骤"
    )
    
    if steps:
        lo.lput("  关联步骤详情: ", font_color="white")
        for step in steps:
            lo.lput(f"    步骤 {step.step_index}: {step.instruction} [{step.status.value}]", font_color="gray")
except Exception as e:
    test_case("加载所有关联对象", False, str(e))

lo.lput("\n【测试 3.4】选择性加载特定关系", font_color="yellow")
lo.lput("说明: 只加载指定的关系，提高查询效率", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  # 只加载步骤，不加载工具调用", font_color="gray")
lo.lput("  tasks = sql.Read_tasks_With_Relations(relations=['task_steps'], id=task_id)", font_color="gray")

try:
    # 创建一个工具调用用于测试
    tool_call = ToolCall(
        task_id=created_task.id,
        step_id=created_steps[0].id,
        tool_name="database_query",
        arguments={"query": "SELECT * FROM users"},
        response={"rows": 100, "time": "0.05s"},
        status=tool_calls_status.success
    )
    created_tool = sql.Create_tool_calls(tool_call)
    
    # 只加载步骤
    tasks_partial = sql.Read_tasks_With_Relations(
        relations=["task_steps"],
        id=created_task.id
    )
    task_partial = tasks_partial[0]
    
    has_steps = task_partial.get_related_object("task_steps") is not None
    has_tools = task_partial.get_related_object("tool_calls") is not None
    
    test_case(
        "选择性关系加载",
        has_steps and not has_tools,
        "只加载了 task_steps，未加载 tool_calls（符合预期）"
    )
except Exception as e:
    test_case("选择性关系加载", False, str(e))

lo.lput("\n【测试 3.5】反向关系查询（多对一）", font_color="yellow")
lo.lput("说明: 从子记录查询父记录（如从 TaskStep 查询 Task）", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  steps = sql.Read_task_steps_With_Relations(relations=['task'], task_id=task_id)", font_color="gray")
lo.lput("  parent_task = steps[0].get_related_object('task')", font_color="gray")

try:
    steps_with_task = sql.Read_task_steps_With_Relations(
        relations=["task"],
        task_id=created_task.id
    )
    
    success_count = 0
    for step in steps_with_task:
        parent_task = step.get_related_object("task")
        if parent_task and parent_task.id == created_task.id:
            success_count += 1
    
    test_case(
        "反向关系查询",
        success_count == len(steps_with_task),
        f"{success_count}/{len(steps_with_task)} 个步骤成功加载父任务"
    )
    
    if steps_with_task and steps_with_task[0].get_related_object("task"):
        parent = steps_with_task[0].get_related_object("task")
        lo.lput(f"  示例: 步骤 1 的父任务 = '{parent.title}'", font_color="white")
except Exception as e:
    test_case("反向关系查询", False, str(e))

lo.lput("\n【测试 3.6】多级关系导航", font_color="yellow")
lo.lput("说明: 通过关联对象进行多级查询（ToolCall → TaskStep → Task）", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  tool = sql.Read_tool_calls_With_Relations(relations=['task_step'], id=tool_id)[0]", font_color="gray")
lo.lput("  step = tool.get_related_object('task_step')", font_color="gray")
lo.lput("  # 再查询 step 的 task", font_color="gray")

try:
    # 查询工具调用及其步骤
    tools_with_step = sql.Read_tool_calls_With_Relations(
        relations=["task_step"],
        id=created_tool.id
    )
    
    if tools_with_step:
        tool = tools_with_step[0]
        step = tool.get_related_object("task_step")
        
        if step:
            # 再查询步骤的任务
            steps_with_task = sql.Read_task_steps_With_Relations(
                relations=["task"],
                id=step.id
            )
            
            if steps_with_task:
                final_task = steps_with_task[0].get_related_object("task")
                test_case(
                    "多级关系导航",
                    final_task is not None and final_task.id == created_task.id,
                    f"ToolCall → TaskStep → Task 导航成功"
                )
                lo.lput(f"  导航路径: 工具'{tool.tool_name}' → 步骤'{step.instruction}' → 任务'{final_task.title}'", font_color="white")
            else:
                test_case("多级关系导航", False, "无法加载任务")
        else:
            test_case("多级关系导航", False, "无法加载步骤")
    else:
        test_case("多级关系导航", False, "无法查询工具调用")
except Exception as e:
    test_case("多级关系导航", False, str(e))


# ============================================================
# 第四部分: JOIN 查询
# ============================================================
test_section("第四部分: JOIN 多表联合查询")

lo.lput("\n【测试 4.1】INNER JOIN 查询", font_color="yellow")
lo.lput("说明: 使用 INNER JOIN 联合查询两个表", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  results = sql.Join_tasks_task_steps(", font_color="gray")
lo.lput("      join_condition='tasks.id = task_steps.task_id',", font_color="gray")
lo.lput("      select_fields=['tasks.title', 'task_steps.instruction'],", font_color="gray")
lo.lput("      **{'tasks.id': task_id}", font_color="gray")
lo.lput("  )", font_color="gray")

try:
    results = sql.Join_tasks_task_steps(
        join_condition="tasks.id = task_steps.task_id",
        select_fields=["tasks.title", "tasks.status", "task_steps.instruction", "task_steps.step_index", "task_steps.status"],
        **{"tasks.id": created_task.id}
    )
    
    test_case(
        "INNER JOIN 查询",
        len(results) > 0,
        f"查询到 {len(results)} 条联合记录"
    )
    
    if results:
        lo.lput("  查询结果示例: ", font_color="white")
        for i, result in enumerate(results[:3], 1):
            lo.lput(
                f"    {i}. 任务: {result.get('title')} | 步骤{result.get('step_index')}: {result.get('instruction')}",
                font_color="gray"
            )
except Exception as e:
    test_case("INNER JOIN 查询", False, str(e))

lo.lput("\n【测试 4.2】LEFT JOIN 查询", font_color="yellow")
lo.lput("说明: LEFT JOIN 保留左表所有记录，即使右表无匹配", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  results = sql.Join_tasks_task_steps(", font_color="gray")
lo.lput("      join_condition='tasks.id = task_steps.task_id',", font_color="gray")
lo.lput("      join_type='LEFT',", font_color="gray")
lo.lput("      **{'tasks.user_id': 'test_sql_tutorial'}", font_color="gray")
lo.lput("  )", font_color="gray")

try:
    # 创建一个没有步骤的任务
    task_no_steps = Task(
        user_id="test_sql_tutorial",
        title="无步骤任务",
        status=tasks_status.pending
    )
    created_no_steps = sql.Create_tasks(task_no_steps)
    
    # LEFT JOIN 查询
    results_left = sql.Join_tasks_task_steps(
        join_condition="tasks.id = task_steps.task_id",
        join_type="LEFT",
        select_fields=["tasks.title", "task_steps.instruction"],
        **{"tasks.user_id": "test_sql_tutorial"}
    )
    
    # 应该包含有步骤的任务和无步骤的任务
    test_case(
        "LEFT JOIN 查询",
        len(results_left) > len(created_steps),
        f"查询到 {len(results_left)} 条记录（包含无步骤任务）"
    )
    
    # 清理
    sql.Delete_tasks(created_no_steps.id)
except Exception as e:
    test_case("LEFT JOIN 查询", False, str(e))

lo.lput("\n【测试 4.3】三表 JOIN 查询", font_color="yellow")
lo.lput("说明: 查询任务、步骤和工具调用的联合信息", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  # 先 JOIN tasks 和 task_steps", font_color="gray")
lo.lput("  results = sql.Join_task_steps_tool_calls(", font_color="gray")
lo.lput("      join_condition='task_steps.id = tool_calls.step_id',", font_color="gray")
lo.lput("      select_fields=['task_steps.instruction', 'tool_calls.tool_name'],", font_color="gray")
lo.lput("      **{'task_steps.task_id': task_id}", font_color="gray")
lo.lput("  )", font_color="gray")

try:
    # 查询步骤和工具调用的联合信息
    results_3table = sql.Join_task_steps_tool_calls(
        join_condition="task_steps.id = tool_calls.step_id",
        select_fields=["task_steps.instruction", "task_steps.step_index", "tool_calls.tool_name", "tool_calls.status"],
        **{"task_steps.task_id": created_task.id}
    )
    
    test_case(
        "三表联合查询",
        len(results_3table) > 0,
        f"查询到 {len(results_3table)} 条关联记录"
    )
    
    if results_3table:
        lo.lput("  查询结果: ", font_color="white")
        for result in results_3table:
            lo.lput(
                f"    步骤{result.get('step_index')}: {result.get('instruction')} | 使用工具: {result.get('tool_name')}",
                font_color="gray"
            )
except Exception as e:
    test_case("三表联合查询", False, str(e))


# ============================================================
# 第五部分: 数据导出与序列化
# ============================================================
test_section("第五部分: 数据导出与序列化")

lo.lput("\n【测试 5.1】导出单条记录", font_color="yellow")
lo.lput("说明: 将 Pydantic 模型导出为字典", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  task = sql.Read_tasks(id=task_id)[0]", font_color="gray")
lo.lput("  task_dict = task.model_dump()  # Pydantic v2", font_color="gray")
lo.lput("  # 或 task.dict()  # Pydantic v1", font_color="gray")

try:
    task = sql.Read_tasks(id=created_task.id)[0]
    task_dict = task.model_dump()
    
    test_case(
        "导出记录为字典",
        isinstance(task_dict, dict) and 'id' in task_dict,
        f"导出了 {len(task_dict)} 个字段"
    )
    
    lo.lput(f"  导出字段: {list(task_dict.keys())}", font_color="white")
except Exception as e:
    test_case("导出记录为字典", False, str(e))

lo.lput("\n【测试 5.2】导出包含关系的数据", font_color="yellow")
lo.lput("说明: 导出记录及其所有关联对象", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  task = sql.Read_tasks_With_Relations(id=task_id)[0]", font_color="gray")
lo.lput("  task_dict = task.to_dict_with_relations()  # 包含所有关系", font_color="gray")
lo.lput("  # 或选择性导出", font_color="gray")
lo.lput("  task_dict = task.to_dict_with_relations(include_relations=['task_steps'])", font_color="gray")

try:
    task_full = sql.Read_tasks_With_Relations(id=created_task.id)[0]
    
    # 导出所有关系
    full_dict = task_full.to_dict_with_relations()
    test_case(
        "导出完整关系数据",
        'task_steps' in full_dict and 'tool_calls' in full_dict,
        f"包含关系: {[k for k in full_dict.keys() if k in ['task_steps', 'tool_calls']]}"
    )
    
    lo.lput(f"  - 步骤数量: {len(full_dict.get('task_steps', []))}", font_color="white")
    lo.lput(f"  - 工具调用数量: {len(full_dict.get('tool_calls', []))}", font_color="white")
    
    # 选择性导出
    partial_dict = task_full.to_dict_with_relations(include_relations=["task_steps"])
    test_case(
        "选择性导出关系",
        'task_steps' in partial_dict and 'tool_calls' not in partial_dict,
        "只包含 task_steps，不包含 tool_calls"
    )
except Exception as e:
    test_case("导出包含关系的数据", False, str(e))


# ============================================================
# 第六部分: 批量操作与高级查询
# ============================================================
test_section("第六部分: 批量操作与高级查询")

lo.lput("\n【测试 6.1】批量创建记录", font_color="yellow")
lo.lput("说明: 快速创建多条记录", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  for i in range(10):", font_color="gray")
lo.lput("      task = Task(user_id='test', title=f'批量任务{i}')", font_color="gray")
lo.lput("      sql.Create_tasks(task)", font_color="gray")

try:
    batch_tasks = []
    for i in range(5):
        task = Task(
            user_id="test_sql_tutorial",
            title=f"批量任务 {i+1}",
            description=f"这是第 {i+1} 个批量创建的任务",
            status=tasks_status.pending
        )
        created = sql.Create_tasks(task)
        batch_tasks.append(created)
    
    test_case(
        "批量创建记录",
        len(batch_tasks) == 5,
        f"成功创建 {len(batch_tasks)} 条记录"
    )
except Exception as e:
    test_case("批量创建记录", False, str(e))

lo.lput("\n【测试 6.2】批量查询", font_color="yellow")
lo.lput("说明: 查询符合条件的所有记录", font_color="white")
lo.lput("代码: all_test_tasks = sql.Read_tasks(user_id='test_sql_tutorial')", font_color="gray")

try:
    all_test_tasks = sql.Read_tasks(user_id="test_sql_tutorial")
    test_case(
        "批量查询记录",
        len(all_test_tasks) >= 6,  # 1个主测试任务 + 5个批量任务
        f"查询到 {len(all_test_tasks)} 条测试用户的任务"
    )
    
    # 统计各状态数量
    status_count = {}
    for task in all_test_tasks:
        status = task.status.value
        status_count[status] = status_count.get(status, 0) + 1
    
    lo.lput("  任务状态分布: ", font_color="white")
    for status, count in status_count.items():
        lo.lput(f"    - {status}: {count} 个", font_color="gray")
except Exception as e:
    test_case("批量查询记录", False, str(e))

lo.lput("\n【测试 6.3】批量更新", font_color="yellow")
lo.lput("说明: 更新多条记录的状态", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  pending_tasks = sql.Read_tasks(status='pending')", font_color="gray")
lo.lput("  for task in pending_tasks:", font_color="gray")
lo.lput("      sql.Update_tasks(task.id, status='running')", font_color="gray")

try:
    # 将所有 pending 的批量任务更新为 running
    pending_tasks = sql.Read_tasks(user_id="test_sql_tutorial", status="pending")
    update_count = 0
    for task in pending_tasks:
        if "批量任务" in task.title:
            sql.Update_tasks(task.id, status=tasks_status.running)
            update_count += 1
    
    # 验证更新
    running_tasks = sql.Read_tasks(user_id="test_sql_tutorial", status="running")
    test_case(
        "批量更新记录",
        update_count > 0,
        f"成功更新 {update_count} 条记录为 running 状态"
    )
except Exception as e:
    test_case("批量更新记录", False, str(e))

lo.lput("\n【测试 6.4】批量删除", font_color="yellow")
lo.lput("说明: 删除批量创建的测试任务", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  tasks_to_delete = sql.Read_tasks(user_id='test')", font_color="gray")
lo.lput("  for task in tasks_to_delete:", font_color="gray")
lo.lput("      sql.Delete_tasks(task.id)", font_color="gray")

try:
    # 删除批量任务
    delete_count = 0
    for task in batch_tasks:
        success = sql.Delete_tasks(task.id)
        if success:
            delete_count += 1
    
    test_case(
        "批量删除记录",
        delete_count == len(batch_tasks),
        f"成功删除 {delete_count}/{len(batch_tasks)} 条记录"
    )
except Exception as e:
    test_case("批量删除记录", False, str(e))


# ============================================================
# 第七部分: 级联删除与外键约束
# ============================================================
test_section("第七部分: 级联删除与外键约束")

lo.lput("\n【测试 7.1】级联删除测试", font_color="yellow")
lo.lput("说明: 删除父记录时，子记录会被自动删除（ON DELETE CASCADE）", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  # 删除任务会自动删除其步骤和工具调用", font_color="gray")
lo.lput("  sql.Delete_tasks(task_id)", font_color="gray")

try:
    # 创建测试任务和步骤
    cascade_task = Task(
        user_id="test_sql_tutorial",
        title="级联删除测试任务",
        status=tasks_status.pending
    )
    cascade_created = sql.Create_tasks(cascade_task)
    
    # 创建步骤
    cascade_steps = []
    for i in range(3):
        step = TaskStep(
            task_id=cascade_created.id,
            step_index=i+1,
            instruction=f"步骤 {i+1}",
            status=task_steps_status.pending
        )
        cascade_steps.append(sql.Create_task_steps(step))
    
    # 查询步骤数量
    steps_before = sql.Read_task_steps(task_id=cascade_created.id)
    lo.lput(f"  删除前: 任务有 {len(steps_before)} 个步骤", font_color="white")
    
    # 删除任务
    sql.Delete_tasks(cascade_created.id)
    
    # 验证步骤也被删除
    steps_after = sql.Read_task_steps(task_id=cascade_created.id)
    test_case(
        "级联删除",
        len(steps_after) == 0,
        f"删除后: 步骤数量为 {len(steps_after)}（自动级联删除）"
    )
except Exception as e:
    test_case("级联删除", False, str(e))


# ============================================================
# 第八部分: 特殊数据类型处理
# ============================================================
test_section("第八部分: 特殊数据类型处理")

lo.lput("\n【测试 8.1】JSON/JSONB 字段处理", font_color="yellow")
lo.lput("说明: ToolCall 的 arguments 和 response 字段为 JSONB 类型", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  tool = ToolCall(", font_color="gray")
lo.lput("      tool_name='api_call',", font_color="gray")
lo.lput("      arguments={'url': 'https://api.example.com', 'method': 'GET'},", font_color="gray")
lo.lput("      response={'status': 200, 'data': {'key': 'value'}}", font_color="gray")
lo.lput("  )", font_color="gray")

try:
    json_tool = ToolCall(
        task_id=created_task.id,
        step_id=created_steps[0].id,
        tool_name="json_test_tool",
        arguments={
            "method": "POST",
            "url": "https://api.example.com/data",
            "headers": {"Content-Type": "application/json"},
            "body": {"key1": "value1", "key2": [1, 2, 3]}
        },
        response={
            "status_code": 200,
            "data": {
                "result": "success",
                "records": 42,
                "nested": {"field": "value"}
            },
            "timestamp": "2025-11-24T10:00:00Z"
        },
        status=tool_calls_status.success
    )
    created_json_tool = sql.Create_tool_calls(json_tool)
    
    # 读取并验证
    read_tool = sql.Read_tool_calls(id=created_json_tool.id)[0]
    test_case(
        "JSON 字段创建与读取",
        read_tool.arguments.get("method") == "POST" and 
        read_tool.response.get("status_code") == 200,
        "JSON 数据正确存储和读取"
    )
    
    lo.lput(f"  arguments keys: {list(read_tool.arguments.keys())}", font_color="white")
    lo.lput(f"  response keys: {list(read_tool.response.keys())}", font_color="white")
    
    # 清理
    sql.Delete_tool_calls(created_json_tool.id)
except Exception as e:
    test_case("JSON 字段处理", False, str(e))

lo.lput("\n【测试 8.2】可选字段处理", font_color="yellow")
lo.lput("说明: 某些字段可以为 NULL（如 TaskStep.output, ToolCall.step_id）", font_color="white")
lo.lput("代码示例: ", font_color="gray")
lo.lput("  step = TaskStep(task_id=task_id, step_index=1, instruction='...')", font_color="gray")
lo.lput("  # output 字段可选，不提供时为 None", font_color="gray")

try:
    optional_step = TaskStep(
        task_id=created_task.id,
        step_index=99,
        instruction="可选字段测试",
        # output 不提供（默认为 None）
        status=task_steps_status.pending
    )
    created_optional = sql.Create_task_steps(optional_step)
    
    # 读取验证
    read_optional = sql.Read_task_steps(id=created_optional.id)[0]
    test_case(
        "可选字段处理",
        read_optional.output is None or read_optional.output == "",
        f"output 字段允许 None 或空字符串: {repr(read_optional.output)}"
    )
    
    # 清理
    sql.Delete_task_steps(created_optional.id)
except Exception as e:
    test_case("可选字段处理", False, str(e))


# ============================================================
# 第九部分: 错误处理与边界情况
# ============================================================
test_section("第九部分: 错误处理与边界情况")

lo.lput("\n【测试 9.1】查询不存在的记录", font_color="yellow")
lo.lput("说明: 查询不存在的 ID 返回空列表", font_color="white")
lo.lput("代码: tasks = sql.Read_tasks(id=999999)", font_color="gray")

try:
    non_exist = sql.Read_tasks(id=999999)
    test_case(
        "查询不存在的记录",
        len(non_exist) == 0,
        "返回空列表（符合预期）"
    )
except Exception as e:
    test_case("查询不存在的记录", False, str(e))

lo.lput("\n【测试 9.2】更新不存在的记录", font_color="yellow")
lo.lput("说明: 更新不存在的记录返回 False", font_color="white")
lo.lput("代码: success = sql.Update_tasks(999999, title='新标题')", font_color="gray")

try:
    success = sql.Update_tasks(999999, title="新标题")
    test_case(
        "更新不存在的记录",
        success == False,
        "返回 False（符合预期）"
    )
except Exception as e:
    test_case("更新不存在的记录", False, str(e))

lo.lput("\n【测试 9.3】删除不存在的记录", font_color="yellow")
lo.lput("说明: 删除不存在的记录返回 False", font_color="white")
lo.lput("代码: success = sql.Delete_tasks(999999)", font_color="gray")

try:
    success = sql.Delete_tasks(999999)
    test_case(
        "删除不存在的记录",
        success == False,
        "返回 False（符合预期）"
    )
except Exception as e:
    test_case("删除不存在的记录", False, str(e))

lo.lput("\n【测试 9.4】无效字段查询", font_color="yellow")
lo.lput("说明: 使用不在 _allowed_get_fields 中的字段查询会报错", font_color="white")
lo.lput("代码: tasks = sql.Read_tasks(invalid_field='value')  # 会抛出 ValueError", font_color="gray")

try:
    error_raised = False
    try:
        sql.Read_tasks(invalid_field_name="test")
    except ValueError as ve:
        error_raised = True
    
    test_case(
        "无效字段查询",
        error_raised,
        "正确抛出 ValueError 异常"
    )
except Exception as e:
    test_case("无效字段查询", False, str(e))


# ============================================================
# 清理测试数据
# ============================================================
test_section("清理测试数据")

try:
    cleanup_final = cleanup_test_data()
    lo.lput(f"\n清理了 {cleanup_final} 条测试数据", font_color="yellow")
except Exception as e:
    lo.lput(f"\n清理失败: {e}", font_color="red")


# ============================================================
# 测试总结
# ============================================================
test_section("测试总结")

total_tests = test_results["passed"] + test_results["failed"]
pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

lo.lput(f"\n总测试数: {total_tests}", font_color="white")
lo.lput(f"通过: {test_results['passed']}", font_color="green")
lo.lput(f"失败: {test_results['failed']}", font_color="red" if test_results["failed"] > 0 else "green")
lo.lput(f"通过率: {pass_rate:.1f}%", font_color="green_high" if pass_rate == 100 else "yellow")

if test_results["failed"] > 0:
    lo.lput("\n失败的测试:", font_color="red")
    for error in test_results["errors"]:
        lo.lput(f"  - {error}", font_color="red")

lo.lput("\n" + "="*60, font_color="cyan")
if test_results["failed"] == 0:
    lo.lput("✅ 所有测试通过！SQL ORM 模块工作正常！", font_color="green_high")
else:
    lo.lput("⚠️  部分测试失败，请检查错误信息", font_color="yellow")
lo.lput("="*60, font_color="cyan")

lo.lput("\n📚 学习要点总结: ", font_color="cyan")
lo.lput("1. 基本 CRUD: Create_*, Read_*, Update_*, Delete_*", font_color="white")
lo.lput("2. 关系查询: Read_*_With_Relations(relations=[...])", font_color="white")
lo.lput("3. JOIN 查询: Join_{table1}_{table2}(join_condition=...)", font_color="white")
lo.lput("4. 数据导出: model.to_dict_with_relations()", font_color="white")
lo.lput("5. 级联删除: 删除父记录自动删除子记录", font_color="white")
lo.lput("6. 枚举处理: 支持枚举对象和字符串值", font_color="white")
lo.lput("7. JSON 字段: dict 自动转换为 JSONB", font_color="white")

lo.lput("\n💡 更多信息请参考: ", font_color="cyan")
lo.lput("  - mylib/sql/docs/sql.md - SQL 模块使用文档", font_color="gray")
lo.lput("  - mylib/sql/docs/Model.md - 模型系统文档", font_color="gray")
lo.lput("  - mylib/sql/docs/DBRepo.md - 仓库层文档", font_color="gray")
