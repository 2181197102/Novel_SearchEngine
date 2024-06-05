---
 智能搜索引擎技术                                                                                      	                                           大数据2101 左阳        			
---

# 智能搜索引擎技术实验报告





## 项目整体架构设计

### 1. 项目目录结构

```

Book_SearchEngine/
├── book_with_author/      # 保存爬取的小说内容
├── functions.py           # 爬虫核心功能模块
├── import_files.py        # 数据导入模块
├── indexer.py             # 索引构建模块
├── craw_main.py           # 程序入口
├── models.py              # 数据库模型
├── settings.py            # 配置文件
└── README.md              # 项目说明
```

#### 2. 模块功能概述

##### 2.1 配置文件 (`settings.py`)

配置文件包含爬虫运行所需的全局设置，包括用户代理、主机地址、数据库连接信息等。

##### 2.2 爬虫核心功能模块 (`functions.py`)

该模块实现了爬虫的核心功能，包括：

- **检查URL是否访问过**：避免重复爬取。
- **获取网页内容**：发送HTTP请求并获取网页内容，支持重试机制。
- **爬取具体内容页面**：从小说页面中提取章节信息并保存到本地文本文件。
- **爬取列表页面**：从类别页面中提取小说链接及信息，并进一步爬取具体内容。
- **爬取主页**：从主页开始，依次爬取各个类别的小说列表页面。

##### 2.3 数据导入模块 (`import_files.py`)

该模块负责将爬取的小说数据导入到数据库中，主要步骤包括：

- **检测文件编码**：确保文件可以正确读取。
- **读取文件内容**：解析小说章节信息。
- **保存到数据库**：将解析到的数据保存到数据库中。

##### 2.4 索引构建模块 (`indexer.py`)

该模块负责将存储在数据库中的小说数据建立倒排索引库，以支持高效的全文检索。主要步骤包括：

- **定义索引Schema**：指定需要索引的字段。
- **创建索引目录**：初始化索引存储位置。
- **构建索引**：从数据库中读取数据，并建立索引。

##### 2.5 数据库模型 (`models.py`)

该模块定义了数据库模型，描述了数据表结构。主要包括：

- **小说类型**
- **小说名称**
- **小说作者**
- **章节号**
- **章节名**
- **章节URL**

##### 2.6 爬虫程序入口 (`craw_main.py`)

爬虫程序的入口文件，负责启动爬虫项目。通过调用 `functions.py` 中的核心函数开始爬取任务。

#### 3. 工作流程

1. **启动爬虫**： 运行 `craw_main.py`，从配置的 `START_URL` 开始爬取主页内容。
2. **爬取主页**： 从主页提取各个小说类别的链接，并为每个类别创建独立的目录。
3. **爬取类别页面**： 从每个类别页面提取小说的链接、名称和作者信息，并保存到相应目录。
4. **爬取小说内容**： 进入每个小说链接页面，提取章节信息并保存到本地文本文件中。
5. **数据导入**： 运行 `import_files.py`，将本地文本文件中的小说数据解析并导入到数据库中。
6. **建立索引**： 运行 `indexer.py`，从数据库中读取数据，并建立倒排索引库，支持全文检索。

### 架构图

```
              +----------------------+
              |    配置文件 settings.py   |
              +-----------+----------+
                          |
                          v
              +-----------+----------+
              |  程序入口 craw_main.py  |
              +-----------+----------+
                          |
                          v
              +-----------+----------+
              |   爬虫功能 functions.py  |
              +-----------+----------+
                          |
            +-------------+-------------+
            |                           |
            v                           v
+-----------+----------+      +---------+----------+
| 爬取主页 crawl_index_page |  | 爬取列表页 crawl_list_page |
+-----------+----------+      +---------+----------+
                          |
                          v
              +-----------+----------+
              | 爬取内容页 crawl_source_page |
              +-----------+----------+
                          |
                          v
              +-----------+----------+
              |  数据导入 import_files.py  |
              +-----------+----------+
                          |
                          v
              +-----------+----------+
              | 数据库模型 models.py     |
              +-----------+----------+
                          |
                          v
              +-----------+----------+
              |  索引构建 indexer.py     |
              +----------------------+
```





## 一、爬虫

### 1.网页内容爬取设计

在本次实验中，我们设计并实现了一个多线程的网页爬虫，旨在从小说网站中提取小说目录及章节信息，并将这些数据存储到本地的文本文件中。爬虫的设计分为以下几个部分：

##### 1.1 爬虫整体架构

爬虫的整体架构如下：

1. **入口函数**：`crawl_index_page` 函数从主页开始，爬取各个类别的小说列表页面。
2. **列表页面爬取**：`crawl_list_page` 函数爬取每个类别页面中的具体小说链接和相关信息。
3. **内容页面爬取**：`crawl_source_page` 函数爬取具体小说的章节信息并将其保存到文本文件中。
4. **多线程支持**：使用 `threading` 模块来提高爬取速度，防止阻塞。

##### 1.2 代码实现

以下是实现该爬虫的具体代码：

