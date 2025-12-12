import asyncio
from typing import Callable, Optional

from mylib.agent.demo_agent import HistorySummaryAgent, PlannerAgent, ExecutorAgent
from mylib.llm.llm_client import MCPClient
from mylib.core.pipeline import TaskPipeline
from mylib.lian_orm import TasksStatus, TaskStepsStatus


async def run_llm_mode(user_input: str, *, agent: Optional[HistorySummaryAgent] = None) -> str:
    """LLM 模式：写入记忆、检索、总结并回答。"""
    agent = agent or HistorySummaryAgent()
    reply = await agent.handle(user_input)
    return reply


def run_mcp_mode(user_input: str, *, client: Optional[MCPClient] = None) -> str:
    """MCP 模式：调用工具，记录 tool_calls/历史。"""
    client = client or MCPClient()
    return client.process_user_request(user_input)


async def run_agent_mode(
    user_input: str,
    *,
    planner: Optional[PlannerAgent] = None,
    executor: Optional[ExecutorAgent] = None,
    pipeline: Optional[TaskPipeline] = None,
    on_step: Optional[Callable[[str], None]] = None,
) -> str:
    """Agent 模式：Planner → Executor 串行执行并落库。

    Returns dict for richer UI:
    {
        "task_id": int,
        "plan_text": str,
        "steps": [str],
        "results": [str],
        "final": str,
    }
    """
    planner = planner or PlannerAgent()
    executor = executor or ExecutorAgent()
    pipeline = pipeline or TaskPipeline()
    mcp_client = MCPClient()

    task_id = await pipeline.create_task(title="agent_session", description=user_input)
    plan_text = await planner.handle(user_input)
    steps = PlannerAgent.parse_steps(plan_text)
    if not steps:
        steps = [user_input]

    step_ids = await pipeline.add_steps(task_id, steps)

    if on_step:
        on_step("planning done")

    results = []
    step_ids_out = []
    tool_calls: list = []  # 预留：未来可注入工具调用记录
    memory_logs: list = []

    # 收集执行阶段的记忆写入 ID
    orig_save = executor.save_memory

    async def wrapped_save(msg: str, rep: str):
        ids = await orig_save(msg, rep)
        if ids:
            memory_logs.extend([i for i in ids if i is not None])
        return ids

    executor.save_memory = wrapped_save  # type: ignore
    for step_id, instr in zip(step_ids, steps):
        try:
            # 使用 MCP 客户端处理指令，带工具调用循环
            result = mcp_client.process_user_request(instr)
            results.append(result)
            step_ids_out.append(step_id)
            await pipeline.mark_step(step_id, output=result, status=TaskStepsStatus.DONE)
            if on_step:
                on_step(f"step {step_id} done")
        except Exception as exc:  # noqa: BLE001
            await pipeline.mark_step(step_id, output=str(exc), status=TaskStepsStatus.FAILED)
            await pipeline.mark_task(task_id, status=TasksStatus.FAILED)
            raise

    await pipeline.mark_task(task_id, status=TasksStatus.DONE)
    final = "\n".join(results)
    return {
        "task_id": task_id,
        "step_ids": step_ids_out,
        "plan_text": plan_text,
        "steps": steps,
        "results": results,
        "final": final,
        "tool_calls": tool_calls,
        "memory_logs": memory_logs,
    }
