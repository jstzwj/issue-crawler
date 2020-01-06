'''
统计各个项目不同label的数量
'''

import requests
from lxml import etree
import time
import datetime
import json

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

async def parse_html(html):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda :etree.HTML(html))
    return result

class GithubSpider(solavis.Spider):
    start_urls = ['https://github.com/jstzwj']
    def __init__(self):
        pass

    async def parse(self, response):
        html = response.text
        # print(response.status)
        html_root = await parse_html(html)

        # get following
        await self.request(response.url + "?tab=following", self.parse_following)

    async def parse_following(self, response):
        html = response.text
        html_root = await parse_html(html)

        for each in html_root.xpath('//span[@class="link-gray pl-1"]/text()'):
            await self.request(each, self.parse)

        pagination = response.xpath('//div[@class="paginate-container"]')
        previous = pagination.xpath('.//a[text()="Previous"]/@href').get()
        next = pagination.xpath('.//a[text()="Next"]/@href').get()

        if next is not None:
            print(next)
            await self.request(next, self.parse_following)
        else:
            # get more users
            for each in user_data['following']:
                yield scrapy.Request(url='https://github.com/{login}'.format(login=each),
                callback=self.parse,
                dont_filter=False)

            user_data['scraped_time'] = datetime.now()
            yield user_data

    async def parse_star(self, response):
        pass

class JsonPipeline(solavis.Pipeline):
    def __init__(self):
        pass

    async def open_spider(self):
        self.save_path = "items.txt"
        self.file = open(self.save_path, 'w', encoding='utf-8')

    async def close_spider(self):
        self.file.close()

    async def process_item(self, item):
        self.file.write(json.dumps(item, cls=DateTimeEncoder) + "\n")


proxies = {'http' : 'http://localhost:10805', 'https': 'https://localhost:10805'}

class Request(object):
    def __init__(self, url, fn, meta=None):
        super().__init__()
        self.url = url
        self.fn = fn
        self.meta = meta

    def crawl(self):
        if self.fn is not None and self.url is not None:
            print(f'crawl: {self.url}')
            self.fn(self.url, self.meta)

class Crawler(object):
    def __init__(self, path="items.txt"):
        super().__init__()
        self.requests_list = []
        self.save_path = path
        self.repo_filter = set()
        self.user_filter = set()
        self.file = open(self.save_path, 'w', encoding='utf-8')

    def __del__(self):
        self.file.close()

    def request_page(self, url):
        html_text = requests.get(url, timeout=15, proxies=proxies).text
        html_root = etree.HTML(html_text)
        return html_root

    def save_item(self, item):
        self.file.write(json.dumps(item, cls=DateTimeEncoder) + "\n")

    def request(self, url, fn, meta=None):
        self.requests_list.append(Request(url, fn, meta))
    
    def main(self):
        username = 'jstzwj'
        self.request(f'https://github.com/{username}', self.get_user)
        try:
            while True:
                if len(self.requests_list) > 0 :
                    req = self.requests_list.pop(0)
                    try:
                        req.crawl()
                    except Exception as e:
                        print(e)
                        self.requests_list.append(req)
                else:
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        
        print('crawl finish')


    def get_user(self, url, meta):
        self.request(url + '?tab=following', self.get_following, [])
        self.request(url + '?tab=stars', self.get_star, [])

    def get_following(self, url, meta):
        html_root = self.request_page(url)
        for each in html_root.xpath('//span[@class="link-gray pl-1"]/text()'):
            meta.append(each)
            self.request(each, self.get_user)

        pagination = html_root.xpath('//div[@class="paginate-container"]')
        previous = pagination.xpath('.//a[text()="Previous"]/@href').get()
        next = pagination.xpath('.//a[text()="Next"]/@href').get()

        if next is not None:
            print(next)
            self.request(next, self.get_following, meta)
        else:
            # get more users
            for each in meta:
                if each not in self.user_filter:
                    self.request(f'https://github.com/{each}', self.get_user)
                    self.user_filter.add(each)

    def get_star(self, url, meta):
        html_root = self.request_page(url)
        for each in html_root.xpath('//div[@class="d-inline-block mb-1"]/h3/a/@href'):
            meta.append(each)

        pagination = html_root.xpath('//div[@class="paginate-container"]')
        previous = pagination.xpath('.//a[text()="Previous"]/@href').get()
        next = pagination.xpath('.//a[text()="Next"]/@href').get()

        if next is not None:
            print(next)
            self.request(next, self.get_star, meta)
        else:
            for each_repo in meta:
                if each_repo not in self.repo_filter:
                    self.request('https://github.com{repo}'.format(repo=each_repo), self.get_repo, meta = {'repo': each_repo})
                    self.repo_filter.add(each_repo)

    def get_repo(self, url, meta):
        self.request(url + '/labels', self.get_label, meta = meta)

    def get_label(self, url, meta):
        html_root = self.request_page(url)
        labels = html_root.xpath('//a[@class="IssueLabel--big d-inline-block v-align-top lh-condensed js-label-link"]')
        meta['labels'] = labels
        self.save_item(meta)

if __name__ == "__main__":
    urls = ['https://github.com/jstzwj']
    label_crawler = Crawler(path='items.txt')
    label_crawler.main()
