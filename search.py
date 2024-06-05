from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh import scoring

def search_and_recommend(query_str):
    # 打开索引目录
    ix = open_dir("indexdir")

    # 创建查询解析器
    qp = QueryParser("novel_chapter_name", schema=ix.schema)  # 修改为实际要查询的字段

    # 解析查询字符串
    q = qp.parse(query_str)

    # 使用 BM25 模型进行搜索
    with ix.searcher(weighting=scoring.BM25F()) as s:
        results = s.search(q, limit=10)  # 限制返回最相关的十条数据
        for result in results:
            print(f"小说类型: {result['novel_type']}")
            print(f"小说名称: {result['novel_name']}")
            print(f"作者: {result['novel_author']}")  # 添加作者输出
            print(f"章节号: {result['novel_chapter_num']}")
            print(f"章节名: {result['novel_chapter_name']}")
            print(f"章节URL: {result['novel_chapter_url']}")
            print("=" * 50)

            # 推荐相关内容（同一类型的小说）
            recommend_related_content(s, result)
            # 推荐同一作者的其他小说
            recommend_author_works(s, result)

def recommend_related_content(searcher, result):
    # 创建推荐查询解析器，以小说类型为基础推荐同一类型的其他小说
    qp = QueryParser("novel_type", schema=searcher.schema)
    q = qp.parse(result["novel_type"])

    # 搜索同一类型的其他小说
    related_results = searcher.search(q, limit=5)
    print("推荐的同一类型的小说:")
    for related_result in related_results:
        if related_result["novel_name"] != result["novel_name"]:  # 排除当前小说
            print(f"小说类型: {related_result['novel_type']}")
            print(f"小说名称: {related_result['novel_name']}")
            print(f"作者: {related_result['novel_author']}")
            print(f"章节号: {related_result['novel_chapter_num']}")
            print(f"章节名: {related_result['novel_chapter_name']}")
            print(f"章节URL: {related_result['novel_chapter_url']}")
            print("-" * 50)

def recommend_author_works(searcher, result):
    # 创建推荐查询解析器，以作者为基础推荐同一作者的其他小说
    qp = QueryParser("novel_author", schema=searcher.schema)
    q = qp.parse(result["novel_author"])

    # 搜索同一作者的其他小说
    author_results = searcher.search(q, limit=5)
    print("推荐的同一作者的其他小说:")
    for author_result in author_results:
        if author_result["novel_name"] != result["novel_name"]:  # 排除当前小说
            print(f"小说类型: {author_result['novel_type']}")
            print(f"小说名称: {author_result['novel_name']}")
            print(f"作者: {author_result['novel_author']}")
            print(f"章节号: {author_result['novel_chapter_num']}")
            print(f"章节名: {author_result['novel_chapter_name']}")
            print(f"章节URL: {author_result['novel_chapter_url']}")
            print("-" * 50)

if __name__ == "__main__":
    query = input("请输入搜索关键词: ")
    search_and_recommend(query)
