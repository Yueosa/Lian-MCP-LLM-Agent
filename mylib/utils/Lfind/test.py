from openai import OpenAI
from typing import List

from mylib import Sql, Loutput
from mylib.utils.Loutput import FontColor8
from mylib.sql import MemoryLog
from mylib.sql.Model.Enum import memory_log_role, memory_log_memory_type


sql = Sql()
lo = Loutput()
client = OpenAI(
    api_key="key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def test_message(content: str, embedding: List[float]) -> MemoryLog:
    return MemoryLog(
        user_id="embedding_test2",
        role=memory_log_role.system,
        content=content,
        embedding=embedding,
        memory_type=memory_log_memory_type.summary,
        importance=0.0
        )


def get_embedding(input: str) -> List[float]:
    return (client.embeddings.create(
        model="text-embedding-v4",
        input=input,
        dimensions=1536,
        encoding_format="float"
    )).data[0].embedding


def all_in() -> None:
    lo.lput("输入测试文本： ", font_color="cyan", end='')
    message: str = input()
    sql.Create_memory_log(test_message(message, get_embedding(message)))
    lo.lput("已存入, 正在查询...", font_color=FontColor8.YELLOW)
    print(sql.Read_memory_log(user_id="embedding_test"))

if __name__ == "__main__":
    all_in()
