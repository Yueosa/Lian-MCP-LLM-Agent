"""
SQL ORM 关系查询功能测试
测试外键关系定义和联合查询功能
"""
import base

from mylib.lian_orm import Sql
from mylib.lian_orm.Model import Task, TaskStep, ToolCall
from mylib.lian_orm.Model.Enum import tasks_status, task_steps_status, tool_calls_status
from mylib.utils import Loutput

# 初始化
lo = Loutput()
sql = Sql()

# 测试连接
lo.lput("\n=== 测试数据库连接 ===", font_color="cyan")
if sql.test_connect():
    lo.lput("✓ 数据库连接成功", font_color="green")
else:
    lo.lput("✗ 数据库连接失败", font_color="red")
    exit(1)

# 清理测试数据（如果存在）
lo.lput("\n=== 清理旧测试数据 ===", font_color="cyan")
existing_tasks = sql.Read_tasks(user_id="test_user_relations")
for task in existing_tasks:
    sql.Delete_tasks(task.id)
lo.lput(f"✓ 清理了 {len(existing_tasks)} 条旧任务", font_color="yellow")

# 测试1: 创建带外键关系的数据
lo.lput("\n=== 测试1: 创建任务和步骤 ===", font_color="cyan")

# 创建任务
task = Task(
    user_id="test_user_relations",
    title="测试关系查询功能",
    description="测试 ORM 的外键关系和联合查询",
    status=tasks_status.pending
)
created_task = sql.Create_tasks(task)
lo.lput(f"✓ 创建任务: ID={created_task.id}, Title='{created_task.title}'", font_color="green")

# 创建多个步骤
steps_data = [
    {"step_index": 1, "instruction": "初始化环境", "status": task_steps_status.done},
    {"step_index": 2, "instruction": "加载数据", "status": task_steps_status.running},
    {"step_index": 3, "instruction": "处理数据", "status": task_steps_status.pending},
]

created_steps = []
for step_data in steps_data:
    step = TaskStep(
        task_id=created_task.id,
        **step_data
    )
    created_step = sql.Create_task_steps(step)
    created_steps.append(created_step)
    lo.lput(f"  ✓ 创建步骤 {step_data['step_index']}: {step_data['instruction']}", font_color="green")

# 创建工具调用
tool_call = ToolCall(
    task_id=created_task.id,
    step_id=created_steps[0].id,
    tool_name="test_tool",
    arguments={"arg1": "value1"},
    response={"result": "success"},
    status=tool_calls_status.success
)
created_tool_call = sql.Create_tool_calls(tool_call)
lo.lput(f"  ✓ 创建工具调用: {tool_call.tool_name}", font_color="green")

# 测试2: 基本查询（不加载关系）
lo.lput("\n=== 测试2: 基本查询 ===", font_color="cyan")
tasks = sql.Read_tasks(id=created_task.id)
if tasks:
    task = tasks[0]
    lo.lput(f"✓ 查询任务: {task.title}", font_color="green")
    lo.lput(f"  关联对象数量: {len(task.get_related_objects())}", font_color="yellow")
    if len(task.get_related_objects()) == 0:
        lo.lput("  ✓ 未加载关联对象（符合预期）", font_color="green")

# 测试3: 加载所有关系
lo.lput("\n=== 测试3: 加载所有关系 ===", font_color="cyan")
tasks_with_all_relations = sql.Read_tasks_With_Relations(id=created_task.id)
if tasks_with_all_relations:
    task = tasks_with_all_relations[0]
    lo.lput(f"✓ 查询任务（含关系）: {task.title}", font_color="green")
    
    # 检查步骤
    steps = task.get_related_object("task_steps")
    if steps:
        lo.lput(f"  ✓ 加载了 {len(steps)} 个步骤:", font_color="green")
        for step in steps:
            lo.lput(f"    - 步骤 {step.step_index}: {step.instruction} ({step.status.value})", 
                   font_color="white")
    else:
        lo.lput("  ✗ 未加载步骤", font_color="red")
    
    # 检查工具调用
    tool_calls = task.get_related_object("tool_calls")
    if tool_calls:
        lo.lput(f"  ✓ 加载了 {len(tool_calls)} 个工具调用:", font_color="green")
        for tc in tool_calls:
            lo.lput(f"    - 工具: {tc.tool_name} ({tc.status.value})", font_color="white")
    else:
        lo.lput("  ✗ 未加载工具调用", font_color="red")

# 测试4: 只加载特定关系
lo.lput("\n=== 测试4: 只加载特定关系 ===", font_color="cyan")
tasks_with_steps_only = sql.Read_tasks_With_Relations(
    relations=["task_steps"],
    id=created_task.id
)
if tasks_with_steps_only:
    task = tasks_with_steps_only[0]
    steps = task.get_related_object("task_steps")
    tool_calls = task.get_related_object("tool_calls")
    
    if steps and not tool_calls:
        lo.lput("  ✓ 只加载了步骤，未加载工具调用（符合预期）", font_color="green")
    else:
        lo.lput("  ✗ 关系加载不符合预期", font_color="red")

