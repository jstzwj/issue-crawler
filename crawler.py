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

        issue_item = {}
        issue_item['type'] = 'issue'
        
        # get panel
        issue_panel = html.xpath('//div[@class="repository-content "]//div[@id="show_issue"]')
        if len(issue_panel) > 0:
            issue_panel = issue_panel[0]
        else:
            raise Exception('issue panel no found')

        # get issue discussion header

        issue_header = issue_panel.xpath('.//div[@id="partial-discussion-header"]')
        if len(issue_header) > 0:
            issue_header = issue_header[0]
        else:
            raise Exception('issue header no found')

        
        # title
        issue_title = issue_header.xpath('.//span[@class="js-issue-title"]/text()')
        if len(issue_title) > 0:
            issue_item['title'] = issue_title[0]

        # id
        issue_id = issue_header.xpath('.//span[@class="gh-header-number"]//text()')
        if len(issue_id) > 0:
            if issue_id[0].startswith('#'):
                issue_item['id'] = int(issue_id[1:])

        # status
        issue_status = issue_header.xpath('.//span[contains(@title, "Status: ")]/@title')
        if len(issue_status) > 0:
            issue_status = issue_status[0]
            if issue_status.startswith('Status: ') and len(issue_status) > 8:
                issue_item['status'] = issue_status[8:]
            else:
                issue_item['status'] = issue_status


        # discussion bucket
        issue_discussion_bucket = issue_panel.xpath('.//div[@id="discussion_bucket"]')
        if len(issue_discussion_bucket) > 0:
            issue_discussion_bucket = issue_discussion_bucket[0]
        else:
            raise Exception('issue discussion bucket not found')

        issue_discussion_left = issue_discussion_bucket.xpath('.//div[0]')
        issue_discussion_right = issue_discussion_bucket.xpath('.//div[1]')

        if len(issue_discussion_left) > 0 and len(issue_discussion_right) > 0:
            issue_discussion_left = issue_discussion_left[0]
            issue_discussion_right = issue_discussion_right[0]
        else:
            raise Exception('issue left or right component no found')
        
        # first timeline item
        issue_comment_item = issue_discussion_left.xpath('.//div[contains(@class, "timeline-comment-group")]')
        if len(issue_comment_item) > 0:
            issue_comment_item = issue_comment_item[0]

            # header
            comment_header = issue_comment_item.xpath('.//div[contains(@class,"timeline-comment-header")]')
            if len(comment_header) > 0:
                comment_header = comment_header[0]
            # comment body
            comment_body = issue_comment_item.xpath('.//td[contains(@class,"comment-body")]')
            if len(comment_body) > 0:
                comment_body = comment_body[0]
                


        # timeline item parse
        issue_timeline_item = issue_discussion_left.xpath('.//div[contains(@class,"js-timeline-item")]')

        for each_timeline_item in issue_timeline_item:
            pass

        


        
        
        

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