```py
python复制代码import os
import re
import random
import time
from urllib.request import Request, urlopen
from lxml import etree
import threading
from settings import UA, HOST, BASE_DIR

# 检查URL是否已经被访问过
def is_url_visited(url, visited_urls):
    return url in visited_urls

# 获取网页内容
def get_page(url, retries=3):
    # 构造请求对象，设置User-Agent头部信息
    req = Request(url)
    req.add_header('User-Agent', random.choice(UA))
    try:
        # 发送请求并获取响应
        with urlopen(req, timeout=60) as response:
            # 读取响应内容并解码
            page = response.read().decode('gbk', 'ignore')
        return page
    except Exception as e:
        if retries > 0:
            print(f"获取页面时出错: {e}, 重试中... ({retries})")
            time.sleep(random.uniform(1, 3))  # 添加随机延时
            return get_page(url, retries - 1)
        else:
            print(f"获取页面失败: {e}")
            return "error"

# 爬取具体内容页面
def crawl_source_page(url, filedir, filename, visited_urls):
    # 获取页面内容
    page = get_page(url)
    # 如果获取页面内容失败，则直接返回
    if page == "error":
        return
    # 将当前URL添加到已访问列表中
    visited_urls.append(url)
    # 使用lxml解析页面内容
    tree = etree.HTML(page)
    # 使用XPath定位需要提取的节点
    nodes = tree.xpath("//div[@id='list']//dl//dd//a")
    # 拼接保存文件的路径
    source_file_path = os.path.join(filedir, f"{filename}.txt")

    # 打开文件并写入内容
    with open(source_file_path, 'w', encoding='utf-8') as f:
        print(f"{source_file_path} 打开成功!")
        # 遍历节点列表，提取链接和文本内容，并写入文件
        for node in nodes:
            source_url = node.xpath("@href")[0]
            source_text = node.xpath("text()")[0]
            # 如果链接以html结尾，则写入文件
            if re.search("html$", source_url):
                f.write(f"{source_text}: {url}{source_url}\n")
    # 写入完毕后打印提示信息
    print(f"{source_file_path} 内容写入完毕!")

# 爬取列表页面
def crawl_list_page(index_url, filedir, visited_urls):
    # 打印正在处理的类别页面URL
    print(f"处理类别页面: {index_url}")
    print("------------------------------\n")
    # 获取页面内容
    page = get_page(index_url)
    # 如果获取页面内容失败，则直接返回
    if page == "error":
        return
    # 将当前URL添加到已访问列表中
    visited_urls.append(index_url)
    # 使用lxml解析页面内容
    tree = etree.HTML(page)
    # 使用XPath定位需要提取的节点
    nodes = tree.xpath("//div[@id='newscontent']//div//ul//li")

    # 遍历节点列表
    for node in nodes:
        # 获取节点中的链接和文本内容
        book_url = node.xpath(".//span[@class='s2']//a/@href")[0]
        book_name = node.xpath(".//span[@class='s2']//a/text()")[0]
        author_name = node.xpath(".//span[@class='s4']/text()")[0]
        print(f"book_content_url: {book_url}")

        # 拼接文件名
        filename = f"{book_name}_{author_name}".replace("/", "_").replace("\\", "_")

        # 如果链接以https开头
        if re.match(r'^https://', book_url):
            # 如果已经访问过，则跳过
            if is_url_visited(book_url, visited_urls):
                pass
            else:
                # 调用crawl_source_page函数处理
                crawl_source_page(book_url, filedir, filename, visited_urls)
                time.sleep(random.uniform(1, 3))  # 添加随机延时
        else:
            # 如果链接不是以https开头，则进行进一步嵌套以进行分页
            print(f"进一步嵌套以进行分页: {book_url}")
            index = index_url.rfind("/")
            base_url = index_url[:index + 1]
            page_url = base_url + book_url
            # 如果未访问过，则递归调用crawl_list_page函数处理
            if not is_url_visited(page_url, visited_urls):
                print(f"进一步嵌套以进行分页: {page_url}")
                crawl_list_page(page_url, filedir, visited_urls)
                time.sleep(random.uniform(1, 3))  # 添加随机延时

# 爬取主页
def crawl_index_page(start_url):
    # 打印抓取主页的提示信息
    print("抓取主页...")
    # 获取主页内容
    page = get_page(start_url)
    # 如果获取页面内容失败，则直接返回
    if page == "error":
        return
    # 使用lxml解析页面内容
    tree = etree.HTML(page)
    # 使用XPath定位需要提取的节点
    nodes = tree.xpath("//div[@class='nav']//ul//li//a")
    # 初始化已访问URL列表
    visited_urls = []

    # 遍历节点列表
    for node in nodes:
        # 获取节点中的链接
        url = node.xpath("@href")[0]

        # 如果链接以指定格式开头
        if re.match(r'^/[^/]*/$', url):
            # 如果已经访问过，则跳过
            if is_url_visited(url, visited_urls):
                print("已经访问过，passing...")
                pass
            else:
                # 否则，将链接添加到已访问列表中，并创建目录
                visited_urls.append(HOST + url)
                print("----------创建类别目录----------")
                catalog = node.xpath("text()")[0]
                new_dir = os.path.join(BASE_DIR, catalog)
                os.makedirs(new_dir, exist_ok=True)
                print(f"类别目录创建成功: {new_dir}")
                # 创建自定义线程并启动
                thread = MyThread(HOST + url, new_dir, visited_urls)
                thread.start()

# 自定义线程类
class MyThread(threading.Thread):
    def __init__(self, url, new_dir, visited_urls):
        threading.Thread.__init__(self)
        self.url = url
        self.new_dir = new_dir
        self.visited_urls = visited_urls

    def run(self):
        # 调用crawl_list_page函数处理类别页面
        crawl_list_page(self.url, self.new_dir, self.visited_urls)
```

