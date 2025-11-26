"""文件操作算法模块（复制、移动、删除）"""

import aiofiles
from pathlib import Path


async def copy_file(
    src: Path,
    dest: Path,
    overwrite: bool = False,
) -> None:
    """
    复制文件
    
    参数:
        src: 源文件路径对象
        dest: 目标文件路径对象
        overwrite: 是否覆盖已存在的目标文件
    """
    if not src.exists():
        raise FileNotFoundError(f"源文件不存在: {src}")
    
    if dest.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在: {dest}")
    
    # 确保目标目录存在
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取源文件并写入目标文件
    async with aiofiles.open(src, "rb") as f:
        content = await f.read()
    
    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)


async def move_file(
    src: Path,
    dest: Path,
    overwrite: bool = False,
) -> None:
    """
    移动/重命名文件
    
    参数:
        src: 源文件路径对象
        dest: 目标文件路径对象
        overwrite: 是否覆盖已存在的目标文件
    """
    if not src.exists():
        raise FileNotFoundError(f"源文件不存在: {src}")
    
    if dest.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在: {dest}")
    
    # 确保目标目录存在
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # 使用 rename 移动文件
    src.rename(dest)


async def delete_file(path: Path) -> None:
    """
    删除文件
    
    参数:
        path: 文件路径对象
    """
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise ValueError(f"路径不是文件: {path}")
    
    path.unlink()
