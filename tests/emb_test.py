import base

from mylib.kit.Lfind import get_embedding
from mylib.kit.Loutput import Loutput
from mylib.lian_orm import (
    Sql,
    MemoryLog,
    MemoryLogRole,
    MemoryLogMemoryType,
)

sql = Sql()
lo = Loutput()


# -----------
# 测试消息列表
# -----------
test_messages = [

]


def emb() -> None:
    while True:
        msg = input("msg: ")
        emb = get_embedding(msg)

        res = sql.memory_log.search_by_embedding(emb, 3)

        for i in res:
            lo.lput(i['id'], i['user_id'], i['content'], font_color=35)


def cql_batch(msg_list: list[str]):
    """
    批量插入消息，直接录入数据库
    """
    for msg in msg_list:
        mql = MemoryLog(
            user_id="test_lian",
            role=MemoryLogRole.USER,
            content=msg,
            embedding=get_embedding(msg),
            memory_type=MemoryLogMemoryType.CONVERSATION,
            importance=0.0,
        )
        created = sql.Create_memory_log(mql)
        lo.lput(f"Inserted ID={created.id}", "test_lian", msg, font_color=36)


if __name__ == "__main__":
    # 批量插入
    # cql_batch(test_messages)

    # 测试embedding检索
    emb()
