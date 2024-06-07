import random
from flask import Flask, request, render_template
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import Term, Or
from whoosh import scoring
import jieba

app = Flask(__name__)

# ANSI 转义码颜色
HIGHLIGHT_COLOR = "<span style='color:red'>"
RESET_COLOR = "</span>"

def highlight_text(text):
    if "<b class=\"match term0\">" in text:
        return text.replace('<b class="match term0">', HIGHLIGHT_COLOR).replace('</b>', RESET_COLOR)
    return text

def search_and_recommend(query_str):
    jieba.load_userdict('custom_dict.txt')
    ix = open_dir("indexdir")
    qp = MultifieldParser(
        ["novel_type", "novel_name", "novel_author", "novel_chapter_num", "novel_chapter_name"],
        schema=ix.schema,
        group=OrGroup
    )

    q = qp.parse(query_str)

    # 手动设置字段权重
    weighted_query = Or([
        Term("novel_name", query_str, boost=300),
        Term("novel_author", query_str, boost=250),
        Term("novel_chapter_name", query_str, boost=145)
    ])

    with ix.searcher(weighting=scoring.BM25F()) as s:
        results = s.search(weighted_query, limit=10)
        if len(results) == 0:
            return {"results": [], "recommendations": []}

        search_results = []
        novel_types = []
        novel_authors = []
        seen_novels = set()

        for result in results:
            search_results.append({
                "novel_type": highlight_text(result.highlights("novel_type") or result["novel_type"]),
                "novel_name": highlight_text(result.highlights("novel_name") or result["novel_name"]),
                "novel_author": highlight_text(result.highlights("novel_author") or result["novel_author"]),
                "novel_chapter_num": highlight_text(result.highlights("novel_chapter_num") or result["novel_chapter_num"]),
                "novel_chapter_name": highlight_text(result.highlights("novel_chapter_name") or result["novel_chapter_name"]),
                "novel_chapter_url": result["novel_chapter_url"]
            })
            seen_novels.add(result["novel_name"])
            if result["novel_type"] not in novel_types:
                novel_types.append(result["novel_type"])
            if result["novel_author"] not in novel_authors:
                novel_authors.append(result["novel_author"])

            if len(novel_types) >= 5 and len(novel_authors) >= 5:
                break

        recommended_types = recommend_by_field(s, "novel_type", novel_types, seen_novels, ix)
        recommended_authors = recommend_by_field(s, "novel_author", novel_authors, seen_novels, ix)

        # 将推荐结果混合，并随机选择其中的结果
        recommendations = recommended_types + recommended_authors
        random.shuffle(recommendations)
        return {
            "results": search_results,
            "recommendations": random.sample(recommendations, 5) if len(recommendations) >= 5 else recommendations
        }

def recommend_by_field(searcher, field, values, seen_novels, ix):
    recommendations = []
    unique_recommendations = set()

    for value in values:
        qp = MultifieldParser([field], schema=ix.schema)
        q = qp.parse(value)
        results = searcher.search(q, limit=10000)  # 增加limit以获取更多的推荐结果
        # print(f"推荐的{field}为{value}的结果数量: {len(results)}")
        # # 打印前五个
        # for result in results[:10]:
        #     print(f"小说类型: {result['novel_type']}")
        #     print(f"小说名称: {result['novel_name']}")
        #     print(f"作者: {result['novel_author']}")
        #     print(f"章节号: {result['novel_chapter_num']}")
        #     print(f"章节名: {result['novel_chapter_name']}")
        #     print(f"章节URL: {result['novel_chapter_url']}")
        #     print("=" * 50)
        #
        # # 打印最后五个
        # for result in results[-5:]:
        #     print(f"小说类型: {result['novel_type']}")
        #     print(f"小说名称: {result['novel_name']}")
        #     print(f"作者: {result['novel_author']}")
        #     print(f"章节号: {result['novel_chapter_num']}")
        #     print(f"章节名: {result['novel_chapter_name']}")
        #     print(f"章节URL: {result['novel_chapter_url']}")
        #     print("=" * 50)

        field_recommendations = []

        for result in results:
            novel_info = {
                "novel_type": result["novel_type"],
                "novel_name": result["novel_name"],
                "novel_author": result["novel_author"],
                "novel_chapter_num": result["novel_chapter_num"],
                "novel_chapter_name": result["novel_chapter_name"],
                "novel_chapter_url": result["novel_chapter_url"]
            }
            if novel_info["novel_name"] not in unique_recommendations and novel_info["novel_name"] not in seen_novels:
                unique_recommendations.add(novel_info["novel_name"])
                field_recommendations.append(novel_info)

        # # 打印seen_novels
        # print("seen_novels:")
        # for novel in seen_novels:
        #     print(novel)
        # # 打印unique_recommendations
        # print("unique_recommendations:")
        # for novel in unique_recommendations:
        #     print(novel)
        # 打印field_recommendations
        print("field_recommendations:")
        for novel in field_recommendations:
            print(novel)
        random.shuffle(field_recommendations)
        recommendations.extend(field_recommendations[:2])  # 每个类型选择随机的两本

    random.shuffle(recommendations)
    return recommendations

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        search_results = search_and_recommend(query)
        return render_template("index.html", query=query, results=search_results["results"],
                               recommendations=search_results["recommendations"])
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)