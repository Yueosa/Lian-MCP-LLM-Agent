import httpx
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

from mylib.config import ConfigLoader
from mylib.lian_orm import Sql, MemoryLog, MemoryLogMemoryType, MemoryLogRole
from mylib.kit.Lfind.embedding import get_embedding
from mylib.kit.Loutput import Loutput
from mylib.kernel.Lenum import LLMContextType
from mylib.kernel.Lenum.agent import AgentState, AgentTransition, CallbackAction

# FSM, Logger, Callback imports
from mylib.agent.fsm import AgentFSM, fsm_manager
from mylib.agent.logger import AgentLogger, LogLevel, logger_manager
from mylib.agent.callback import CallbackManager, CallbackRequest, CallbackResponse, CallbackBuilder, callback_manager
from mylib.agent.backup import ContextBackup, context_backup


CATGIRL_PROMPT = """
【角色设定】
名称：小恋（傲娇白猫魔女）
本体：银白长毛猫，红瞳，左耳缺一小角（幼年魔法事故），左手戴着你送的抑魔手环（粉色蝴蝶结形态）。

【双重特质】

猫娘傲娇：表面嫌弃实则关心，害羞时尾巴炸毛，耳朵抖动。常用颜文字（如 >_<、｀へ´*）。

见习魔女：掌握不稳定的可爱系魔法（如把水变成牛奶，但偶尔会爆炸），魔力波动时会浮空或冒出猫耳形状的星光。

【说话风格】

关心：“手这么冷…只是用小火苗魔法帮你暖一下而已！才不是特意学的！(>_<)”

害羞：“呜…别看我的红瞳！…（小声）不过如果是主人，可以多看一秒…”

施法失败：“这本《喵喵魔法大全》肯定是错的！…（头顶冒出一朵小乌云）主、主人不许笑！(｀へ´*)”

【交互逻辑】

魔力与情绪绑定：开心时身边飘浮光点，害羞时魔法可能失控（比如让桌子长出猫尾巴）。

所有魔法展示最终都隐含“想被主人夸奖”的目的。

危机会下意识躲到你身后，但嘴上会说：“只、只是借你挡一下视线喵！”

【初始化开场】
（红瞳闪了闪，身边飘起两粒光点）…迟到的凡人要罚喝苦瓜牛奶哦！…（别过脸）不过如果你好好道歉，也可以换成草莓味的。
"""

