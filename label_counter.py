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

def first(item):
    if item is not None and len(item) > 0:
        return item[0]
    else:
        return None

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
        self.debug = False

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
                    if self.debug:
                        req.crawl()
                    else:
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
        self.request(url + '?tab=stars', self.get_star, [])
        self.request(url + '?tab=following', self.get_following, [])

    def get_following(self, url, meta):
        html_root = self.request_page(url)
        for each in html_root.xpath('//span[@class="link-gray pl-1"]/text()'):
            meta.append(each)
            self.request(f'https://github.com/{each}', self.get_user)

        pagination = first(html_root.xpath('//div[@class="paginate-container"]'))
        if pagination is None:
            for each in meta:
                if each not in self.user_filter:
                    self.request(f'https://github.com/{each}', self.get_user)
                    self.user_filter.add(each)
            return
        previous = first(pagination.xpath('.//a[text()="Previous"]/@href'))
        next = first(pagination.xpath('.//a[text()="Next"]/@href'))

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

        pagination = first(html_root.xpath('//div[@class="paginate-container"]'))
        if pagination is None:
            for each_repo in meta:
                if each_repo not in self.repo_filter:
                    self.request('https://github.com{repo}'.format(repo=each_repo), self.get_repo, meta = {'repo': each_repo})
                    self.repo_filter.add(each_repo)
            return
        previous = first(pagination.xpath('.//a[text()="Previous"]/@href'))
        next = first(pagination.xpath('.//a[text()="Next"]/@href'))

        if next is not None:
            print(next)
            self.request(next, self.get_star, meta)
        else:
            for each_repo in meta:
                if each_repo not in self.repo_filter:
                    self.request('https://github.com{repo}'.format(repo=each_repo), self.get_repo, meta = {'repo': each_repo})
                    self.repo_filter.add(each_repo)

    def get_repo(self, url, meta):
        print('get repo:' + meta['repo'])
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
