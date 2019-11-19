import os
import shutil
import json

from issue_crawler import Crawler
from commit_crawler import get_commits
from user_crawler import UserCrawler

import ioutil



def fetch_repo(repo_name, repo_path, url, save_path):
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    issue_file = os.path.join(save_path, f'{repo_name}_issue.txt')
    commit_file = os.path.join(save_path, f'{repo_name}_commit.txt')
    user_file = os.path.join(save_path, f'{repo_name}_user.txt')
    # fetch issue
    if not os.path.exists(issue_file):
        crawler = Crawler(issue_file)
        crawler.get_repo_issue(repo_path)

    # get commits
    if not os.path.exists(commit_file):
        get_commits(url, commit_file)

    # get user
    user_crawler = UserCrawler(user_file)
    issues = ioutil.read_issues(issue_file)
    for each_issue in issues:
        for each_timeline in each_issue['timeline']:
            if each_timeline == {}:
                continue
            if 'author' in each_timeline.keys():
                user_crawler.save_user(each_timeline['author'])

if __name__ == "__main__":
    # fetch_repo('deno', '/denoland/deno', 'https://github.com/denoland/deno.git', './')
    # fetch_repo('godot', '/godotengine/godot', 'https://github.com/godotengine/godot.git', './data/godot')
    # fetch_repo('gumtree', '/GumTreeDiff/gumtree', 'https://github.com/GumTreeDiff/gumtree.git', './data/gumtree')
    fetch_repo('glfw', '/glfw/glfw', 'https://github.com/glfw/glfw.git', './data/glfw')
    
    