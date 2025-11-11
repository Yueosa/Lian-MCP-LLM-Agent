import aiofiles
from pathlib import Path

class FileTools:
    async def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except Exception as e:
            return f"读取文件错误: {str(e)}"
    
    async def write_file(self, file_path: str, content: str) -> str:
        """写入文件内容"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return f"文件已成功写入: {file_path}"
        except Exception as e:
            return f"写入文件错误: {str(e)}"
    
    async def list_directory(self, directory: str) -> list:
        """列出目录内容"""
        try:
            path = Path(directory)
            if not path.exists():
                return f"目录不存在: {directory}"
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            return items
        except Exception as e:
            return f"列出目录错误: {str(e)}"
