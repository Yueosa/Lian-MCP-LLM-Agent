import aiohttp

class WebTools:
    async def fetch_webpage(self, url: str) -> str:
        """获取网页内容"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # 返回前1000个字符作为预览
                        # return content[:3000] + "..." if len(content) > 3000 else content
                        return content
                    else:
                        return f"HTTP错误: {response.status}"
        except Exception as e:
            return f"网络请求错误: {str(e)}"
    
    async def check_url_status(self, url: str) -> dict:
        """检查URL状态"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return {
                        "url": url,
                        "status_code": response.status,
                        "content_type": response.headers.get('content-type', 'unknown')
                    }
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "error": str(e)
            }
