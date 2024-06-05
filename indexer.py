import jieba
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from jieba.analyse import ChineseAnalyzer
import os
from models import NovelChapter

# 使用 jieba 分词器进行中文分词
analyzer = ChineseAnalyzer()

# 生成自定义词典文件
def generate_custom_dict(directory):
    authors = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                # 从文件名中提取作者名字
                novel_info = os.path.splitext(file)[0].split('_')
                if len(novel_info) == 2:
                    author = novel_info[1]
                    authors.add(author)
    # 写入自定义词典文件
    with open('custom_dict.txt', 'w', encoding='utf-8') as f:
        for author in authors:
            f.write(f"{author} 1000 nr\n")

# 加载自定义词典
def load_custom_dict():
    jieba.load_userdict('custom_dict.txt')

# 定义索引的 Schema，包含小说类型、名称、作者、章节号、章节名和URL字段
schema = Schema(
    novel_type=TEXT(stored=True, analyzer=analyzer),
    novel_name=TEXT(stored=True, analyzer=analyzer),
    novel_author=TEXT(stored=True, analyzer=analyzer),
    novel_chapter_num=TEXT(stored=True, analyzer=analyzer),
    novel_chapter_name=TEXT(stored=True, analyzer=analyzer),
    novel_chapter_url=ID(stored=True, unique=True)
)

# 创建索引目录
index_dir = "indexdir"
if not os.path.exists(index_dir):
    os.mkdir(index_dir)
    ix = create_in(index_dir, schema)
else:
    # 如果索引目录已经存在，删除旧索引
    for root, dirs, files in os.walk(index_dir):
        for file in files:
            os.remove(os.path.join(root, file))
    ix = create_in(index_dir, schema)

# 构建索引的函数
def build_index():
    writer = ix.writer()
    total_chapters = NovelChapter.select().count()
    print(f"总章节数: {total_chapters}")
    processed = 0
    for chapter in NovelChapter.select():
        try:
            writer.add_document(
                novel_type=chapter.novel_type,
                novel_name=chapter.novel_name,
                novel_author=chapter.novel_author,
                novel_chapter_num=chapter.novel_chapter_num,
                novel_chapter_name=chapter.novel_chapter_name,
                novel_chapter_url=chapter.novel_chapter_url
            )
            processed += 1
            if processed % 100 == 0:
                print(f"已处理章节数: {processed}/{total_chapters}")
        except Exception as e:
            print(f"索引时出错: {chapter.novel_name} - {chapter.novel_chapter_num} {chapter.novel_chapter_name} - {e}")
    writer.commit()

if __name__ == "__main__":
    # 使用实际的小说文件目录生成自定义词典
    generate_custom_dict('D:\\course\\Distributed_crawler\\crawl_book - turn_pages\\book_with_author')
    load_custom_dict()  # 加载自定义词典
    build_index()  # 构建索引
    print("索引构建完成")
