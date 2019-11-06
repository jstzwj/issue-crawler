import git
import os
import json

url = 'https://github.com/grpc/grpc.git'
path = os.path.join('repos', 'grpc')
with open('commits_grpc.txt', mode='w', encoding='utf-8') as f:
    repo = None
    if not os.path.exists(path):
        repo = git.Repo.clone_from(url, path, branch='master')
    else:
        repo = git.Repo(path)
    cms = repo.iter_commits('master')

    commit_item = {}
    for each_commit in cms:
        # print(each_commit.committer)
        commit_item['author'] = each_commit.author.name
        commit_item['authored_date'] = each_commit.authored_date
        commit_item['hexsha'] = each_commit.hexsha
        f.write(json.dumps(commit_item) + '\n')
