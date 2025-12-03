"""用于解析 HTML 文档的通用提取辅助工具"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Union
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def _normalize_attributes(
    element,
    attributes: Sequence[str],
    *,
    base_url: Optional[str] = None,
    resolve_urls: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """返回元素属性值的规范化映射"""
    resolved: Dict[str, str] = {}
    resolve_urls = set(resolve_urls or [])

    for name in attributes:
        value = element.get(name)
        if value is None:
            continue
        if base_url and name in resolve_urls:
            resolved[name] = urljoin(base_url, value)
        else:
            resolved[name] = value
    return resolved


def extract_elements(
    soup: BeautifulSoup,
    selector: str,
    *,
    attributes: Optional[Union[str, Sequence[str]]] = None,
    include_text: bool = True,
    include_html: bool = False,
    limit: Optional[int] = None,
    base_url: Optional[str] = None,
    resolve_urls: Optional[Sequence[str]] = None,
) -> List[Dict[str, object]]:
    """将与 CSS 选择器匹配的元素提取到结构化有效负载中"""
    if limit is not None and limit < 0:
        raise ValueError("limit cannot be negative")

    elements = soup.select(selector)
    if limit is not None:
        elements = elements[:limit]

    attr_list: Optional[List[str]]
    if attributes is None:
        attr_list = None
    elif isinstance(attributes, str):
        attr_list = [attributes]
    else:
        attr_list = list(attributes)

    results: List[Dict[str, object]] = []
    for index, element in enumerate(elements):
        entry: Dict[str, object] = {"index": index, "tag": element.name or ""}

        if include_text:
            entry["text"] = element.get_text(strip=True)

        if attr_list:
            entry["attributes"] = _normalize_attributes(
                element,
                attr_list,
                base_url=base_url,
                resolve_urls=resolve_urls,
            )

        if include_html:
            entry["html"] = str(element)

        results.append(entry)

    return results
