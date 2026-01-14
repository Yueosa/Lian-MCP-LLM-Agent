"""
上下文备份系统 (ContextBackup)

防止因请求过多/截断机制丢失关键信息。

功能：
1. 自动保存上下文快照
2. 支持按会话/Agent 检索
3. 循环清理过期备份
4. JSON 格式存储，易于调试
"""

import os
import json
import glob
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from mylib.kit.Loutput import Loutput, FontColor8


@dataclass
class BackupMetadata:
    """备份元数据"""
    session_id: str
    agent_id: str
    backup_type: str  # context, message, plan, result
    timestamp: str
    size_bytes: int
    description: str = ""


class ContextBackup:
    """
    上下文备份管理器
    
    防止因请求过多/截断机制丢失关键信息。
    
    使用示例:
    ```python
    backup = ContextBackup("./backups")
    
    # 保存上下文
    filepath = backup.save_context(
        session_id="sess_abc123",
        agent_id="Executor_001",
        context={"messages": [...], "tools": [...]}
    )
    
    # 加载最新上下文
    ctx = backup.load_latest_context("sess_abc123", "Executor_001")
    
    # 清理过期备份
    backup.cleanup(max_age_hours=24)
    ```
    """
    
    def __init__(self, backup_dir: str = "./backups"):
        """
        初始化备份管理器
        
        :param backup_dir: 备份目录
        """
        self.backup_dir = backup_dir
        self.lo = Loutput()
        self._ensure_dir()
        
    def _ensure_dir(self):
        """确保备份目录存在"""
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def _generate_filename(self, session_id: str, agent_id: str, backup_type: str) -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"{session_id}_{agent_id}_{backup_type}_{timestamp}.json"
    
    def save_context(
        self, 
        session_id: str, 
        agent_id: str, 
        context: Dict[str, Any],
        backup_type: str = "context",
        description: str = ""
    ) -> str:
        """
        保存上下文快照
        
        :param session_id: 会话 ID
        :param agent_id: Agent ID
        :param context: 上下文数据
        :param backup_type: 备份类型
        :param description: 描述
        :return: 备份文件路径
        """
        filename = self._generate_filename(session_id, agent_id, backup_type)
        filepath = os.path.join(self.backup_dir, filename)
        
        data = {
            "metadata": {
                "session_id": session_id,
                "agent_id": agent_id,
                "backup_type": backup_type,
                "timestamp": datetime.now().isoformat(),
                "description": description,
            },
            "context": context
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        size_bytes = os.path.getsize(filepath)
        self.lo.lput(
            f"[Backup] Saved {backup_type} for {agent_id}: {filename} ({size_bytes} bytes)",
            font_color=FontColor8.CYAN
        )
        
        return filepath
    
    def save_messages(
        self, 
        session_id: str, 
        agent_id: str, 
        messages: List[Dict]
    ) -> str:
        """保存消息历史"""
        return self.save_context(
            session_id, agent_id, 
            {"messages": messages},
            backup_type="messages",
            description=f"Message history ({len(messages)} messages)"
        )
    
    def save_plan(
        self, 
        session_id: str, 
        agent_id: str, 
        plan: Dict
    ) -> str:
        """保存任务计划"""
        return self.save_context(
            session_id, agent_id,
            {"plan": plan},
            backup_type="plan",
            description=f"Task plan ({len(plan.get('steps', []))} steps)"
        )
    
    def save_result(
        self, 
        session_id: str, 
        agent_id: str, 
        result: Any,
        step_id: int = None
    ) -> str:
        """保存执行结果"""
        return self.save_context(
            session_id, agent_id,
            {"result": result, "step_id": step_id},
            backup_type="result",
            description=f"Execution result (step={step_id})"
        )
    
    def load_latest_context(
        self, 
        session_id: str, 
        agent_id: str,
        backup_type: str = None
    ) -> Optional[Dict]:
        """
        加载最新的上下文备份
        
        :param session_id: 会话 ID
        :param agent_id: Agent ID
        :param backup_type: 备份类型（可选）
        :return: 上下文数据
        """
        pattern = f"{session_id}_{agent_id}_"
        if backup_type:
            pattern += f"{backup_type}_"
        pattern += "*.json"
        
        files = glob.glob(os.path.join(self.backup_dir, pattern))
        
        if not files:
            return None
            
        # 按文件名排序（包含时间戳）
        latest = sorted(files)[-1]
        
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.lo.lput(
            f"[Backup] Loaded {os.path.basename(latest)}",
            font_color=FontColor8.GREEN
        )
        
        return data.get("context")
    
    def load_all_context(
        self, 
        session_id: str, 
        agent_id: str = None,
        backup_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        加载所有匹配的上下文备份
        
        :param session_id: 会话 ID
        :param agent_id: Agent ID（可选）
        :param backup_type: 备份类型（可选）
        :param limit: 最大返回数量
        :return: 上下文列表
        """
        pattern = f"{session_id}_"
        if agent_id:
            pattern += f"{agent_id}_"
        else:
            pattern += "*_"
        if backup_type:
            pattern += f"{backup_type}_"
        else:
            pattern += "*_"
        pattern += "*.json"
        
        files = glob.glob(os.path.join(self.backup_dir, pattern))
        files = sorted(files, reverse=True)[:limit]
        
        results = []
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append({
                        "filepath": filepath,
                        "metadata": data.get("metadata"),
                        "context": data.get("context")
                    })
            except Exception as e:
                self.lo.lput(
                    f"[Backup] Failed to load {filepath}: {e}",
                    font_color=FontColor8.RED
                )
                
        return results
    
    def list_backups(
        self, 
        session_id: str = None, 
        agent_id: str = None
    ) -> List[BackupMetadata]:
        """
        列出备份文件
        
        :param session_id: 会话 ID（可选）
        :param agent_id: Agent ID（可选）
        :return: 备份元数据列表
        """
        pattern = ""
        if session_id:
            pattern += f"{session_id}_"
        else:
            pattern += "*_"
        if agent_id:
            pattern += f"{agent_id}_"
        else:
            pattern += "*_"
        pattern += "*.json"
        
        files = glob.glob(os.path.join(self.backup_dir, pattern))
        
        results = []
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get("metadata", {})
                    results.append(BackupMetadata(
                        session_id=meta.get("session_id", ""),
                        agent_id=meta.get("agent_id", ""),
                        backup_type=meta.get("backup_type", ""),
                        timestamp=meta.get("timestamp", ""),
                        size_bytes=os.path.getsize(filepath),
                        description=meta.get("description", "")
                    ))
            except Exception:
                pass
                
        return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def cleanup(self, max_age_hours: int = 24, max_count: int = 1000) -> int:
        """
        清理过期备份
        
        :param max_age_hours: 最大保留时间（小时）
        :param max_count: 最大保留数量
        :return: 删除的文件数量
        """
        files = glob.glob(os.path.join(self.backup_dir, "*.json"))
        
        deleted = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # 按时间过滤
        file_times = []
        for filepath in files:
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                file_times.append((filepath, mtime))
            except Exception:
                pass
        
        # 按时间排序
        file_times.sort(key=lambda x: x[1], reverse=True)
        
        for i, (filepath, mtime) in enumerate(file_times):
            # 超过最大数量或过期
            if i >= max_count or mtime < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted += 1
                except Exception as e:
                    self.lo.lput(
                        f"[Backup] Failed to delete {filepath}: {e}",
                        font_color=FontColor8.RED
                    )
        
        if deleted > 0:
            self.lo.lput(
                f"[Backup] Cleaned up {deleted} old backup files",
                font_color=FontColor8.YELLOW
            )
            
        return deleted
    
    def get_stats(self) -> Dict:
        """获取备份统计信息"""
        files = glob.glob(os.path.join(self.backup_dir, "*.json"))
        
        total_size = sum(os.path.getsize(f) for f in files)
        
        # 按类型统计
        type_counts = {}
        for f in files:
            basename = os.path.basename(f)
            parts = basename.split('_')
            if len(parts) >= 3:
                backup_type = parts[2]
                type_counts[backup_type] = type_counts.get(backup_type, 0) + 1
        
        return {
            "backup_dir": self.backup_dir,
            "total_files": len(files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "type_counts": type_counts,
        }
    
    def export_session(self, session_id: str, output_path: str) -> str:
        """
        导出会话的所有备份
        
        :param session_id: 会话 ID
        :param output_path: 输出路径
        :return: 导出文件路径
        """
        pattern = f"{session_id}_*.json"
        files = glob.glob(os.path.join(self.backup_dir, pattern))
        
        if not files:
            raise ValueError(f"No backups found for session {session_id}")
        
        # 创建导出目录
        export_dir = os.path.join(output_path, f"export_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(export_dir, exist_ok=True)
        
        # 复制文件
        for filepath in files:
            shutil.copy2(filepath, export_dir)
        
        self.lo.lput(
            f"[Backup] Exported {len(files)} files to {export_dir}",
            font_color=FontColor8.GREEN
        )
        
        return export_dir


# 全局备份管理器实例
context_backup = ContextBackup()
