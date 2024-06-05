from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser
from whoosh import scoring
import jieba

# ANSI 转义码颜色
HIGHLIGHT_COLOR = "\033[1;31m"  # 红色
RESET_COLOR = "\033[0m"  # 重置颜色


def highlight_text(text):
    if "<b class=\"match term0\">" in text:
        return text.replace('<b class="match term0">', HIGHLIGHT_COLOR).replace('</b>', RESET_COLOR)
    return text


def search_and_recommend(query_str):
    # 加载自定义词典
    jieba.load_userdict('custom_dict.txt')

    # 打开索引目录
    ix = open_dir("indexdir")

    # 创建多字段查询解析器
    qp = MultifieldParser(["novel_type", "novel_name", "novel_author", "novel_chapter_num", "novel_chapter_name"],
                          schema=ix.schema)

    # 解析查询字符串
    q = qp.parse(query_str)
    # print(f"解析后的查询: {q}")

    # 使用 BM25 模型进行搜索
    with ix.searcher(weighting=scoring.BM25F()) as s:
        results = s.search(q, limit=10)  # 限制返回最相关的十条数据
        print(f"最匹配的搜索结果[共{len(results)}条相关记录，显示匹配度最高的前10条]:")
        if len(results) == 0:
            print("没有找到匹配的结果")
        novel_types = []
        novel_authors = []
        seen_novels = set()
        for result in results:
            # 获取高亮的结果，若没有高亮内容则返回字段本身
            novel_type = highlight_text(result.highlights("novel_type") or result["novel_type"])
            novel_name = highlight_text(result.highlights("novel_name") or result["novel_name"])
            novel_author = highlight_text(result.highlights("novel_author") or result["novel_author"])
            novel_chapter_num = highlight_text(result.highlights("novel_chapter_num") or result["novel_chapter_num"])
            novel_chapter_name = highlight_text(result.highlights("novel_chapter_name") or result["novel_chapter_name"])

            print(f"小说类型: {novel_type}")
            print(f"小说名称: {novel_name}")
            print(f"作者: {novel_author}")
            print(f"章节号: {novel_chapter_num}")
            print(f"章节名: {novel_chapter_name}")
            print(f"章节URL: {result['novel_chapter_url']}")
            print("=" * 50)

            seen_novels.add(result["novel_name"])
            if result["novel_type"] not in novel_types:
                novel_types.append(result["novel_type"])
            if result["novel_author"] not in novel_authors:
                novel_authors.append(result["novel_author"])

            if len(novel_types) >= 5 and len(novel_authors) >= 5:
                break

        # print("novel_types:", novel_types)
        # print("\n")
        # print("novel_authors:", novel_authors)
        # print("\n")

        # 推荐内容
        print("----------------------------------------------------------------------------------------------------------------------------------------------------")
        print("------------------------------------------------------------------*****推荐阅读*****------------------------------------------------------------------")
        # 推荐同类型的小说
        recommended_types = recommend_by_field(s, "novel_type", novel_types, 5, seen_novels, ix)
        for rec in recommended_types:
            print(f"小说类型: {rec['小说类型']}")
            print(f"小说名称: {rec['小说名称']}")
            print(f"作者: {rec['作者']}")
            print(f"章节号: {rec['章节号']}")
            print(f"章节名: {rec['章节名']}")
            print(f"章节URL: {rec['章节URL']}")
            print("=" * 50)

        # 推荐同作者的小说
        recommended_authors = recommend_by_field(s, "novel_author", novel_authors, 5, seen_novels, ix)
        for rec in recommended_authors:
            print(f"小说类型: {rec['小说类型']}")
            print(f"小说名称: {rec['小说名称']}")
            print(f"作者: {rec['作者']}")
            print(f"章节号: {rec['章节号']}")
            print(f"章节名: {rec['章节名']}")
            print(f"章节URL: {rec['章节URL']}")
            print("=" * 50)


def recommend_by_field(searcher, field, values, limit, seen_novels, ix):
    recommendations = []
    unique_recommendations = set()
    num_values = len(values)

    if num_values >= 5:
        for value in values[:5]:
            add_recommendations(searcher, field, value, recommendations, unique_recommendations, seen_novels, ix, limit)
    else:
        for value in values:
            add_recommendations(searcher, field, value, recommendations, unique_recommendations, seen_novels, ix, 1)
        first_value = values[0]
        additional_needed = 5 - num_values + 1
        add_recommendations(searcher, field, first_value, recommendations, unique_recommendations, seen_novels, ix,
                            additional_needed)

    return recommendations


def add_recommendations(searcher, field, value, recommendations, unique_recommendations, seen_novels, ix, needed):
    qp = MultifieldParser([field], schema=ix.schema)
    q = qp.parse(value)
    results = searcher.search(q, limit=needed * 2)  # 加大搜索范围以确保足够的推荐量
    for result in results:
        novel_info = {
            "小说类型": result["novel_type"],
            "小说名称": result["novel_name"],
            "作者": result["novel_author"],
            "章节号": result["novel_chapter_num"],
            "章节名": result["novel_chapter_name"],
            "章节URL": result["novel_chapter_url"]
        }
        # 确保推荐的小说是唯一的且未被推荐过
        if novel_info["小说名称"] not in unique_recommendations and novel_info["小说名称"] not in seen_novels:
            unique_recommendations.add(novel_info["小说名称"])
            recommendations.append(novel_info)
        if len(recommendations) >= needed:
            break


if __name__ == "__main__":
    query = input("请输入搜索关键词: ")
    search_and_recommend(query)
