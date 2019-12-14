import requests
import json
import os
import re
import time
from lxml import etree


proxies = {'http' : 'http://localhost:10805', 'https': 'https://localhost:10805'}

def first(elements_list):
    if elements_list is None:
        return None
    if len(elements_list) == 0:
        return None

    return elements_list[0]

def strip_not_none(s):
    if s is not None:
        return s.strip()
    else:
        return None


def parse_profile(tree):
    ret = {}

    # left profile
    person_item = first(tree.xpath('//div[@itemtype="http://schema.org/Person"]'))
    if person_item is not None:
        names_card = first(person_item.xpath('.//h1[@class="vcard-names"]'))
        if names_card is not None:
            ret['full_name'] = first(names_card.xpath('.//span[@itemprop="name"]/text()'))
            ret['user_name'] = first(names_card.xpath('.//span[@itemprop="additionalName"]/text()'))

        ret['bio'] = first(person_item.xpath('.//div[@class="p-note user-profile-bio js-user-profile-bio"]/div/text()'))
        ret['company'] = first(person_item.xpath('.//li[@itemprop="worksFor"]/span[@class="p-org"]/div/text()'))
        ret['location'] = first(person_item.xpath('.//li[@itemprop="homeLocation"]/span[@class="p-label"]/text()'))
        ret['website'] = first(person_item.xpath('.//li[@itemprop="url"]/a/@href'))

        org_panel = first(person_item.xpath('.//div[@class="border-top py-3 clearfix hide-sm hide-md"]'))
        if org_panel is not None:
            org_list = org_panel.xpath('.//a[@data-hovercard-type="organization"]/@aria-label')
            ret['organizations'] = org_list

    # profile nav
    user_profile_nav = first(tree.xpath('//nav[@aria-label="User profile"]'))
    if user_profile_nav is not None:
        ret['repositories_num'] = strip_not_none(first(user_profile_nav.xpath('.//a[2]/span/text()')))
        ret['projects_num'] = strip_not_none(first(user_profile_nav.xpath('.//a[3]/span/text()')))
        ret['stars_num'] = strip_not_none(first(user_profile_nav.xpath('.//a[4]/span/text()')))
        ret['followers_num'] = strip_not_none(first(user_profile_nav.xpath('.//a[5]/span/text()')))
        ret['following_num'] = strip_not_none(first(user_profile_nav.xpath('.//a[6]/span/text()')))

    # repos
    js_pinned_item = first(tree.xpath('//div[@class="js-pinned-items-reorder-container"]'))
    if js_pinned_item is not None:
        ret['pinned'] = tree.xpath('.//ol/li/div/div/div/a[1]/@href')

    # contribution
    contributions_statistic = first(tree.xpath('//div[@class="js-yearly-contributions"]'))
    if contributions_statistic is not None:
        contribs = strip_not_none(first(contributions_statistic.xpath('.//div/h2/text()')))
        if contribs is not None:
            re_result = re.search('([0-9]+) contribution', contribs)
            ret['contribs'] = re_result.group(1)

        contrib_graph = first(contributions_statistic.xpath('.//div//svg[@class="js-calendar-graph-svg"]'))
        if contrib_graph is not None:
            ret['contrib_matrix'] = {}
            active_day_list = contrib_graph.xpath('.//rect[@data-count!="0"]')
            for each in active_day_list:
                contrib_date = first(each.xpath('.//@data-date'))
                contrib_count = first(each.xpath('.//@data-count'))
                if None not in [contrib_count, contrib_date]:
                    ret['contrib_matrix'][contrib_date] = {'count': contrib_count}

    # contribution year
    filter_list = first(tree.xpath('.//ul[@class="filter-list small"]'))
    if filter_list is not None:
        year_text = first(filter_list.xpath('.//li/a[@class="js-year-link filter-item px-3 mb-2 py-2 selected "]/text()'))
        ret['contrib_year'] = year_text

    return ret

def parse_repository(login):
    ret = {
        'repo': []
    }
    url = f'https://github.com/{login}?tab=repositories'
    
    while True:
        html_text = requests.get(url, proxies=proxies).text
        if html_text == 'Not Found':
            return {}
        tree = etree.HTML(html_text)

        for each in tree.xpath('//a[@itemprop="name codeRepository"]/text()'):
            ret['repo'].append(each.strip())

        pagination = tree.xpath('//div[@class="paginate-container"]')[0]
        previous = pagination.xpath('.//a[text()="Previous"]/@href')
        next = pagination.xpath('.//a[text()="Next"]/@href')

        if len(next) != 0:
            url = next[0]
        else:
            break

    return ret


def parse_star(login):
    ret = {
        'star': []
    }
    url = f'https://github.com/{login}?tab=stars'
    
    while True:
        html_text = requests.get(url, proxies=proxies).text
        if html_text == 'Not Found':
            return {}
        tree = etree.HTML(html_text)

        for each in tree.xpath('//div[@class="d-inline-block mb-1"]/h3/a/@href'):
            ret['star'].append(each)

        pagination = tree.xpath('//div[@class="paginate-container"]')[0]
        previous = pagination.xpath('.//a[text()="Previous"]/@href')
        next = pagination.xpath('.//a[text()="Next"]/@href')

        if len(next) != 0:
            url = next[0]
        else:
            break

    return ret

class UserCrawler(object):
    def __init__(self, path = 'user.txt'):
        self.path = path
        self.users = []

        self.load_from_file()

    def __del__(self):
        self.save_to_file()

    def load_from_file(self):
        self.users = []
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for each_line in lines:
                    self.users.append(json.loads(each_line))

    def save_to_file(self):
        try:
            with open(self.path + '.backup', 'w', encoding='utf-8') as f:
                for each_user in self.users:
                    f.write(json.dumps(each_user) + '\n')
        except Exception as e:
            print(f'save users fail :\n{str(e)}')
            return

        if os.path.exists(self.path):
            os.remove(self.path)
        os.rename(self.path + '.backup', self.path)

    def save_user(self, login):
        if login is None:
            return
        for each_user in self.users:
            if 'user_name' in each_user.keys() and each_user['user_name'] == login:
                return each_user
        user_url = 'https://github.com/' + login
        print(f'get user: {user_url}')
        user = None
        while True:
            try:
                # profile
                html_text = requests.get('https://github.com/' + login, proxies=proxies).text
                if html_text == 'Not Found':
                    return {}
                html_root = etree.HTML(html_text)
                user = parse_profile(html_root)

                # repository
                repos = parse_repository(user['user_name'])
                user.update(repos)

                # star
                stars = parse_star(user['user_name'])
                user.update(stars)

                # follower

                # following
                break
            except Exception as e:
                print(e)
                time.sleep(1)
            if len(self.users) % 10 == 0:
                self.save_to_file()
        self.users.append(user)
        return user

    def get_user_by_login(self, login):
        for each_user in self.users:
            if each_user['user_name'] == login:
                return each_user

        # no found
        return save_user(login)

    def get_user_by_name(self, name):
        for each_user in self.users:
            if each_user['full_name'] == name:
                return each_user