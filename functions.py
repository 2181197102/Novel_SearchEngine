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
        # 打印错误信息并返回错误标记
        print(f"获取页面时出错: {e}")
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
    with open(source_file_path, 'w') as f:
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
    nodes = tree.xpath("//div[@id='newscontent']//div//ul//li//span[@class='s2']//a")

    # 遍历节点列表
    for node in nodes:
        # 获取节点中的链接
        url = node.xpath("@href")[0]
        print(f"book_content_url: {url}")

        # 如果链接以https开头
        if re.match(r'^https://', url):
            # 如果已经访问过，则跳过
            if is_url_visited(url, visited_urls):
                pass
            else:
                # 否则，提取链接中的文本，并调用crawl_source_page函数处理
                filename = re.sub(r'[\\/:*?"<>|]', ' ', node.xpath("text()")[0])
                crawl_source_page(url, filedir, filename, visited_urls)
        else:
            # 如果链接不是以https开头，则进行进一步嵌套以进行分页
            print(f"进一步嵌套以进行分页: {url}")
            index = index_url.rfind("/")
            base_url = index_url[:index + 1]
            page_url = base_url + url
            # 如果未访问过，则递归调用crawl_list_page函数处理
            if not is_url_visited(page_url, visited_urls):
                print(f"进一步嵌套以进行分页: {page_url}")
                crawl_list_page(page_url, filedir, visited_urls)

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
