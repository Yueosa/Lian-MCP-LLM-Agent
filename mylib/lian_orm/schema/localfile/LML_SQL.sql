-- ============================================
-- 1. 扩展：pgvector（用于 embedding 检索）
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================
-- 2. memory_log —— 长期记忆（含 embedding）
-- ============================================
CREATE TABLE IF NOT EXISTS memory_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) DEFAULT 'default',
    role VARCHAR(16) NOT NULL,                       -- user / assistant / system / llm
    content TEXT NOT NULL,
    embedding VECTOR(1536),                          -- 向量维度可根据模型修改
    memory_type VARCHAR(32) DEFAULT 'conversation',  -- summary / reflection / preference / plan 等
    importance FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 向量索引用于快速检索
CREATE INDEX IF NOT EXISTS memory_log_embedding_idx
ON memory_log USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);


-- ============================================
-- 3. tasks —— 顶层任务 
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) DEFAULT 'default',
    title TEXT,
    description TEXT,
    status VARCHAR(32) DEFAULT 'pending',           -- pending / running / done / failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS tasks_user_id_idx ON tasks (user_id);


-- ============================================
-- 4. task_steps —— 单任务的步骤
-- ============================================
CREATE TABLE IF NOT EXISTS task_steps (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,                    -- 步骤编号
    instruction TEXT NOT NULL,                      -- Planner 给执行器的指令
    output TEXT,                                    -- 执行结果
    status VARCHAR(32) DEFAULT 'pending',           -- pending / running / done / failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 为任务步骤创建索引
CREATE INDEX IF NOT EXISTS task_steps_task_id_idx ON task_steps (task_id);
CREATE INDEX IF NOT EXISTS task_steps_idx_idx ON task_steps (step_index);


-- ============================================
-- 5. tool_calls —— 工具调用记录
-- ============================================
CREATE TABLE IF NOT EXISTS tool_calls (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    step_id INTEGER REFERENCES task_steps(id) ON DELETE SET NULL,
    tool_name VARCHAR(128) NOT NULL,
    arguments JSONB,
    response JSONB,
    status VARCHAR(32) DEFAULT 'success',           -- success / failed
    created_at TIMESTAMP DEFAULT NOW()
);

-- 工具调用性能优化
CREATE INDEX IF NOT EXISTS tool_calls_task_id_idx ON tool_calls (task_id);
CREATE INDEX IF NOT EXISTS tool_calls_step_id_idx ON tool_calls (step_id);
CREATE INDEX IF NOT EXISTS tool_calls_tool_name_idx ON tool_calls (tool_name);