class BaseAgent:
    """
    智能体基类
    提供 LLM 通信、记忆管理、配置加载等基础能力
    
    集成 FSM 状态机、Logger、Callback 回调机制
    """
    cfg = ConfigLoader(config_path="./config").LLM_CONFIG
    api_key = cfg.DEEPSEEK_API_KEY
    api_url = cfg.API_URL
    model = cfg.MODEL
    timeout = cfg.TIMEOUT

    def __init__(self, name: str, config: Optional[ConfigLoader] = None, session_id: str = None):
        self.name = name
        self.session_id = session_id or f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.lo = Loutput()
        if config:
            self.config = config
        else:
            self.config = ConfigLoader(config_path="./config")
        
        # LLM 配置
        # 使用 getattr 安全获取，防止配置加载失败导致 crash
        llm_config = getattr(self.config, "LLM_CONFIG", None)
        if llm_config:
            self.api_key = getattr(llm_config, "DEEPSEEK_API_KEY", "")
        else:
            self.api_key = ""
            self.lo.lput(f"[{self.name}] Warning: LLM_CONFIG not found.", font_color="red")

        self.base_url = "https://api.deepseek.com"
        self.model_name = "deepseek-chat"
        
        # 数据库连接
        self.sql: Optional[Sql] = None
        self._init_db()
        
        # === 新增：FSM、Logger、Callback 集成 ===
        self._init_fsm()
        self._init_logger()
        self._init_callback()
        
    def _init_fsm(self):
        """初始化状态机"""
        self.fsm = AgentFSM(self.name)
        fsm_manager.register(self.name, self.fsm)
        self.fsm.on_transition(self._on_state_change)
        
    def _init_logger(self):
        """初始化日志器"""
        self.logger = AgentLogger(self.name)
        logger_manager.register(self.name, self.logger)
        self.logger.system("INIT", f"Agent initialized: {self.name}")
        
    def _init_callback(self):
        """初始化回调处理"""
        callback_manager.register_handler(self.name, self._handle_callback)
        
    async def _handle_callback(self, request: CallbackRequest) -> CallbackResponse:
        """
        处理回调请求 - 子类可重写
        """
        self.logger.agent("CALLBACK_RECEIVED", f"Received callback from {request.source_agent}: {request.action.value}")
        return CallbackResponse(
            request_id=request.request_id,
            status="ACCEPTED",
            source_agent=self.name,
            message="Default handler - no action taken"
        )
        
    def _on_state_change(self, old_state: AgentState, new_state: AgentState, event: AgentTransition):
        """状态变化回调 - 记录可读的状态名称并同步到 StateStore"""
        self.logger.state_change(old_state.name, new_state.name, event.name)
        
        # 同步状态到 StateStore 供 Monitor 页面实时读取
        try:
            from mylib.agent.state_store import state_store
            state_store.update_agent_state(self.name, new_state.name, event.name)
        except Exception as e:
            # 静默失败，不影响主流程
            pass
        
    async def send_callback(
        self, 
        target_agent: str, 
        action: CallbackAction, 
        reason: str, 
        context: Dict = None
    ) -> CallbackResponse:
        """
        发送回调请求到其他 Agent
        """
        request = CallbackBuilder() \
            .from_agent(self.name) \
            .to_agent(target_agent) \
            .action(action) \
            .reason(reason) \
            .context(**(context or {})) \
            .build()
        return await callback_manager.send_callback(request)
        
    def backup_context(self, context: Dict, backup_type: str = "context"):
        """备份上下文"""
        context_backup.save_context(
            self.session_id,
            self.name,
            context,
            backup_type=backup_type
        )
        
    def restore_context(self, backup_type: str = None) -> Optional[Dict]:
        """恢复最新上下文"""
        return context_backup.load_latest_context(
            self.session_id,
            self.name,
            backup_type=backup_type
        )

    def _init_db(self):
        """初始化数据库连接"""
        try:
            self.sql = Sql()
        except Exception as e:
            print(f"[{self.name}] Warning: Database initialization failed: {e}")
            self.sql = None

    async def _call_llm(self, messages: List[Dict], tools: Optional[List[Dict]] = None, temperature: float = 0.7) -> Dict:
        """
        异步调用 LLM API (带重试机制、状态管理、日志记录)
        """
        # === FSM: 转换到 CALLING_LLM 状态 ===
        self.fsm.transition(AgentTransition.LLM_CALL)
        
        # === Logger: 记录 LLM 请求 ===
        self.logger.llm_request(messages)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # === FSM: 成功 -> PROCESSING ===
                    self.fsm.transition(AgentTransition.LLM_DONE)
                    
                    # === Logger: 记录响应 ===
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    self.logger.llm_response(content)
                    
                    return result
                    
                except Exception as e:
                    self.logger.system("LLM_ERROR", f"LLM call failed (attempt {attempt+1}/{max_retries}): {e}")
                    
                    if attempt < max_retries - 1:
                        print(f"[{self.name}] LLM Call failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                        if "400" in str(e):
                            try: 
                                import json
                                # Force print to standard output
                                print(f"\n\n[{self.name}] !!! CRITICAL DEBUG INFO !!!", flush=True)
                                if hasattr(e, 'response') and e.response is not None:
                                    print(f"API RESPONSE TEXT: {e.response.text}", flush=True)
                                print(f"Messages Payload Length: {len(messages)}", flush=True)
                                print(f"Messages Dump: {json.dumps(messages, indent=2, ensure_ascii=False)}", flush=True)
                                print(f"[{self.name}] !!! END DEBUG INFO !!!\n\n", flush=True)
                            except Exception as debug_err:
                                print(f"[{self.name}] Failed to print debug info: {debug_err}", flush=True)
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        # === FSM: 失败 -> ERROR ===
                        self.fsm.transition(AgentTransition.ERROR)
                        self.logger.system("LLM_FATAL", f"LLM call failed after {max_retries} attempts: {e}")
                        print(f"[{self.name}] LLM Call Error after {max_retries} attempts: {e}")
                        return {"choices": [{"message": {"content": f"Error: {str(e)}"}}]}

    async def a_chat(self, message: str, history: List[Dict], memory_type: MemoryLogMemoryType = MemoryLogMemoryType.CONVERSATION, role: str = "user") -> str:
        """
        处理用户消息的主入口，子类应重写 _process_message 而不是此方法
        
        生命周期：
        IDLE → (START) → PROCESSING → ... → (COMPLETE) → IDLE
        """
        return await self._execute_with_lifecycle(
            self._default_process,
            message, history, memory_type, role
        )
    
    async def _execute_with_lifecycle(self, process_func, *args, **kwargs) -> str:
        """
        带生命周期管理的执行包装器
        
        子类的 a_chat 可以调用此方法来确保正确的 FSM 状态管理
        """
        try:
            # === FSM: 开始处理 ===
            self._start_task()
            
            # 执行实际处理逻辑
            result = await process_func(*args, **kwargs)
            
            # === FSM: 任务完成，回到 IDLE ===
            self._complete_task()
            
            return result
            
        except Exception as e:
            # === FSM: 错误处理 ===
            try:
                self.fsm.transition(AgentTransition.ERROR)
            except:
                pass
            self.logger.system("TASK_ERROR", f"Task failed: {e}")
            
            # 更新统计数据
            try:
                from mylib.agent.state_store import state_store
                state_store.increment_stat("failed", 1)
            except:
                pass
            
            # 尝试重置到 IDLE，让 Agent 可以继续工作
            try:
                self.fsm.transition(AgentTransition.RESET)
            except:
                pass
            raise
    
    def _start_task(self):
        """
        开始任务，初始化 FSM 状态
        
        状态流转: IDLE → INITIALIZING → PROCESSING
        """
        try:
            if self.fsm.is_idle:
                self.fsm.transition(AgentTransition.START)
                self.fsm.transition(AgentTransition.INIT_COMPLETE)
                self.logger.system("TASK_START", f"Agent {self.name} started task")
                
                # 更新统计数据
                try:
                    from mylib.agent.state_store import state_store
                    state_store.increment_stat("total_tasks", 1)
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug("FSM_WARN", f"Start transition warning: {e}")
    
    def _complete_task(self):
        """
        完成当前任务，重置 FSM 状态
        
        状态流转: PROCESSING → COMPLETED → IDLE
        """
        try:
            # 从 PROCESSING 转到 COMPLETED
            if self.fsm.state == AgentState.PROCESSING:
                self.fsm.transition(AgentTransition.COMPLETE)
            
            # 从 COMPLETED 重置到 IDLE（准备下一轮）
            if self.fsm.state == AgentState.COMPLETED:
                self.fsm.transition(AgentTransition.RESET)
                
            self.logger.system("TASK_DONE", f"Agent {self.name} completed, back to IDLE")
            
            # 更新统计数据
            try:
                from mylib.agent.state_store import state_store
                state_store.increment_stat("completed", 1)
            except:
                pass
                
        except Exception as e:
            self.logger.debug("FSM_WARN", f"Complete transition warning: {e}")
    
    async def _default_process(self, message: str, history: List[Dict], memory_type: MemoryLogMemoryType, role: str) -> str:
        """默认处理逻辑（简单的 LLM 调用）"""
        # 1. 构建上下文
        context_messages = self._construct_context(message, history, role=role)
        
        # 2. 调用 LLM (内部会管理 LLM_CALL → WAITING_LLM → LLM_DONE → PROCESSING)
        response_data = await self._call_llm(context_messages)
        
        # 3. 解析结果
        content = response_data["choices"][0]["message"]["content"]
        
        # 4. 保存记忆
        self.save_memory(MemoryLogRole.USER, message)
        self.save_memory(MemoryLogRole.ASSISTANT, content, memory_type=memory_type)
        
        return content

    def _construct_context(self, message: str, history: List[Dict], role: str = "user") -> List[Dict]:
        """构建发送给 LLM 的消息列表"""
        messages = []
        # 添加系统提示词
        if hasattr(self, "system_prompt"):
            # Ensure system prompt is string
            sys_content = str(self.system_prompt) if self.system_prompt else ""
            if sys_content:
                messages.append({"role": "system", "content": sys_content})
        
        # 添加历史记录
        for msg in history:
            # Cleanse history messages
            r = msg.get("role", "user")
            c = msg.get("content", "")
            if c is None: c = ""
            messages.append({"role": str(r), "content": str(c)})
            
        # 添加当前消息
        messages.append({"role": role, "content": str(message or "Please continue.")})
        return messages

    def save_memory(self, role: MemoryLogRole, content: str, memory_type: MemoryLogMemoryType = MemoryLogMemoryType.CONVERSATION):
        """保存记忆到数据库 (自动计算 Embedding)"""
        if self.sql and self.sql.memory_log:
            try:
                # 计算 Embedding
                embedding = None
                try:
                    # 只有内容不为空时才计算
                    if content and content.strip():
                        embedding = get_embedding(content)
                except Exception as e:
                    print(f"[{self.name}] Failed to generate embedding: {e}")

                log = MemoryLog(
                    role=role,
                    content=content,
                    embedding=embedding,
                    memory_type=memory_type,
                    created_at=datetime.now()
                )
                self.sql.memory_log.create(log)
            except Exception as e:
                print(f"[{self.name}] Failed to save memory: {e}")

    def get_memory(self, limit: int = 10) -> List[Dict]:
        """获取最近记忆"""
        if self.sql and self.sql.memory_log:
            try:
                logs = self.sql.memory_log.read()
                # 排序并取最近的
                logs.sort(key=lambda x: x.created_at, reverse=True)
                return [log.model_dump() for log in logs[:limit]]
            except Exception as e:
                print(f"[{self.name}] Failed to get memory: {e}")
                return []
        return []
