"""
Agent 状态存储 (StateStore)

用于跨进程共享 Agent 状态，实现 Monitor 页面的实时更新。

存储内容：
1. Agent 状态 (FSM states)
2. 日志流 (Logs)
3. 任务进度 (Task progress)
4. 回调记录 (Callbacks)
5. 统计信息 (Stats)
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# 默认存储路径
DEFAULT_STORE_PATH = Path(__file__).parent.parent.parent / ".agent_state"


@dataclass
class AgentStateSnapshot:
    """Agent 状态快照"""
    agent_id: str
    state: str
    last_event: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class StateStore:
    """
    状态存储器
    
    使用文件系统存储状态，支持跨进程读取。
    
    目录结构：
    .agent_state/
    ├── agents.json       # Agent 状态
    ├── logs.json         # 日志（循环缓冲）
    ├── tasks.json        # 任务进度
    ├── callbacks.json    # 回调记录
    └── stats.json        # 统计信息
    """
    
    def __init__(self, store_path: Path = None):
        self.store_path = Path(store_path) if store_path else DEFAULT_STORE_PATH
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.agents_file = self.store_path / "agents.json"
        self.logs_file = self.store_path / "logs.json"
        self.tasks_file = self.store_path / "tasks.json"
        self.callbacks_file = self.store_path / "callbacks.json"
        self.stats_file = self.store_path / "stats.json"
        
        # 内存缓存
        self._agents_cache: Dict[str, Dict] = {}
        self._logs_cache: List[Dict] = []
        self._tasks_cache: List[Dict] = []
        self._callbacks_cache: List[Dict] = []
        self._stats_cache: Dict = {}
        
        # 最大日志数
        self.max_logs = 500
        self.max_callbacks = 100
        
        # 写锁
        self._lock = threading.Lock()
        
        # 初始化文件
        self._init_files()
        
    def _init_files(self):
        """初始化存储文件"""
        for filepath, default in [
            (self.agents_file, {}),
            (self.logs_file, []),
            (self.tasks_file, []),
            (self.callbacks_file, []),
            (self.stats_file, {"total_tasks": 0, "completed": 0, "failed": 0, "total_time_ms": 0}),
        ]:
            if not filepath.exists():
                self._write_json(filepath, default)
                
    def _read_json(self, filepath: Path) -> Any:
        """读取 JSON 文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
            
    def _write_json(self, filepath: Path, data: Any):
        """写入 JSON 文件"""
        with self._lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
    # ==================== Agent 状态 ====================
    
    def update_agent_state(self, agent_id: str, state: str, event: str = ""):
        """更新 Agent 状态"""
        agents = self._read_json(self.agents_file) or {}
        agents[agent_id] = {
            "agent_id": agent_id,
            "state": state,
            "last_event": event,
            "updated_at": datetime.now().isoformat()
        }
        self._write_json(self.agents_file, agents)
        self._agents_cache = agents
        
    def get_agent_states(self) -> Dict[str, Dict]:
        """获取所有 Agent 状态"""
        return self._read_json(self.agents_file) or {}
    
    def get_agent_state(self, agent_id: str) -> Optional[Dict]:
        """获取单个 Agent 状态"""
        agents = self.get_agent_states()
        return agents.get(agent_id)
    
    # ==================== 日志 ====================
    
    def add_log(self, log_entry: Dict):
        """添加日志条目"""
        logs = self._read_json(self.logs_file) or []
        logs.append({
            **log_entry,
            "timestamp": log_entry.get("timestamp", datetime.now().isoformat())
        })
        # 保持最大数量
        if len(logs) > self.max_logs:
            logs = logs[-self.max_logs:]
        self._write_json(self.logs_file, logs)
        self._logs_cache = logs
        
    def get_logs(self, limit: int = 100, agent_id: str = None, level: str = None) -> List[Dict]:
        """获取日志"""
        logs = self._read_json(self.logs_file) or []
        
        if agent_id:
            logs = [l for l in logs if l.get("agent_id") == agent_id]
        if level:
            logs = [l for l in logs if l.get("level") == level]
            
        return logs[-limit:]
    
    def clear_logs(self):
        """清空日志"""
        self._write_json(self.logs_file, [])
        self._logs_cache = []
        
    # ==================== 任务进度 ====================
    
    def update_tasks(self, tasks: List[Dict]):
        """更新任务列表"""
        self._write_json(self.tasks_file, tasks)
        self._tasks_cache = tasks
        
    def update_task(self, task_id: str, progress: float, status: str):
        """更新单个任务进度"""
        tasks = self._read_json(self.tasks_file) or []
        for task in tasks:
            if task.get("task_id") == task_id or task.get("name") == task_id:
                task["progress"] = progress
                task["status"] = status
                break
        else:
            # 不存在则添加
            tasks.append({
                "task_id": task_id,
                "name": task_id,
                "progress": progress,
                "status": status,
                "type": "sequential"
            })
        self._write_json(self.tasks_file, tasks)
        self._tasks_cache = tasks
        
    def get_tasks(self) -> List[Dict]:
        """获取任务列表"""
        return self._read_json(self.tasks_file) or []
    
    def clear_tasks(self):
        """清空任务"""
        self._write_json(self.tasks_file, [])
        self._tasks_cache = []
        
    # ==================== 回调记录 ====================
    
    def add_callback(self, callback: Dict):
        """添加回调记录"""
        callbacks = self._read_json(self.callbacks_file) or []
        callbacks.append({
            **callback,
            "timestamp": callback.get("timestamp", datetime.now().isoformat())
        })
        if len(callbacks) > self.max_callbacks:
            callbacks = callbacks[-self.max_callbacks:]
        self._write_json(self.callbacks_file, callbacks)
        self._callbacks_cache = callbacks
        
    def get_callbacks(self, limit: int = 50) -> List[Dict]:
        """获取回调记录"""
        callbacks = self._read_json(self.callbacks_file) or []
        return callbacks[-limit:]
    
    def clear_callbacks(self):
        """清空回调"""
        self._write_json(self.callbacks_file, [])
        self._callbacks_cache = []
        
    # ==================== 统计信息 ====================
    
    def update_stats(self, **kwargs):
        """更新统计信息"""
        stats = self._read_json(self.stats_file) or {}
        stats.update(kwargs)
        stats["updated_at"] = datetime.now().isoformat()
        self._write_json(self.stats_file, stats)
        self._stats_cache = stats
        
    def increment_stat(self, key: str, value: int = 1):
        """递增统计值"""
        stats = self._read_json(self.stats_file) or {}
        stats[key] = stats.get(key, 0) + value
        stats["updated_at"] = datetime.now().isoformat()
        self._write_json(self.stats_file, stats)
        self._stats_cache = stats
        
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._read_json(self.stats_file) or {}
    
    # ==================== 会话管理 ====================
    
    def reset_session(self):
        """重置会话（清空所有状态）"""
        self._write_json(self.agents_file, {})
        self._write_json(self.logs_file, [])
        self._write_json(self.tasks_file, [])
        self._write_json(self.callbacks_file, [])
        self._write_json(self.stats_file, {
            "total_tasks": 0, 
            "completed": 0, 
            "failed": 0, 
            "total_time_ms": 0,
            "session_start": datetime.now().isoformat()
        })
        
    def get_all_state(self) -> Dict:
        """获取完整状态（用于监控页面）"""
        return {
            "agents": self.get_agent_states(),
            "logs": self.get_logs(limit=100),
            "tasks": self.get_tasks(),
            "callbacks": self.get_callbacks(),
            "stats": self.get_stats(),
            "timestamp": datetime.now().isoformat()
        }


# 全局状态存储实例
state_store = StateStore()
