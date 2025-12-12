from pathlib import Path
from typing import Dict, Any, List

import toml

from .base import BaseAgent as Agent


def _safe_load_toml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return toml.load(path)
    except Exception:
        return {}


class HistorySummaryAgent(Agent):
    """Specialized agent that summarizes retrieved memories."""

    def __init__(self, *, config_path: str | None = None) -> None:
        super().__init__(identity="你是一个RAG生成专家", config_path=config_path)
        base_dir = Path(__file__).resolve().parent
        self.prompt_conf = _safe_load_toml(base_dir / "prompt" / "history_summary.toml")
        self.schema_conf = _safe_load_toml(base_dir / "schema" / "history_summary.toml")

    def build_prompt(self, user_message: str, memories):
        memory_text = self._format_memories(memories)
        system_prompt = self.prompt_conf.get("prompt", {}).get(
            "system", "你是一个RAG总结专家，输出简洁、事实性的总结。"
        )
        user_template = self.prompt_conf.get("prompt", {}).get(
            "user_template",
            "请基于下列记忆生成总结：\n{{MEMORIES}}\n\n用户问题：{{QUERY}}\n\n输出格式：{{RESPONSE_TEMPLATE}}",
        )
        response_template = self.schema_conf.get("response", {}).get(
            "template", "以下是对基于记忆检索到的内容的总结: {{TEXT}}",
        )

        user_content = (
            user_template
            .replace("{{MEMORIES}}", memory_text)
            .replace("{{QUERY}}", user_message)
            .replace("{{RESPONSE_TEMPLATE}}", response_template)
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]


class PlannerAgent(Agent):
    """生成步骤规划的 Agent。"""

    def __init__(self, *, config_path: str | None = None) -> None:
        super().__init__(identity="你是一个任务规划专家", config_path=config_path)
        base_dir = Path(__file__).resolve().parent
        self.prompt_conf = _safe_load_toml(base_dir / "prompt" / "planner.toml")
        self.schema_conf = _safe_load_toml(base_dir / "schema" / "planner.toml")

    def build_prompt(self, user_message: str, memories):
        system_prompt = self.prompt_conf.get("prompt", {}).get(
            "system", "你是一个任务规划专家，请将目标拆解为 3-6 步。"
        )
        user_template = self.prompt_conf.get("prompt", {}).get(
            "user_template", "用户需求：{{QUERY}}\n请输出步骤列表，每行一个动作。",
        )
        response_template = self.schema_conf.get("response", {}).get(
            "template", "步骤规划:\n{{STEPS}}",
        )

        user_content = (
            user_template
            .replace("{{QUERY}}", user_message)
            .replace("{{STEPS}}", "")
            .replace("{{RESPONSE_TEMPLATE}}", response_template)
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def parse_steps(plan_text: str) -> List[str]:
        lines = [l.strip(" -\t") for l in plan_text.splitlines()]
        return [l for l in lines if l]


class ExecutorAgent(Agent):
    """执行单步指令的 Agent。"""

    def __init__(self, *, config_path: str | None = None) -> None:
        super().__init__(identity="你是一个执行型智能体", config_path=config_path)
        base_dir = Path(__file__).resolve().parent
        self.prompt_conf = _safe_load_toml(base_dir / "prompt" / "executor.toml")
        self.schema_conf = _safe_load_toml(base_dir / "schema" / "executor.toml")

    def build_prompt(self, user_message: str, memories):
        system_prompt = self.prompt_conf.get("prompt", {}).get(
            "system", "你是一个执行型智能体，按指令完成任务并输出简洁结果。"
        )
        user_template = self.prompt_conf.get("prompt", {}).get(
            "user_template", "执行指令：{{INSTRUCTION}}\n请给出完成情况或下一步建议。",
        )
        response_template = self.schema_conf.get("response", {}).get(
            "template", "执行结果: {{TEXT}}",
        )

        user_content = (
            user_template
            .replace("{{INSTRUCTION}}", user_message)
            .replace("{{RESPONSE_TEMPLATE}}", response_template)
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
