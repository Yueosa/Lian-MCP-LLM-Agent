"""
重构后的 Agent 系统使用示例

演示如何使用：
1. FSM 状态机控制
2. AgentLogger 日志记录  
3. CallbackManager 回调机制
4. ExecutorPool 并行执行
"""

import base
import asyncio
from mylib.agent import (
    # Agents
    RAGAgent, PlannerAgent, ExecutorAgent, SummaryAgent,
    
    # FSM
    AgentFSM, fsm_manager,
    
    # Logger
    AgentLogger, LogLevel, logger_manager,
    
    # Callback
    CallbackManager, CallbackRequest, CallbackBuilder, callback_manager,
    
    # Backup
    ContextBackup, context_backup,
    
    # ExecutorPool
    ExecutorPool, ExecutorTask, executor_pool_manager,
)
from mylib.kernel.Lenum.agent import AgentState, AgentTransition, CallbackAction


async def demo_fsm():
    """演示 FSM 状态机"""
    print("\n" + "=" * 50)
    print("🔮 Demo: FSM 状态机")
    print("=" * 50)
    
    # 创建状态机
    fsm = AgentFSM("Demo_Agent")
    
    # 注册状态变化回调
    def on_change(old, new, event):
        print(f"  状态变化: {old.value} --[{event.value}]--> {new.value}")
    
    fsm.on_transition(on_change)
    
    # 模拟状态转换
    print(f"\n当前状态: {fsm.state.value}")
    
    print("\n执行: START_TASK")
    fsm.trigger(AgentTransition.START_TASK)
    
    print("\n执行: LLM_CALL")
    fsm.trigger(AgentTransition.LLM_CALL)
    
    print("\n执行: LLM_DONE")
    fsm.trigger(AgentTransition.LLM_DONE)
    
    print("\n执行: TASK_DONE")
    fsm.trigger(AgentTransition.TASK_DONE)
    
    # 查看历史
    print(f"\n转换历史: {len(fsm.history)} 条记录")


async def demo_logger():
    """演示 Logger 日志"""
    print("\n" + "=" * 50)
    print("📋 Demo: AgentLogger")
    print("=" * 50)
    
    logger = AgentLogger("Demo_Logger")
    
    logger.system("系统启动")
    logger.agent("Agent 初始化完成")
    logger.llm_request(messages_count=5, temperature=0.7)
    logger.llm_response(length=1234, preview="这是一段示例响应...")
    logger.tool_call("search_files", {"pattern": "*.py"})
    logger.tool_result("search_files", {"files": ["a.py", "b.py"]})
    logger.state_change("IDLE", "PROCESSING", "START_TASK")
    logger.error("这是一个错误示例")
    
    print(f"\n日志缓冲区: {len(logger.buffer)} 条记录")


async def demo_callback():
    """演示 Callback 回调"""
    print("\n" + "=" * 50)
    print("🔄 Demo: CallbackManager")
    print("=" * 50)
    
    # 创建管理器
    manager = CallbackManager()
    
    # 注册 Planner 的处理器
    async def planner_handler(request: CallbackRequest):
        print(f"  Planner 收到回调: {request.action.value}")
        print(f"  原因: {request.reason}")
        
        from mylib.agent.callback import CallbackResponse
        return CallbackResponse(
            request_id=request.request_id,
            status="ACCEPTED",
            source_agent="Planner",
            data={"new_plan": "重新规划的结果"},
            message="已接受重新规划请求"
        )
    
    manager.register_handler("Planner", planner_handler)
    
    # 发送回调
    print("\nExecutor 请求 Planner 重新规划...")
    
    request = CallbackBuilder() \
        .from_agent("Executor") \
        .to_agent("Planner") \
        .action(CallbackAction.REPLAN) \
        .reason("工具调用失败，需要替代方案") \
        .context(failed_step=3, error="Permission denied") \
        .build()
    
    response = await manager.send_callback(request)
    
    print(f"\n响应状态: {response.status}")
    print(f"响应消息: {response.message}")
    print(f"响应数据: {response.data}")


async def demo_backup():
    """演示 Backup 备份"""
    print("\n" + "=" * 50)
    print("💾 Demo: ContextBackup")
    print("=" * 50)
    
    backup = ContextBackup("./demo_backups")
    
    # 保存上下文
    session_id = "demo_session_001"
    
    backup.save_context(
        session_id=session_id,
        agent_id="Executor_001",
        context={
            "messages": [
                {"role": "user", "content": "帮我搜索文件"},
                {"role": "assistant", "content": "正在搜索..."}
            ],
            "current_step": 2
        }
    )
    
    backup.save_plan(
        session_id=session_id,
        agent_id="Planner_001",
        plan={
            "goal": "搜索并分析代码",
            "steps": [
                {"step_id": 1, "action": "search"},
                {"step_id": 2, "action": "analyze"}
            ]
        }
    )
    
    # 读取备份
    ctx = backup.load_latest_context(session_id, "Executor_001")
    print(f"\n恢复的上下文: {ctx}")
    
    # 统计
    stats = backup.get_stats()
    print(f"\n备份统计: {stats}")


async def demo_executor_pool():
    """演示 ExecutorPool 并行执行"""
    print("\n" + "=" * 50)
    print("⚡ Demo: ExecutorPool")
    print("=" * 50)
    
    pool = ExecutorPool(max_workers=3)
    
    # 模拟执行函数
    async def mock_executor(task: ExecutorTask, context: dict):
        print(f"  执行任务: {task.task_id} - {task.action}")
        await asyncio.sleep(0.5)  # 模拟执行时间
        return f"Result of {task.action}"
    
    # 添加任务（混合依赖）
    pool.add_task("task_1", 1, "search_files", {"pattern": "*.py"})
    pool.add_task("task_2", 2, "read_file", {"path": "a.py"}, dependencies=[1])
    pool.add_task("task_3", 3, "read_file", {"path": "b.py"}, dependencies=[1])
    pool.add_task("task_4", 4, "analyze_code", {}, dependencies=[2, 3])
    
    # 设置进度回调
    def on_progress(completed, total, current):
        print(f"  进度: {completed}/{total} - {current}")
    
    pool.on_progress(on_progress)
    
    # 执行
    print("\n开始执行...")
    results = await pool.execute_all(mock_executor)
    
    print(f"\n执行结果: {results}")
    print(f"统计: {pool.get_stats()}")


async def main():
    """运行所有演示"""
    print("🔮 Lian-MCP-LLM-Agent 重构模块演示")
    print("=" * 50)
    
    await demo_fsm()
    await demo_logger()
    await demo_callback()
    await demo_backup()
    await demo_executor_pool()
    
    print("\n" + "=" * 50)
    print("✅ 所有演示完成!")
    print("=" * 50)
    
    # 清理演示备份
    import shutil
    import os
    if os.path.exists("./demo_backups"):
        shutil.rmtree("./demo_backups")
        print("已清理演示备份目录")


if __name__ == "__main__":
    asyncio.run(main())
