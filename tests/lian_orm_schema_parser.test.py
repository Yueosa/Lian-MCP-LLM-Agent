import base
from mylib.lian_orm.schema import SqlParser

sql = SqlParser()

print(sql.parse_file(file_path="mylib/lian_orm/schema/localfile/LML_SQL.sql"))
