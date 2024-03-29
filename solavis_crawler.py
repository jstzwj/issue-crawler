import asyncio
import solavis
from lxml import etree
from concurrent.futures import ThreadPoolExecutor
import time
import datetime
import json

import solavis

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

async def parse_html(html):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda :etree.HTML(html))
    return result

async def xpath(tree, path):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda :tree.xpath(path))
    return result

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
    labels = node.xpath('.//span[contains(@class, "IssueLabel")]/a/text()')
    return labels

def get_issue(node):
    issue_item = node.xpath('.//a[@data-hovercard-type="issue"]/@href')
    if len(issue_item) > 0:
        return issue_item[0]
    else:
        return None

def get_issues(node):
    issue_items = node.xpath('.//a[@data-hovercard-type="issue"]/@href')
    return issue_items

def get_pulls(node):
    issue_items = node.xpath('.//a[@data-hovercard-type="pull_request"]/@href')
    return issue_items

def get_pull(node):
    pull_item = node.xpath('.//a[@data-hovercard-type="pull_request"]/@href')
    if len(pull_item) > 0:
        return pull_item[0]
    else:
        return None

def get_datetime(node):
    dt = node.xpath('.//relative-time/@datetime')
    if len(dt) > 0:
        return datetime.datetime.strptime(dt[0], '%Y-%m-%dT%H:%M:%SZ')
    else:
        return None

class GithubSpider(solavis.Spider):
    start_urls = ['https://github.com/grpc/grpc/issues', 'https://github.com/grpc/grpc/issues?q=is%3Aissue+is%3Aclosed']
    def __init__(self):
        pass

    async def parse(self, response):
        html = response.text
        # print(response.status)
        html_root = await parse_html(html)

        # get issues
        issue_panel = html_root.xpath('//div[@aria-label="Issues"]/div/div')
        for each_issue in issue_panel:
            issue_url = each_issue.xpath('.//a[@data-hovercard-type="issue"]/@href')
            if len(issue_url) > 0:
                issue_url = issue_url[0]
            
            await self.request(f'https://github.com{issue_url}', self.get_issue)

        # next page
        next_page = html_root.xpath('.//a[@class="next_page"]/@href')
        if len(next_page) > 0:
            next_page = next_page[0]
            next_page = "https://github.com" + next_page

            await self.request(next_page, self.parse)

    async def get_issue(self, response):
        html = response.text
        html_root = await parse_html(html)

        issue_item = {}
        issue_item['type'] = 'issue'
        
        # get panel
        issue_panel = html_root.xpath('//div[@class="repository-content "]//div[@id="show_issue"]')
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
            comment_body = issue_comment_item.xpath('.//td[contains(@class,"comment-body")]')
            if len(comment_body) > 0:
                comment_body = comment_body[0]
            
            timeline_item['comment'] = etree.tostring(comment_body, encoding='utf-8').decode(encoding='utf-8')

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
                comment_body = issue_comment_item.xpath('.//td[contains(@class,"comment-body")]')
                if len(comment_body) > 0:
                    comment_body = comment_body[0]

                timeline_item['comment'] = etree.tostring(comment_body, encoding='utf-8').decode(encoding='utf-8')

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

                # self-assigned
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "self-assigned this")]/parent::div')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['author'] = author
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'assign_self'
                # assign and unassign task
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "and unassigned")]/parent::div')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['author'] = author
                    users = get_users(each_timeline_item)
                    timeline_item['assignee'] = users[0]
                    timeline_item['unassignee'] = users[1]
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'change_assignees'
                # assign task
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "assigned")]/parent::div')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['author'] = author
                    users = get_users(each_timeline_item)
                    timeline_item['assignee'] = users[0]
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'assign_user'
                # referenced this issue
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]//text()[contains(., "referenced this issue")]/ancestor::div[@class="TimelineItem-body"]')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['author'] = author
                    timeline_item['ref_pull'] = get_pull(each_timeline_item)
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'ref_issue'
                # changed the title
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "changed the title")]/parent::div')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['author'] = author
                    del_title = each_timeline_item.xpath('.//del/text()')
                    if len(del_title) > 0:
                        del_title = del_title[0]
                    timeline_item['del_title'] = del_title
                    ins_title = each_timeline_item.xpath('.//ins/text()')
                    if len(ins_title) > 0:
                        ins_title = ins_title[0]
                    timeline_item['ins_title'] = ins_title
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'change_title'

                # removed their assignment
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]/text()[contains(., "removed their assignment")]/parent::div')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['author'] = author
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'remove_assignment'
                # This was referenced
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]//text()[contains(., "This was referenced")]/ancestor::div[@class="TimelineItem-body"]')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['ref_pulls'] = get_pulls(each_timeline_item)
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'referenced_this'
                # close
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]//text()[contains(., "closed this")]/ancestor::div[@class="TimelineItem-body"]')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'close_this'
                # reopen
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]//text()[contains(., "reopened this")]/ancestor::div[@class="TimelineItem-body"]')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'reopen_this'
                # delete comment
                elif len(each_timeline_item.xpath('.//div[@class="TimelineItem-body"]//text()[contains(., "deleted a comment")]/ancestor::div[@class="TimelineItem-body"]')) > 0:
                    author = get_author(each_timeline_item)
                    timeline_item['time'] = get_datetime(each_timeline_item)
                    timeline_item['item_type'] = 'delete_comment'
                
                issue_item['timeline'].append(timeline_item)

        await self.save(issue_item)

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

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    github_spider = GithubSpider()
    json_pipeline = JsonPipeline()
    container = solavis.Container()

    container.set_delay(5)
    container.set_random_delay(True)
    container.add_spider(github_spider)
    container.add_pipeline(json_pipeline, 1)
    # container.add_middleware(DepthMiddleware(), 1)
    # container.set_request_loader(solavis.contrib.request.SqliteRequestLoader(''))
    
    container.run()