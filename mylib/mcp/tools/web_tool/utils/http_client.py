"""HTTP 客户端操作算法模块"""

from typing import Dict, Optional

import aiohttp
from aiohttp import ClientSession


def create_session_kwargs(
    timeout: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    """
    创建 aiohttp 会话参数
    
    参数:
        timeout: 超时时间（秒），可选
        headers: HTTP 请求头字典，可选
        
    返回:
        会话配置字典
    """
    kwargs = {}
    if timeout is not None:
        kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
    if headers:
        kwargs["headers"] = headers
    return kwargs


async def retrieve_document(
    session: ClientSession,
    url: str,
    allow_redirects: bool = True,
    consume_body: bool = True,
) -> Dict[str, object]:
    """
    检索 HTTP 文档
    
    参数:
        session: aiohttp 客户端会话
        url: 目标 URL
        allow_redirects: 是否允许重定向
        consume_body: 是否读取响应体
        
    返回:
        包含 status、content_type、final_url、body 等的字典
    """
    async with session.get(url, allow_redirects=allow_redirects) as response:
        body = await response.text() if consume_body else ""
        if not consume_body:
            await response.release()
        return {
            "status": response.status,
            "content_type": response.headers.get("content-type", "unknown"),
            "content_length": int(response.headers.get("content-length", 0) or 0),
            "final_url": str(response.url),
            "body": body,
        }