##### 1.3 代码详解

1. **获取网页内容 (`get_page` 函数)**： 该函数发送 HTTP 请求获取网页内容，如果请求失败则进行最多三次重试。在每次重试之间添加一个随机延时，以防止频繁请求被目标服务器拒绝。
2. **爬取具体内容页面 (`crawl_source_page` 函数)**： 该函数从具体的小说页面中提取章节信息，并将章节名称和 URL 写入到本地文本文件中。
3. **爬取列表页面 (`crawl_list_page` 函数)**： 该函数处理每个类别页面，提取小说链接、名称和作者信息，并调用 `crawl_source_page` 函数爬取具体小说的章节内容。
4. **爬取主页 (`crawl_index_page` 函数)**： 该函数从主页开始，爬取各个类别页面的链接，并为每个类别创建一个独立的目录。然后，为每个类别页面创建一个线程进行爬取。
5. **自定义线程类 (`MyThread` 类)**： 该类继承自 `threading.Thread`，用于并发处理不同类别页面的爬取任务。

##### 1.4本地数据存储展示

小说类别作为文件名：

![image-20240605123924733](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605123924733.png)

小说名与小说作者拼接作为.txt文件名称（格式为：小说名_作者）：

![image-20240605123947457](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605123947457.png)

.txt文件内部存储整本小说的所有章节、章节名、章节url：

![image-20240605124046121](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605124046121.png)



### 2.反制反爬虫机制：

#### 2.1随机'User-Agent'

引入大量的'User-Agent'，并在请求时使用“random()”随机调用，以达到模拟不同主机访问，防止被反爬虫而中断。

> ./settings.py  UA

![image-20240605124406262](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605124406262.png)





#### 2.2随机延时重试

网页获取失败时，可能是由于网络波动，也有可能是被反爬虫机制检测到了，于是设置随机延时后进行重试。

> ./functions.py

```py
    except Exception as e:
        if retries > 0:
            print(f"获取页面时出错: {e}, 重试中... ({retries})")
            time.sleep(random.uniform(1, 3))  # 添加随机延时
            return get_page(url, retries - 1)
        else:
            print(f"获取页面失败: {e}")
            return "error"
```

![image-20240605131540994](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605131540994.png)



### 3.爬取效率优化

采用多线程分布式爬取，以提高效率，并且配合随机UA，模拟多台不同主机的并发访问。

```py
class MyThread(threading.Thread):
    def __init__(self, url, new_dir, visited_urls):
        threading.Thread.__init__(self)
        self.url = url
        self.new_dir = new_dir
        self.visited_urls = visited_urls

    def run(self):
        # 调用crawl_list_page函数处理类别页面
        crawl_list_page(self.url, self.new_dir, self.visited_urls)
```



### 4.爬取过程控制台输出截图

![image-20240605131639785](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605131639785.png)





## 二、数据处理并导入数据库

### 1. 数据处理流程

在本次实验中，我从多个包含小说数据的文本文件中提取信息，并将其存储到 MySQL 数据库中。数据处理主要分为以下几个步骤：

1. **检测文件编码**： 使用 `chardet` 库检测每个文本文件的编码，以确保文件能够被正确读取。
2. **提取文件名中的小说信息**： 从文本文件名中提取小说的名称和作者名，并将这部分信息与小说章节数据一起保存到数据库中。
3. **读取文件内容**： 逐行读取文本文件内容，并解析其中的章节号、章节名以及章节的 URL。
4. **保存到数据库**： 使用 `peewee` 库将提取到的小说信息和章节数据存储到 MySQL 数据库中。

### 2. 数据库模型设计

在 `models.py` 文件中，我们定义了一个 `NovelChapter` 模型来表示数据库中的一张表。表结构如下：

- `novel_type`：小说类型
- `novel_name`：小说名称
- `novel_author`：小说作者
- `novel_chapter_num`：章节号
- `novel_chapter_name`：章节名
- `novel_chapter_url`：章节的 URL

**models.py**：

```py
python复制代码from peewee import Model, CharField, MySQLDatabase
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
```

### 3. 数据处理与导入实现

在 `import_files.py` 文件中实现了数据处理和导入数据库的逻辑：

**import_files.py**：

```py
python复制代码import os
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
```



### 4.数据处理以及导入过程控制台截图

![image-20240605131758271](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605131758271.png)



### 5.数据库数据展示

![image-20240605130904448](C:\Users\21811\AppData\Roaming\Typora\typora-user-images\image-20240605130904448.png)





