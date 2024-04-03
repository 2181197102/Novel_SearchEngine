import os
import re
import random
from urllib.request import Request, urlopen
from lxml import etree
import threading
from settings import UA, HOST, BASE_DIR

# 检查URL是否已经被访问过
def is_url_visited(url, visited_urls):
    return url in visited_urls

# 获取网页内容
def get_page(url):
    req = Request(url)
    req.add_header('User-Agent', random.choice(UA))
    try:
        with urlopen(req, timeout=60) as response:
            page = response.read().decode('gbk', 'ignore')
        return page
    except Exception as e:
        print(f"获取页面时出错: {e}")
        return "error"

# 爬取具体内容页面
def crawl_source_page(url, filedir, filename, visited_urls):
    page = get_page(url)
    if page == "error":
        return
    visited_urls.append(url)
    tree = etree.HTML(page)
    nodes = tree.xpath("//div[@id='list']//dl//dd//a")
    source_file_path = os.path.join(filedir, f"{filename}.txt")

    with open(source_file_path, 'w') as f:
        print(f"{source_file_path} 打开成功!")
        for node in nodes:
            source_url = node.xpath("@href")[0]
            source_text = node.xpath("text()")[0]

            if re.search("html$", source_url):
                f.write(f"{source_text}: {url}{source_url}\n")
    print(f"{source_file_path} 内容写入完毕!")

# 爬取列表页面
def crawl_list_page(index_url, filedir, visited_urls):
    print(f"处理类别页面: {index_url}")
    print("------------------------------\n")
    page = get_page(index_url)
    if page == "error":
        return
    visited_urls.append(index_url)
    tree = etree.HTML(page)
    nodes = tree.xpath("//div[@id='newscontent']//div//ul//li//span[@class='s2']//a")

    for node in nodes:
        url = node.xpath("@href")[0]
        print(f"book_content_url: {url}")

        if re.match(r'^https://', url):
            if is_url_visited(url, visited_urls):
                pass
            else:
                filename = re.sub(r'[\\/:*?"<>|]', ' ', node.xpath("text()")[0])
                crawl_source_page(url, filedir, filename, visited_urls)
        else:
            print(f"进一步嵌套以进行分页: {url}")
            index = index_url.rfind("/")
            base_url = index_url[:index + 1]
            page_url = base_url + url
            if not is_url_visited(page_url, visited_urls):
                print(f"进一步嵌套以进行分页: {page_url}")
                crawl_list_page(page_url, filedir, visited_urls)

# 爬取主页
def crawl_index_page(start_url):
    print("抓取主页...")
    page = get_page(start_url)
    if page == "error":
        return
    tree = etree.HTML(page)
    nodes = tree.xpath("//div[@class='nav']//ul//li//a")
    visited_urls = []

    for node in nodes:
        url = node.xpath("@href")[0]

        if re.match(r'^/[^/]*/$', url):
            if is_url_visited(url, visited_urls):
                print("已经访问过，passing...")
                pass
            else:
                visited_urls.append(HOST + url)
                print("----------创建类别目录----------")
                catalog = node.xpath("text()")[0]
                new_dir = os.path.join(BASE_DIR, catalog)
                os.makedirs(new_dir, exist_ok=True)
                print(f"类别目录创建成功: {new_dir}")
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
        crawl_list_page(self.url, self.new_dir, self.visited_urls)
