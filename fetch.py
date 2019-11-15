import os
import json

from issue_crawler import Crawler
from commit_crawler import get_commits
from user_crawler import UserCrawler


def read_issues(repo_name):
    issues = []
    with open(f'issue_{repo_name}.txt', mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            issue = json.loads(each_line)
            issues.append(issue)

    return issues

def fetch_repo(repo_name, repo_path, url, save_path):
    # fetch issue
    crawler = Crawler(os.path.join(save_path, f'{repo_name}_issue.txt'))
    crawler.get_repo_issue(repo_path)

    # get commits
    path = os.path.join('repos', repo_name)
    get_commits(url, path, os.path.join(save_path, f'{repo_name}_commit.txt'))

    # get user
    user_crawler = UserCrawler(os.path.join(save_path, f'{repo_name}_user.txt'))
    issues = read_issues(repo_name)
    for each_issue in issues:
        for each_timeline in each_issue['timeline']:
            if each_timeline == {}:
                continue
            if each_timeline['item_type'] not in ['referenced_this', 'referenced_to_pull']:
                user_crawler.save_user(each_timeline['author'])


if __name__ == "__main__":
    fetch_repo('deno', '/denoland/deno', 'https://github.com/denoland/deno.git', './')