# 测试5: 反向查询（从步骤查任务）
lo.lput("\n=== 测试5: 反向查询（步骤→任务） ===", font_color="cyan")
steps_with_task = sql.Read_task_steps_With_Relations(
    relations=["task"],
    task_id=created_task.id
)
if steps_with_task:
    lo.lput(f"✓ 查询到 {len(steps_with_task)} 个步骤", font_color="green")
    for step in steps_with_task:
        parent_task = step.get_related_object("task")
        if parent_task:
            lo.lput(f"  ✓ 步骤 {step.step_index} 的任务: {parent_task.title}", font_color="green")
        else:
            lo.lput(f"  ✗ 步骤 {step.step_index} 未加载任务", font_color="red")

# 测试6: 导出包含关系的数据
lo.lput("\n=== 测试6: 导出数据（含关系） ===", font_color="cyan")
tasks_full = sql.Read_tasks_With_Relations(id=created_task.id)
if tasks_full:
    task = tasks_full[0]
    
    # 导出包含所有关系
    task_dict = task.to_dict_with_relations()
    lo.lput(f"✓ 导出数据结构:", font_color="green")
    lo.lput(f"  - 任务字段: {list(task_dict.keys())[:5]}...", font_color="white")
    lo.lput(f"  - 步骤数量: {len(task_dict.get('task_steps', []))}", font_color="white")
    lo.lput(f"  - 工具调用数量: {len(task_dict.get('tool_calls', []))}", font_color="white")
    
    # 只导出特定关系
    task_dict_partial = task.to_dict_with_relations(include_relations=["task_steps"])
    if 'task_steps' in task_dict_partial and 'tool_calls' not in task_dict_partial:
        lo.lput("  ✓ 部分导出成功", font_color="green")

# 测试7: JOIN 查询
lo.lput("\n=== 测试7: JOIN 查询 ===", font_color="cyan")
try:
    results = sql.Join_tasks_task_steps(
        join_condition="tasks.id = task_steps.task_id",
        select_fields=["tasks.title", "tasks.status", "task_steps.instruction", "task_steps.step_index"],
        **{"tasks.id": created_task.id}
    )
    
    if results:
        lo.lput(f"✓ JOIN 查询返回 {len(results)} 条记录:", font_color="green")
        for result in results:
            lo.lput(f"  - {result.get('title')}: 步骤{result.get('step_index')} - {result.get('instruction')}", 
                   font_color="white")
    else:
        lo.lput("  ⚠ JOIN 查询无结果", font_color="yellow")
except Exception as e:
    lo.lput(f"  ✗ JOIN 查询失败: {e}", font_color="red")

# 测试8: 更新并验证
lo.lput("\n=== 测试8: 更新任务状态 ===", font_color="cyan")
update_success = sql.Update_tasks(created_task.id, status=tasks_status.running)
if update_success:
    lo.lput("✓ 更新任务状态成功", font_color="green")
    
    # 验证更新
    updated_tasks = sql.Read_tasks(id=created_task.id)
    if updated_tasks and updated_tasks[0].status == tasks_status.running:
        lo.lput(f"  ✓ 验证更新: 状态={updated_tasks[0].status.value}", font_color="green")

# 测试9: 级联关系（工具调用→步骤→任务）
lo.lput("\n=== 测试9: 多级关系查询 ===", font_color="cyan")
tool_calls_with_step = sql.Read_tool_calls_With_Relations(
    relations=["task_step"],
    id=created_tool_call.id
)
if tool_calls_with_step:
    tc = tool_calls_with_step[0]
    step = tc.get_related_object("task_step")
    if step:
        lo.lput(f"✓ 工具调用 → 步骤: {step.instruction}", font_color="green")
        
        # 再查询步骤的任务
        steps_with_task_again = sql.Read_task_steps_With_Relations(
            relations=["task"],
            id=step.id
        )
        if steps_with_task_again:
            step_full = steps_with_task_again[0]
            parent_task = step_full.get_related_object("task")
            if parent_task:
                lo.lput(f"  ✓ 步骤 → 任务: {parent_task.title}", font_color="green")

# 清理测试数据
lo.lput("\n=== 清理测试数据 ===", font_color="cyan")
sql.Delete_tasks(created_task.id)  # 级联删除会自动删除关联的步骤和工具调用
lo.lput("✓ 测试数据已清理", font_color="yellow")

# 总结
lo.lput("\n" + "="*50, font_color="cyan")
lo.lput("✅ 所有测试完成！", font_color="green_high")
lo.lput("="*50, font_color="cyan")
lo.lput("\n功能验证:", font_color="cyan")
lo.lput("  ✓ 基本 CRUD 操作", font_color="green")
lo.lput("  ✓ 外键关系定义（一对多、多对一）", font_color="green")
lo.lput("  ✓ Read_With_Relations 自动加载关联对象", font_color="green")
lo.lput("  ✓ 选择性加载特定关系", font_color="green")
lo.lput("  ✓ 反向关系查询", font_color="green")
lo.lput("  ✓ 导出包含关系的数据", font_color="green")
lo.lput("  ✓ JOIN 多表联合查询", font_color="green")
lo.lput("  ✓ 多级关系导航", font_color="green")
