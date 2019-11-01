import requests
import time
from lxml import etree


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
    def __init__(self):
        super().__init__()
        self.requests_list = []

    def request_page(self, url):
        html_text = requests.get(url).text
        html = etree.HTML(html_text)
        return html

    def get_issue(self, url, meta):
        html = self.request_page(url)

        issue_item = object()
        issue_item.type = 'issue'

        issue_panel = html.xpath('//div[@class="repository-content "]//div[@id="show_issue"]')
        if len(issue_panel) > 0:
            issue_panel = issue_panel[0]

        
        

    def get_issue_page(self, url, meta):
        html = self.request_page(url)

        # get issues
        issue_panel = html.xpath('//div[@aria-label="Issues"]/div/div')
        for each_issue in issue_panel:
            issue_url = each_issue.xpath('.//a[@data-hovercard-type="issue"]/@href')
            if len(issue_url) > 0:
                issue_url = issue_url[0]
            self.requests_list.append(Request(f'https://github.com{issue_url}', self.get_issue))
            


    def get_repo_issue(self, repo):
        self.requests_list.append(Request(f'https://github.com{repo}/issues', self.get_issue_page))
        try:
            while True:
                if len(self.requests_list) > 0 :
                    req = self.requests_list.pop()
                    req.crawl()
                else:
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        
        print('crawl finish')

if __name__ == "__main__":
    crawler = Crawler()
    crawler.get_repo_issue('/grpc/grpc')