#!/usr/bin/env python3
"""
导出对话记录脚本

用法:
    uv run python scripts/export_conversation.py --start 466 --end 510 --output demo_conversation.json
    uv run python scripts/export_conversation.py --start 466 --end 510 --format html --output demo.html
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mylib.lian_orm import Sql
from mylib.kernel.Lenum import MemoryLogRole, MemoryLogMemoryType


def export_conversation(start_id: int, end_id: int, output_path: str, output_format: str = "json"):
    """导出指定 ID 范围的对话记录"""
    
    print(f"📚 正在导出 memory_log 表中 id {start_id}-{end_id} 的记录...")
    
    # 连接数据库
    sql = Sql()
    
    # 使用 ORM 封装的 db_client 执行查询
    query = """
        SELECT id, user_id, role, content, memory_type, importance, created_at
        FROM memory_log
        WHERE id >= %s AND id <= %s
        ORDER BY id ASC
    """
    
    rows = sql.db_client.fetch_all(query, [start_id, end_id])
    
    # fetch_all 已返回字典列表，直接处理
    records = []
    for record in rows:
        # 处理枚举类型
        if isinstance(record.get('role'), MemoryLogRole):
            record['role'] = record['role'].value
        if isinstance(record.get('memory_type'), MemoryLogMemoryType):
            record['memory_type'] = record['memory_type'].value
        # 处理时间
        if isinstance(record.get('created_at'), datetime):
            record['created_at'] = record['created_at'].isoformat()
        records.append(record)
    
    print(f"✅ 找到 {len(records)} 条记录")
    
    if output_format == "json":
        # 导出 JSON
        output_data = {
            "meta": {
                "exported_at": datetime.now().isoformat(),
                "id_range": f"{start_id}-{end_id}",
                "total_records": len(records),
                "description": "Lian MCP Agent 多轮对话记录导出"
            },
            "conversation": records
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"📝 JSON 已保存到: {output_path}")
        
    elif output_format == "html":
        # 导出 HTML 展示页面
        html_content = generate_html(records, start_id, end_id)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML 已保存到: {output_path}")
    
    elif output_format == "markdown":
        # 导出 Markdown
        md_content = generate_markdown(records, start_id, end_id)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📄 Markdown 已保存到: {output_path}")
    
    return records


def generate_markdown(records, start_id, end_id):
    """生成 Markdown 格式"""
    md = f"""# Lian MCP Agent 多轮对话演示

> 导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 记录范围: ID {start_id} - {end_id}
> 总计: {len(records)} 条记录

---

