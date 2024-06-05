from peewee import Model, CharField, MySQLDatabase
from settings import DATABASE

# 连接到 MySQL 数据库
db = MySQLDatabase(
    DATABASE['name'],
    user=DATABASE['user'],
    password=DATABASE['password'],
    host=DATABASE['host'],
    port=DATABASE['port']
)

# 定义 NovelChapter 模型来存储小说章节数据
class NovelChapter(Model):
    novel_type = CharField()  # 小说类型
    novel_name = CharField()  # 小说名称
    novel_author = CharField()  # 小说作者
    novel_chapter_num = CharField()  # 章节号
    novel_chapter_name = CharField()  # 章节名
    novel_chapter_url = CharField()  # 章节的URL

    class Meta:
        database = db  # 绑定到 MySQL 数据库

# 连接到数据库并创建表
db.connect()
db.create_tables([NovelChapter])
