from .sql import Sql

from .Model.Enum import tasks_status

from mylib import Loutput

lo = Loutput()
sql = Sql()

# 输出支持的表名
# lo.lput(f"\n支持的表名: \n{sql.get_supported_tables()}", font_color="cyan")

# 查询表的字段信息
# fields_info = sql.get_table_fields("tasks")
# lo.lput(f"\ntasks表字段信息: \n{fields_info}", font_color="magenta")

# 获取表创建SQL
# create_sql = sql.get_table_create_sql("tasks")
# lo.lput(f"\n创建tasks表的SQL: \n{create_sql}", font_color="green")

# 创建记录
from mylib.sql.Model.Tasks import Task
new_task = Task(
    user_id="lian", title="测试", description="测试枚举", status=tasks_status.pending
)
created_task = sql.Create_tasks(new_task)
lo.lput(f"\n创建的任务: \n{created_task}", font_color="blue")

# 查询记录
# 1. 根据ID查询单条记录
task_by_id = sql.Read_tasks(id=created_task.id)
lo.lput(f"\n根据ID查询: \n{task_by_id}", font_color="cyan")

# 2. 根据其他字段查询多条记录
tasks_by_user = sql.Read_tasks(user_id="lian")
lo.lput(f"\n用户的所有任务: \n{tasks_by_user}", font_color="cyan")

# 3. 更新记录
update_success = sql.Update_tasks(created_task.id, status="done")
lo.lput(f"\n更新成功: \n{update_success}", font_color="green_high") if update_success else None

# 4. 根据ID查询单条记录
task_by_id = sql.Read_tasks(id=created_task.id)
lo.lput(f"\n根据ID查询: \n{task_by_id}", font_color="cyan")

# 5. 删除记录
delete_success = sql.Delete_tasks(id=created_task.id)
lo.lput(f"\n删除成功: \n{delete_success}", font_color="black") if delete_success else None

