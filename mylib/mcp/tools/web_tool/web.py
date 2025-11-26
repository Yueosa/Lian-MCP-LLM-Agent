"""用于网页抓取的核心 MCP 工具实现"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import aiohttp
from bs4 import BeautifulSoup

from mylib import ConfigLoader

from .utils import extract_elements as extract_elements_from_html
from .utils.http_client import retrieve_document, create_session_kwargs
from .utils.content_processor import clip_content, slice_lines_from_content

DEFAULT_CONFIG_PATH = Path(__file__).with_name("web.config.toml")


class WebTool:
    """Provide asynchronous utilities for inspecting web documents."""

    DEFAULT_TIMEOUT = 30
    DEFAULT_USER_AGENT = "MCP-WebTool/1.0 (Python/aiohttp)"
    DEFAULT_MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    DEFAULT_SELECTOR_LIMIT = 50

    _CONFIG_CACHE: Dict[Tuple[str, bool], ConfigLoader] = {}

    def __init__(
        self,
        *,
        config_path: Optional[str] = None,
        search_subdirs: bool = False,
    ) -> None:
        self._config_loader = self._get_config_loader(config_path, search_subdirs)
        http_cfg = getattr(self._config_loader, "http", None)
        extraction_cfg = getattr(self._config_loader, "extraction", None)

        self._default_timeout = self._read_int(http_cfg, "timeout", self.DEFAULT_TIMEOUT)
        self._user_agent = self._read_str(http_cfg, "user_agent", self.DEFAULT_USER_AGENT)
        self._max_content_length = self._read_int(
            http_cfg,
            "max_content_length",
            self.DEFAULT_MAX_CONTENT_LENGTH,
        )
        self._default_selector_limit = self._read_int(
            extraction_cfg,
            "default_limit",
            self.DEFAULT_SELECTOR_LIMIT,
        )
        self._resolve_url_attributes = self._read_str_list(
            extraction_cfg,
            "resolve_url_attributes",
            default=("href", "src"),
        )

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    @classmethod
    def _get_config_loader(
        cls,
        config_path: Optional[str],
        search_subdirs: bool,
    ) -> ConfigLoader:
        resolved_path = config_path or str(DEFAULT_CONFIG_PATH)
        cache_key = (resolved_path, search_subdirs)
        if cache_key not in cls._CONFIG_CACHE:
            cls._CONFIG_CACHE[cache_key] = ConfigLoader(
                config_path=resolved_path,
                search_subdirs=search_subdirs,
            )
        return cls._CONFIG_CACHE[cache_key]

    @staticmethod
    def _read_int(section, key: str, default: int) -> int:
        if section is None:
            return default
        value = section.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _read_str(section, key: str, default: str) -> str:
        if section is None:
            return default
        value = section.get(key, default)
        if not isinstance(value, str):
            return default
        return value

    @staticmethod
    def _read_str_list(
        section,
        key: str,
        default: Sequence[str] = (),
    ) -> Tuple[str, ...]:
        if section is None:
            return tuple(default)
        value = section.get(key, list(default))
        if isinstance(value, (list, tuple)):
            return tuple(str(item) for item in value)
        if isinstance(value, str):
            return (value,)
        return tuple(default)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _session_kwargs(self, timeout: Optional[int]) -> Dict[str, object]:
        """创建会话参数(使用 utils 函数)"""
        return create_session_kwargs(
            timeout=timeout or self._default_timeout,
            headers={"User-Agent": self._user_agent},
        )

    def _clip_content(self, text: str) -> Tuple[str, bool]:
        """裁剪内容到最大长度(使用 utils 函数)"""
        clipped = clip_content(text, self._max_content_length)
        truncated = len(clipped) < len(text)
        return clipped, truncated

    @staticmethod
    def _slice_lines(
        content: str,
        start_line: Optional[int],
        end_line: Optional[int],
    ) -> Tuple[str, int, int]:
        """按行切片内容(使用 utils 函数)"""
        lines = content.split("\n")
        total_lines = len(lines)
        if start_line is None and end_line is None:
            return content, total_lines, total_lines

        # 转换为 0-based 索引
        start_idx = max(0, (start_line or 1) - 1)
        end_idx = end_line or total_lines
        end_idx = min(total_lines, end_idx)

        sliced = slice_lines_from_content(content, start_idx, end_idx)
        lines_returned = len(sliced.split("\n")) if sliced else 0
        return sliced, lines_returned, total_lines

    async def _retrieve_document(
        self,
        url: str,
        *,
        timeout: Optional[int] = None,
        allow_redirects: bool = True,
        consume_body: bool = True,
    ) -> Dict[str, object]:
        """检索 HTTP 文档(使用 utils 函数)"""
        async with aiohttp.ClientSession(**self._session_kwargs(timeout)) as session:
            return await retrieve_document(
                session,
                url,
                allow_redirects=allow_redirects,
                consume_body=consume_body,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def fetch(
        self,
        url: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, object]:
        try:
            result = await self._retrieve_document(url, timeout=timeout)
        except aiohttp.ClientError as exc:
            return {"success": False, "url": url, "error": f"网络请求错误: {exc}"}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "url": url, "error": f"获取网页错误: {exc}"}

        if result["status"] != 200:
            return {
                "success": False,
                "url": url,
                "status_code": result["status"],
                "error": f"HTTP 错误: {result['status']}",
            }

        text, truncated = self._clip_content(result["body"])
        content, lines_returned, total_lines = self._slice_lines(text, start_line, end_line)

        return {
            "success": True,
            "url": url,
            "final_url": result["final_url"],
            "status_code": result["status"],
            "content": content,
            "lines_returned": lines_returned,
            "total_lines": total_lines,
            "content_type": result["content_type"],
            "truncated": truncated,
        }

    async def check_status(
        self,
        url: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, object]:
        try:
            result = await self._retrieve_document(
                url,
                timeout=timeout,
                allow_redirects=True,
                consume_body=False,
            )
        except aiohttp.ClientError as exc:
            return {"success": False, "url": url, "status_code": 0, "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "url": url, "status_code": 0, "error": str(exc)}

        return {
            "success": True,
            "url": url,
            "status_code": result["status"],
            "content_type": result["content_type"],
            "content_length": result["content_length"],
            "final_url": result["final_url"],
            "is_redirect": result["final_url"] != url,
        }

    async def extract_elements(
        self,
        url: str,
        selector: str,
        *,
        attributes: Optional[Sequence[str]] = None,
        include_text: bool = True,
        include_html: bool = False,
        limit: Optional[int] = None,
        resolve_urls: Optional[Sequence[str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, object]:
        try:
            result = await self._retrieve_document(url, timeout=timeout)
        except aiohttp.ClientError as exc:
            return {"success": False, "url": url, "error": f"网络请求错误: {exc}"}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "url": url, "error": f"获取网页错误: {exc}"}

        if result["status"] != 200:
            return {
                "success": False,
                "url": url,
                "status_code": result["status"],
                "error": f"HTTP 错误: {result['status']}",
            }

        html, truncated = self._clip_content(result["body"])
        soup = BeautifulSoup(html, "html.parser")

        resolved_limit = limit if limit is not None else self._default_selector_limit
        resolved_urls = tuple(resolve_urls) if resolve_urls is not None else self._resolve_url_attributes

        elements = extract_elements_from_html(
            soup,
            selector,
            attributes=attributes,
            include_text=include_text,
            include_html=include_html,
            limit=resolved_limit,
            base_url=result["final_url"],
            resolve_urls=resolved_urls,
        )

        return {
            "success": True,
            "url": url,
            "final_url": result["final_url"],
            "selector": selector,
            "total": len(elements),
            "results": elements,
            "truncated": truncated,
        }
