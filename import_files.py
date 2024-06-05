import os
import chardet
from models import NovelChapter

# 检测文件编码
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    return result['encoding']

# 导入文件数据
def import_files(directory):
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            novel_type = dir_name  # 小说类型是文件夹名称
            dir_path = os.path.join(root, dir_name)
            for novel_file in os.listdir(dir_path):
                if novel_file.endswith('.txt'):
                    # 从文件名中提取小说名和作者名
                    novel_info = os.path.splitext(novel_file)[0].split('_')
                    if len(novel_info) == 2:
                        novel_name, novel_author = novel_info
                    else:
                        novel_name = novel_info[0]
                        novel_author = '未知'

                    file_path = os.path.join(dir_path, novel_file)
                    encoding = detect_encoding(file_path)  # 检测文件编码
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                            lines = f.readlines()
                            for line in lines:
                                parts = line.strip().split(': ')
                                if len(parts) == 2:
                                    chapter_info = parts[0].split(' ')
                                    if len(chapter_info) == 2:
                                        novel_chapter_num = chapter_info[0]
                                        novel_chapter_name = chapter_info[1]
                                        novel_chapter_url = parts[1]
                                        try:
                                            # 将数据保存到数据库
                                            NovelChapter.create(
                                                novel_type=novel_type,
                                                novel_name=novel_name,
                                                novel_author=novel_author,
                                                novel_chapter_num=novel_chapter_num,
                                                novel_chapter_name=novel_chapter_name,
                                                novel_chapter_url=novel_chapter_url
                                            )
                                            print(f"已导入: {novel_name} - {novel_chapter_num} {novel_chapter_name}")
                                        except Exception as e:
                                            print(f"导入时出错: {novel_name} - {novel_chapter_num} {novel_chapter_name} - {e}")
                    except UnicodeDecodeError as e:
                        print(f"文件解码错误: {file_path} - {e}")

if __name__ == "__main__":
    import_files('D:\\course\\Distributed_crawler\\crawl_book - turn_pages\\book_with_author')  # 使用实际的小说文件目录