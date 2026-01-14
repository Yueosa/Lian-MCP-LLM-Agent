"""
Executor Pool (执行器池)

支持多个 Executor 实例并行执行任务。

功能：
1. 管理多个 Executor 实例
2. 按依赖关系拓扑排序执行
3. 支持 sequential/parallel/mixed 执行模式
4. 进度追踪和结果聚合
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Awaitable
from enum import Enum

from mylib.kernel.Lenum.agent import TaskType, RetryPolicy
from mylib.kit.Loutput import Loutput, FontColor8


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutorTask:
    """执行任务"""
    task_id: str
    step_id: int
    action: str
    input_data: Dict[str, Any]
    dependencies: List[int] = field(default_factory=list)
    retry_policy: RetryPolicy = RetryPolicy.RETRY_TWICE
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    executor_id: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "step_id": self.step_id,
            "action": self.action,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "executor_id": self.executor_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


# 任务执行器函数类型
TaskExecutorFunc = Callable[[ExecutorTask, Dict[str, Any]], Awaitable[Any]]


class ExecutorPool:
    """
    执行器池
    
    管理多个 Executor 实例，支持并行执行。
    
    使用示例:
    ```python
    pool = ExecutorPool(max_workers=4)
    
    # 定义执行函数
    async def execute_step(task: ExecutorTask, context: Dict) -> Any:
        # 调用 MCP 工具
        result = await mcp_client.call_tool(task.action, task.input_data)
        return result
    
    # 添加任务
    pool.add_task("task_1", 1, "search_files", {"pattern": "*.py"})
    pool.add_task("task_2", 2, "read_file", {"path": "..."}, dependencies=[1])
    pool.add_task("task_3", 3, "read_file", {"path": "..."}, dependencies=[1])
    
    # 执行（自动处理依赖）
    results = await pool.execute_all(execute_step)
    ```
    """
    
    def __init__(self, max_workers: int = 4):
        """
        初始化执行器池
        
        :param max_workers: 最大并行工作数
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, ExecutorTask] = {}
        self.step_to_task: Dict[int, str] = {}  # step_id -> task_id 映射
        self.results: Dict[int, Any] = {}  # step_id -> result 映射
        self.lo = Loutput()
        
        # 执行统计
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "total_time_ms": 0
        }
        
        # 进度回调
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        
    def on_progress(self, callback: Callable[[int, int, str], None]):
        """设置进度回调: callback(completed, total, current_task)"""
        self._progress_callback = callback
        
    def add_task(
        self,
        task_id: str,
        step_id: int,
        action: str,
        input_data: Dict[str, Any],
        dependencies: List[int] = None,
        retry_policy: RetryPolicy = RetryPolicy.RETRY_TWICE
    ):
        """
        添加执行任务
        
        :param task_id: 任务 ID
        :param step_id: 步骤 ID
        :param action: 动作/工具名
        :param input_data: 输入数据
        :param dependencies: 依赖的步骤 ID 列表
        :param retry_policy: 重试策略
        """
        task = ExecutorTask(
            task_id=task_id,
            step_id=step_id,
            action=action,
            input_data=input_data,
            dependencies=dependencies or [],
            retry_policy=retry_policy
        )
        self.tasks[task_id] = task
        self.step_to_task[step_id] = task_id
        self.stats["total_tasks"] += 1
        
    def add_tasks_from_plan(self, plan: Dict):
        """
        从 Planner 生成的计划中批量添加任务
        
        :param plan: Planner 返回的执行计划
        """
        steps = plan.get("steps", [])
        task_type = TaskType(plan.get("task_type", "sequential"))
        
        for step in steps:
            step_id = step.get("step_id", 0)
            action = step.get("action", "")
            input_data = step.get("input", {})
            
            # 根据任务类型确定依赖
            dependencies = []
            if task_type == TaskType.SEQUENTIAL:
                # 顺序执行：依赖前一个步骤
                if step_id > 1:
                    dependencies = [step_id - 1]
            elif task_type == TaskType.MIXED:
                # 混合：使用计划中指定的依赖
                dependencies = step.get("dependencies", [])
            # PARALLEL: 无依赖
            
            retry_policy_str = step.get("retry_policy", plan.get("retry_policy", "retry_twice"))
            retry_policy = RetryPolicy(retry_policy_str)
            
            self.add_task(
                task_id=f"step_{step_id}",
                step_id=step_id,
                action=action,
                input_data=input_data,
                dependencies=dependencies,
                retry_policy=retry_policy
            )
            
    def _topological_sort(self) -> List[List[str]]:
        """
        按依赖关系进行拓扑排序，返回分层的任务组
        
        返回: [[无依赖任务], [依赖第一层的任务], ...]
        """
        # 计算入度
        in_degree = {task_id: 0 for task_id in self.tasks}
        for task in self.tasks.values():
            for dep_step in task.dependencies:
                dep_task_id = self.step_to_task.get(dep_step)
                if dep_task_id:
                    in_degree[task.task_id] += 1
                    
        # 分层
        layers = []
        remaining = set(self.tasks.keys())
        
        while remaining:
            # 找出入度为 0 的任务
            current_layer = [
                task_id for task_id in remaining 
                if in_degree[task_id] == 0
            ]
            
            if not current_layer:
                # 存在循环依赖
                self.lo.lput(
                    f"[ExecutorPool] Warning: Circular dependency detected!",
                    font_color=FontColor8.RED
                )
                # 强制添加剩余任务
                current_layer = list(remaining)
                
            layers.append(current_layer)
            
            # 移除已处理的任务，更新入度
            for task_id in current_layer:
                remaining.discard(task_id)
                task = self.tasks[task_id]
                # 更新依赖此任务的其他任务的入度
                for other_task in self.tasks.values():
                    if task.step_id in other_task.dependencies:
                        in_degree[other_task.task_id] -= 1
                        
        return layers
    
    async def _execute_task(
        self, 
        task: ExecutorTask, 
        executor_func: TaskExecutorFunc,
        context: Dict[str, Any]
    ):
        """执行单个任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        
        # 获取依赖结果
        dep_results = {}
        for dep_step in task.dependencies:
            if dep_step in self.results:
                dep_results[f"step_{dep_step}_result"] = self.results[dep_step]
                
        # 合并到输入数据
        task_context = {**context, "dependency_results": dep_results}
        
        # 重试逻辑
        max_retries = {
            RetryPolicy.NO_RETRY: 1,
            RetryPolicy.RETRY_ONCE: 2,
            RetryPolicy.RETRY_TWICE: 3,
            RetryPolicy.RETRY_INFINITE: 10  # 限制为10次
        }.get(task.retry_policy, 3)
        
        last_error = None
        for attempt in range(max_retries):
            try:
                self.lo.lput(
                    f"[ExecutorPool] Executing {task.task_id}: {task.action} (attempt {attempt + 1})",
                    font_color=FontColor8.CYAN
                )
                
                result = await executor_func(task, task_context)
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                self.results[task.step_id] = result
                self.stats["completed"] += 1
                
                self.lo.lput(
                    f"[ExecutorPool] {task.task_id} completed successfully",
                    font_color=FontColor8.GREEN
                )
                return
                
            except Exception as e:
                last_error = str(e)
                self.lo.lput(
                    f"[ExecutorPool] {task.task_id} failed (attempt {attempt + 1}): {e}",
                    font_color=FontColor8.YELLOW
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # 递增延迟
                    
        # 所有重试失败
        task.status = TaskStatus.FAILED
        task.error = last_error or "Unknown error"
        task.completed_at = datetime.now().isoformat()
        self.stats["failed"] += 1
        
        self.lo.lput(
            f"[ExecutorPool] {task.task_id} failed after {max_retries} attempts: {last_error}",
            font_color=FontColor8.RED
        )
        
    async def execute_all(
        self, 
        executor_func: TaskExecutorFunc,
        context: Dict[str, Any] = None
    ) -> Dict[int, Any]:
        """
        执行所有任务
        
        :param executor_func: 任务执行函数
        :param context: 共享上下文
        :return: step_id -> result 的映射
        """
        context = context or {}
        start_time = datetime.now()
        
        # 拓扑排序
        layers = self._topological_sort()
        
        self.lo.lput(
            f"[ExecutorPool] Starting execution: {len(self.tasks)} tasks in {len(layers)} layers",
            font_color=FontColor8.MAGENTA
        )
        
        # 按层执行
        for layer_idx, layer in enumerate(layers):
            self.lo.lput(
                f"[ExecutorPool] Layer {layer_idx + 1}/{len(layers)}: {len(layer)} tasks",
                font_color=FontColor8.BLUE
            )
            
            # 检查是否有前置失败
            tasks_to_run = []
            for task_id in layer:
                task = self.tasks[task_id]
                
                # 检查依赖是否都成功
                deps_ok = True
                for dep_step in task.dependencies:
                    dep_task_id = self.step_to_task.get(dep_step)
                    if dep_task_id:
                        dep_task = self.tasks[dep_task_id]
                        if dep_task.status == TaskStatus.FAILED:
                            deps_ok = False
                            break
                            
                if deps_ok:
                    tasks_to_run.append(task)
                else:
                    task.status = TaskStatus.SKIPPED
                    task.error = "Dependency failed"
                    self.stats["skipped"] += 1
                    self.lo.lput(
                        f"[ExecutorPool] Skipped {task_id} due to dependency failure",
                        font_color=FontColor8.YELLOW
                    )
            
            # 并行执行本层任务（限制并发数）
            semaphore = asyncio.Semaphore(self.max_workers)
            
            async def run_with_semaphore(task):
                async with semaphore:
                    await self._execute_task(task, executor_func, context)
                    # 进度回调
                    if self._progress_callback:
                        completed = self.stats["completed"] + self.stats["failed"] + self.stats["skipped"]
                        self._progress_callback(completed, self.stats["total_tasks"], task.task_id)
            
            await asyncio.gather(*[run_with_semaphore(t) for t in tasks_to_run])
        
        # 统计执行时间
        end_time = datetime.now()
        self.stats["total_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        self.lo.lput(
            f"[ExecutorPool] Execution completed: {self.stats['completed']} success, "
            f"{self.stats['failed']} failed, {self.stats['skipped']} skipped "
            f"({self.stats['total_time_ms']}ms)",
            font_color=FontColor8.MAGENTA
        )
        
        return self.results
    
    def get_all_results(self) -> List[Dict]:
        """获取所有任务结果"""
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_stats(self) -> Dict:
        """获取执行统计"""
        return self.stats
    
    def reset(self):
        """重置执行器池"""
        self.tasks.clear()
        self.step_to_task.clear()
        self.results.clear()
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "total_time_ms": 0
        }


class ExecutorPoolManager:
    """执行器池管理器"""
    
    def __init__(self):
        self.pools: Dict[str, ExecutorPool] = {}
        
    def create_pool(self, session_id: str, max_workers: int = 4) -> ExecutorPool:
        """创建执行器池"""
        pool = ExecutorPool(max_workers=max_workers)
        self.pools[session_id] = pool
        return pool
        
    def get_pool(self, session_id: str) -> Optional[ExecutorPool]:
        """获取执行器池"""
        return self.pools.get(session_id)
        
    def remove_pool(self, session_id: str):
        """移除执行器池"""
        if session_id in self.pools:
            del self.pools[session_id]
            
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有池的统计"""
        return {sid: pool.get_stats() for sid, pool in self.pools.items()}


# 全局执行器池管理器
executor_pool_manager = ExecutorPoolManager()