"""
    
    for record in records:
        role = record['role']
        content = record['content']
        memory_type = record['memory_type']
        created_at = record.get('created_at', '')
        
        # 角色图标
        role_icon = {
            'user': '👤 用户',
            'assistant': '🤖 助手',
            'system': '⚙️ 系统',
            'tool': '🔧 工具'
        }.get(role, role)
        
        # 类型标签
        type_badge = f"[{memory_type}]" if memory_type else ""
        
        md += f"### {role_icon} {type_badge}\n\n"
        md += f"{content}\n\n"
        md += f"*{created_at}*\n\n"
        md += "---\n\n"
    
    return md


def generate_html(records, start_id, end_id):
    """生成 HTML 展示页面"""
    
    # ========== 配置区域 ==========
    # 初始展开的 Round（其他默认折叠）
    EXPANDED_ROUNDS = [1, 6, 7, 22]
    # 需要突出显示的 Round（添加特殊边框）
    HIGHLIGHTED_ROUNDS = [13, 18]
    # ==============================
    
    # 按对话轮次分组
    rounds = []
    current_round = {"user": None, "agents": []}
    
    for record in records:
        role = record['role']
        if role == 'user':
            if current_round['user'] is not None:
                rounds.append(current_round)
                current_round = {"user": None, "agents": []}
            current_round['user'] = record
        else:
            current_round['agents'].append(record)
    
    if current_round['user'] is not None:
        rounds.append(current_round)
    
    # 生成 HTML
    messages_html = ""
    for i, round_data in enumerate(rounds, 1):
        user_msg = round_data['user']
        is_expanded = i in EXPANDED_ROUNDS
        is_highlighted = i in HIGHLIGHTED_ROUNDS
        
        highlight_class = "highlighted" if is_highlighted else ""
        expanded_class = "expanded" if is_expanded else ""
        
        # 用户消息预览（折叠时显示）
        user_preview = escape_html(user_msg['content'][:80]) + "..." if len(user_msg['content']) > 80 else escape_html(user_msg['content'])
        
        messages_html += f"""
        <div class="round-container {highlight_class} {expanded_class}" data-round="{i}">
            <div class="round-header" onclick="toggleRound({i})">
                <div class="round-header-left">
                    <span class="expand-icon">{'▼' if is_expanded else '▶'}</span>
                    <span class="round-badge">Round {i}</span>
                    {f'<span class="highlight-badge">⭐ 重点</span>' if is_highlighted else ''}
                </div>
                <div class="round-header-right">
                    <span class="round-preview">{user_preview}</span>
                    <span class="round-time">{user_msg.get('created_at', '')[:19]}</span>
                </div>
            </div>
            
            <div class="round-content" style="display: {'block' if is_expanded else 'none'};">
                <div class="message user-message">
                    <div class="message-header">
                        <span class="avatar user-avatar">👤</span>
                        <span class="sender-name">用户</span>
                    </div>
                    <div class="message-content">{escape_html(user_msg['content'])}</div>
                </div>
        """
        
        for agent_msg in round_data['agents']:
            memory_type = agent_msg.get('memory_type', 'conversation')
            content = agent_msg.get('content', '')
            agent_info = get_agent_info(memory_type, content)
            
            messages_html += f"""
                <div class="message agent-message {agent_info['class']}">
                    <div class="message-header">
                        <span class="avatar">{agent_info['icon']}</span>
                        <span class="sender-name">{agent_info['name']}</span>
                        <span class="type-badge">{memory_type}</span>
                    </div>
                    <div class="message-content">{format_content(content)}</div>
                </div>
            """
        
        messages_html += """
            </div>
        </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lian MCP Agent - 多轮对话演示</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    <style>
        /* 深色主题（默认） */
        :root {{
            --bg-dark: #0a0a0f;
            --bg-card: #13131a;
            --bg-hover: #1a1a24;
            --primary: #a855f7;
            --accent-pink: #ec4899;
            --accent-blue: #3b82f6;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
            --accent-cyan: #06b6d4;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: #27272a;
            --body-bg: #0a0a0f;
            --card-shadow: none;
            --json-bg: #1e1e2e;
            --json-color: #a6e3a1;
        }}
        
        /* 粉蓝白主题 */
        :root.theme-light {{
            --bg-dark: #f8fafc;
            --bg-card: #ffffff;
            --bg-hover: #f1f5f9;
            --primary: #a855f7;
            --accent-pink: #ec4899;
            --accent-blue: #3b82f6;
            --accent-green: #22c55e;
            --accent-yellow: #f59e0b;
            --accent-cyan: #06b6d4;
            --text-primary: #1e293b;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --body-bg: linear-gradient(135deg, #fef3f8 0%, #f0f9ff 100%);
            --card-shadow: 0 4px 20px rgba(125, 211, 252, 0.15);
            --json-bg: #f1f5f9;
            --json-color: #166534;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--body-bg);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            transition: background 0.3s ease, color 0.3s ease;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .header {{
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary), var(--accent-pink));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        .meta-info {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        
        .meta-item {{
            background: var(--bg-card);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        .meta-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        
        .meta-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--primary);
        }}
        
        .round-container {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0;
            margin-bottom: 1rem;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: var(--card-shadow);
        }}
        
        .round-container.highlighted {{
            border: 2px solid var(--accent-pink);
            box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
        }}
        
        .round-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            background: var(--bg-hover);
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }}
        
        .round-header:hover {{
            background: rgba(168, 85, 247, 0.1);
        }}
        
        .round-header-left {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .round-header-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .expand-icon {{
            color: var(--text-muted);
            font-size: 0.75rem;
            transition: transform 0.2s;
        }}
        
        .round-container.expanded .expand-icon {{
            transform: rotate(0deg);
        }}
        
        .round-preview {{
            color: var(--text-muted);
            font-size: 0.8rem;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .round-container.expanded .round-preview {{
            display: none;
        }}
        
        .highlight-badge {{
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-yellow));
            padding: 0.15rem 0.5rem;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 600;
            color: #fff;
        }}
        
        .round-content {{
            padding: 1.5rem;
            border-top: 1px solid var(--border);
        }}
        
        .round-badge {{
            background: linear-gradient(135deg, var(--primary), var(--accent-pink));
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .round-time {{
            font-size: 0.8rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .message {{
            margin: 1rem 0;
            padding: 1rem;
            border-radius: 12px;
            border-left: 3px solid transparent;
        }}
        
        .user-message {{
            background: rgba(168, 85, 247, 0.1);
            border-left-color: var(--primary);
        }}
        
        .agent-message {{
            background: var(--bg-hover);
        }}
        
        .agent-message.rag {{
            border-left-color: var(--accent-cyan);
        }}
        
        .agent-message.plan {{
            border-left-color: var(--accent-blue);
        }}
        
        .agent-message.execution {{
            border-left-color: var(--accent-yellow);
        }}
        
        .agent-message.summary {{
            border-left-color: var(--accent-pink);
        }}
        
        .message-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }}
        
        .avatar {{
            font-size: 1.25rem;
        }}
        
        .sender-name {{
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .type-badge {{
            font-size: 0.7rem;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            background: var(--bg-dark);
            color: var(--text-muted);
            margin-left: auto;
        }}
        
        .message-content {{
            color: var(--text-secondary);
            white-space: pre-wrap;
            word-break: break-word;
            font-size: 0.95rem;
        }}
        
        .message-content code {{
            background: var(--bg-dark);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }}
        
        .message-content pre {{
            background: var(--bg-dark);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 0.5rem 0;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }}
        
        .json-block {{
            background: var(--json-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            overflow-x: auto;
            color: var(--json-color);
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}
        
        .controls button {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}
        
        .controls button:hover {{
            background: var(--bg-hover);
            border-color: var(--primary);
            color: var(--primary);
        }}
        
        .theme-btn {{
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-blue)) !important;
            border: none !important;
            color: white !important;
        }}
        
        .theme-btn:hover {{
            opacity: 0.9;
            transform: scale(1.02);
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            .header h1 {{
                font-size: 1.75rem;
            }}
            .meta-info {{
                gap: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🐱 Lian MCP Agent</h1>
            <p class="subtitle">Multi-Agent 协作对话系统演示</p>
            <div class="meta-info">
                <div class="meta-item">
                    <div class="meta-label">记录范围</div>
                    <div class="meta-value">#{start_id} - #{end_id}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">对话轮次</div>
                    <div class="meta-value">{len(rounds)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">总消息数</div>
                    <div class="meta-value">{len(records)}</div>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <button onclick="expandAll()">📂 全部展开</button>
            <button onclick="collapseAll()">📁 全部折叠</button>
            <button onclick="showHighlighted()">⭐ 只看重点</button>
            <button class="theme-btn" onclick="toggleTheme()" id="theme-toggle-btn">🌙 深色</button>
        </div>
        
        <main class="conversation">
            {messages_html}
        </main>
        
        <footer class="footer">
            <p>Powered by Lian MCP Agent | Multi-Agent System with RAG + Planning + Execution</p>
            <p>导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </div>
    
    <script>
        // 主题管理
        let currentTheme = localStorage.getItem('conversation-theme') || 'dark';
        
        function initTheme() {{
            if (currentTheme === 'light') {{
                document.documentElement.classList.add('theme-light');
                updateThemeButton();
            }}
        }}
        
        function toggleTheme() {{
            if (currentTheme === 'dark') {{
                currentTheme = 'light';
                document.documentElement.classList.add('theme-light');
            }} else {{
                currentTheme = 'dark';
                document.documentElement.classList.remove('theme-light');
            }}
            localStorage.setItem('conversation-theme', currentTheme);
            updateThemeButton();
        }}
        
        function updateThemeButton() {{
            const btn = document.getElementById('theme-toggle-btn');
            if (currentTheme === 'dark') {{
                btn.innerHTML = '🌙 深色';
            }} else {{
                btn.innerHTML = '☀️ 浅色';
            }}
        }}
        
        // 立即应用主题
        initTheme();
        
        function toggleRound(roundNum) {{
            const container = document.querySelector(`[data-round="${{roundNum}}"]`);
            const content = container.querySelector('.round-content');
            const icon = container.querySelector('.expand-icon');
            
            if (content.style.display === 'none') {{
                content.style.display = 'block';
                container.classList.add('expanded');
                icon.textContent = '▼';
            }} else {{
                content.style.display = 'none';
                container.classList.remove('expanded');
                icon.textContent = '▶';
            }}
        }}
        
        function expandAll() {{
            document.querySelectorAll('.round-container').forEach(container => {{
                container.querySelector('.round-content').style.display = 'block';
                container.classList.add('expanded');
                container.querySelector('.expand-icon').textContent = '▼';
            }});
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.round-container').forEach(container => {{
                container.querySelector('.round-content').style.display = 'none';
                container.classList.remove('expanded');
                container.querySelector('.expand-icon').textContent = '▶';
            }});
        }}
        
        function showHighlighted() {{
            document.querySelectorAll('.round-container').forEach(container => {{
                const isHighlighted = container.classList.contains('highlighted');
                container.querySelector('.round-content').style.display = isHighlighted ? 'block' : 'none';
                container.classList.toggle('expanded', isHighlighted);
                container.querySelector('.expand-icon').textContent = isHighlighted ? '▼' : '▶';
            }});
        }}
    </script>
</body>
</html>
"""
    return html


def get_agent_info(memory_type, content=""):
    """根据 memory_type 和内容特征返回 Agent 信息"""
    
    # 先根据内容特征判断
    if content:
        content_lower = content[:200].lower() if len(content) > 200 else content.lower()
        
        # Executor 特征
        if any(keyword in content for keyword in ['【执行小结】', 'TOOL_CALL:', '工具调用', '执行结果']):
            return {'name': 'Executor (魔力执行官)', 'icon': '⚡', 'class': 'execution'}
        
        # Planner 特征 (JSON 格式的计划)
        if '"steps"' in content or '"task_type"' in content or '步骤规划' in content:
            return {'name': 'Planner (星盘占卜师)', 'icon': '🔮', 'class': 'plan'}
        
        # RAG 特征
        if '记忆片段' in content or '历史记忆' in content or '检索结果' in content:
            return {'name': 'RAG (全知魔导书)', 'icon': '📖', 'class': 'rag'}
    
    # 根据 memory_type 判断
    mapping = {
        'summary': {'name': 'Summary (小恋)', 'icon': '🐱', 'class': 'summary'},
        'plan': {'name': 'Planner (星盘占卜师)', 'icon': '🔮', 'class': 'plan'},
        'execution': {'name': 'Executor (魔力执行官)', 'icon': '⚡', 'class': 'execution'},
        'conversation': {'name': 'Executor (魔力执行官)', 'icon': '⚡', 'class': 'execution'},  # 默认 conversation 是执行器
        'reflection': {'name': 'System', 'icon': '💭', 'class': 'rag'},
        'preference': {'name': 'System', 'icon': '⚙️', 'class': 'rag'},
    }
    return mapping.get(memory_type, {'name': 'Agent', 'icon': '🤖', 'class': ''})


def escape_html(text):
    """转义 HTML 特殊字符"""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))


def format_content(content):
    """格式化内容（处理代码块、JSON 等）"""
    content = escape_html(content)
    
    # 简单处理 JSON 块
    if content.strip().startswith('{') and content.strip().endswith('}'):
        return f'<div class="json-block">{content}</div>'
    
    return content


def main():
    parser = argparse.ArgumentParser(description='导出 Lian MCP Agent 对话记录')
    parser.add_argument('--start', type=int, required=True, help='起始 ID')
    parser.add_argument('--end', type=int, required=True, help='结束 ID')
    parser.add_argument('--output', '-o', type=str, default='demo_conversation.json', help='输出文件路径')
    parser.add_argument('--format', '-f', type=str, choices=['json', 'html', 'markdown'], default='json', help='输出格式')
    
    args = parser.parse_args()
    
    export_conversation(args.start, args.end, args.output, args.format)


if __name__ == "__main__":
    main()
