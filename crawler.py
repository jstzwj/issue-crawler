import requests
import time
import datetime
import json
from lxml import etree


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

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


def get_author(node):
    author = node.xpath('.//a[@data-hovercard-type="user"]/text()')
    if len(author) > 0:
        return author[0]
    else:
        return None

def get_authors(node):
    author = node.xpath('.//a[@data-hovercard-type="user"]/text()')
    return author

def get_users(node):
    users = node.xpath('.//a[@data-hovercard-type="user"]/span/text()')
    return users

def get_labels(node):
    labels = node.xpath('.//span[contains(@class, "IssueLabel")]/text()')
    return labels

def get_datetime(node):
    dt = node.xpath('.//a[@class="link-gray js-timestamp"]/relative-time/@datetime')
    if len(dt) > 0:
        return datetime.datetime.strptime(dt[0], '%Y-%m-%dT%H:%M:%SZ')
    else:
        return None

class Crawler(object):
    def __init__(self):
        super().__init__()
        self.requests_list = []
        self.save_path = "items.txt"
        self.file = open(self.save_path, 'w', encoding='utf-8')

    def __del__(self):
        self.file.close()

    def request_page(self, url):
        html_text = requests.get(url).text
        html = etree.HTML(html_text)
        return html

    def save_item(self, item):
        self.file.write(json.dumps(item, cls=DateTimeEncoder) + "\n")

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
            issue_item['title'] = issue_title[0].strip()

        # id
        issue_id = issue_header.xpath('.//span[@class="gh-header-number"]//text()')
        if len(issue_id) > 0:
            issue_id = issue_id[0]
            if issue_id.startswith('#'):
                issue_item['id'] = int(issue_id[1:])

        # status
        issue_status = issue_header.xpath('.//span[contains(@title, "Status: ")]/@title')
        if len(issue_status) > 0:
            issue_status = issue_status[0]
            if issue_status.startswith('Status: ') and len(issue_status) > 8:
                issue_item['status'] = issue_status[8:]
            else:
                issue_item['status'] = issue_status


        issue_item['timeline'] = []
        # discussion bucket
        issue_discussion_bucket = issue_panel.xpath('.//div[@id="discussion_bucket"]')
        if len(issue_discussion_bucket) > 0:
            issue_discussion_bucket = issue_discussion_bucket[0]
        else:
            raise Exception('issue discussion bucket not found')

        issue_discussion_left = issue_discussion_bucket.xpath('./div[1]')
        issue_discussion_right = issue_discussion_bucket.xpath('./div[2]')

        if len(issue_discussion_left) > 0 and len(issue_discussion_right) > 0:
            issue_discussion_left = issue_discussion_left[0]
            issue_discussion_right = issue_discussion_right[0]
        else:
            raise Exception('issue left or right component no found')
        
        # first timeline item
        issue_comment_item = issue_discussion_left.xpath('.//div[contains(@class, "js-discussion")]/div[contains(@class, "TimelineItem")]')
        if len(issue_comment_item) > 0:
            issue_comment_item = issue_comment_item[0]

            timeline_item = {}
            # header
            comment_header = issue_comment_item.xpath('.//div[contains(@class,"timeline-comment-header")]')
            if len(comment_header) > 0:
                comment_header = comment_header[0]
            
            # header author
            timeline_item['author'] = get_author(comment_header)

            # header time
            timeline_item['time'] = get_datetime(comment_header)
            
            # comment body
            comment_body = issue_comment_item.xpath('.//td[contains(@class,"comment-body")]/node()')
            if len(comment_body) > 0:
                comment_body = comment_body[0]

            timeline_item['comment'] = comment_body

            timeline_item['item_type'] = 'comment'
            issue_item['timeline'].append(timeline_item)
                


        # timeline item parse
        issue_timeline_item = issue_discussion_left.xpath('.//div[contains(@class,"js-timeline-item")]')

        for each_js_timeline_item in issue_timeline_item:
            comment_items = each_js_timeline_item.xpath('.//div[@class="TimelineItem js-comment-container"]')
            activities_items = each_js_timeline_item.xpath('.//div[@class="TimelineItem"]')

            for each_timeline_item in comment_items:
                timeline_item = {}
                # header
                comment_header = issue_comment_item.xpath('.//div[contains(@class,"timeline-comment-header")]')
                if len(comment_header) > 0:
                    comment_header = comment_header[0]
                
                # header author
                comment_author = comment_header.xpath('.//a[@data-hovercard-type="user"]/text()')
                if len(comment_author) > 0:
                    comment_author = comment_author[0]
                timeline_item['author'] = comment_author

                # header time
                comment_time = comment_header.xpath('.//a[@class="link-gray js-timestamp"]/relative-time/@datetime')
                if len(comment_time) > 0:
                    comment_time = comment_time[0]

                timeline_item['time'] = datetime.datetime.strptime(comment_time, '%Y-%m-%dT%H:%M:%SZ')
                
                # comment body
                comment_body = issue_comment_item.xpath('.//td[contains(@class,"comment-body")]/node()')
                if len(comment_body) > 0:
                    comment_body = comment_body[0]

                timeline_item['comment'] = comment_body

                timeline_item['item_type'] = 'comment'
                issue_item['timeline'].append(timeline_item)
            
            for each_timeline_item in activities_items:
                timeline_item = {}

                timelineitem_body = each_timeline_item.xpath('.//div[@class="TimelineItem-body"]')

                # add label
                if len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "added")]/parent::div')) > 0:
                    timeline_item['author'] = get_author(each_timeline_item)
                    timeline_item['labels'] = get_labels(each_timeline_item)
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'add_label'
                
                # assign task
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "assigned")]/parent::div')) > 0:
                    author = get_authors(each_timeline_item)
                    timeline_item['author'] = author
                    users = get_users(each_timeline_item)
                    timeline_item['assignee'] = users[0]
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'assign_user'
                # self-assigned
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "self-assigned this")]/parent::div')) > 0:
                    author = get_authors(each_timeline_item)
                    timeline_item['author'] = author
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'change_assignees'
                # assign and unassign task
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "and unassigned")]/parent::div')) > 0:
                    author = get_authors(each_timeline_item)
                    timeline_item['author'] = author
                    users = get_users(each_timeline_item)
                    timeline_item['assignee'] = users[0]
                    timeline_item['unassignee'] = users[1]
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'change_assignees'
                
                issue_item['timeline'].append(timeline_item)

        self.save_item(issue_item)
        

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