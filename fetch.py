import os
import shutil
import json

from issue_crawler import Crawler
from commit_crawler import get_commits
from user_crawler import UserCrawler

import ioutil
import project


def fetch_repo(url, save_path):
    repo_owner, repo_name = project.parse_repo_url(url)
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    issue_file = os.path.join(save_path, f'{repo_owner}_{repo_name}_issue.txt')
    commit_file = os.path.join(save_path, f'{repo_owner}_{repo_name}_commit.txt')
    user_file = os.path.join(save_path, f'{repo_owner}_{repo_name}_user.txt')
    # fetch issue
    if not os.path.exists(issue_file):
        crawler = Crawler(issue_file)
        crawler.get_repo_issue(f'/{repo_owner}/{repo_name}')

    # get commits
    if not os.path.exists(commit_file):
        get_commits(url, './repos', commit_file)

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
    pass
    fetch_repo('https://github.com/denoland/deno.git', './data/deno')
    # fetch_repo('godot', '/godotengine/godot', 'https://github.com/godotengine/godot.git', './data/godot')
    # fetch_repo('https://github.com/GumTreeDiff/gumtree.git', './data/gumtree')
    # fetch_repo('https://github.com/glfw/glfw.git', './data/glfw')
    # fetch_repo('https://github.com/ray-project/ray.git', './data/ray')
    # fetch_repo('https://github.com/yegord/snowman.git', './data/snowman')
    # fetch_repo('https://github.com/FreeRDP/FreeRDP.git', './data/FreeRDP')
    # fetch_repo('https://github.com/java-decompiler/jd-gui.git', './data/jd-gui')
    # fetch_repo('https://github.com/UKPLab/sentence-transformers.git', './data/sentence-transformers')
    