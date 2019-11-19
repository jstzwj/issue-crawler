import git
import os
import json
import re

class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print('update(%s, %s, %s, %s)'%(op_code, cur_count, max_count, message))

def get_commits(url, repo_path, save_path, branch='master'):
    with open(save_path, mode='w', encoding='utf-8') as f:
        repo = None

        url_groups = re.match(r"https://github.com/([0-9a-zA-Z_\-]+)/([0-9a-zA-Z_\-]+)\.git", url)
        if url_groups is None:
            print('Error: invalid url')
            return
        
        temp_dir = os.path.join(repo_path, f'{url_groups.group(1)}_{url_groups.group(2)}')
        if not os.path.exists(temp_dir):
            repo = git.Repo.clone_from(url, temp_dir, progress=Progress())
        else:
            repo = git.Repo(temp_dir)
        cms = repo.iter_commits(rev=None)

        commit_item = {}
        for each_commit in cms:
            # print(each_commit.committer)
            commit_item['author'] = each_commit.author.name
            commit_item['authored_date'] = each_commit.authored_date
            commit_item['hexsha'] = each_commit.hexsha
            f.write(json.dumps(commit_item) + '\n')

if __name__ == "__main__":
    # url = 'https://github.com/grpc/grpc.git'
    # path = os.path.join('repos', 'grpc')
    '''
    url = 'https://github.com/denoland/deno.git'
    path = os.path.join('repos', 'deno')
    get_commits(url, path, 'commits_deno.txt')
    '''

    url = 'https://github.com/GumTreeDiff/gumtree.git'
    get_commits(url, './repos', 'commits_gumtree.txt')