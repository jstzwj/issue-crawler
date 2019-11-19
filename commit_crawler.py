import git
import os
import json

class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print('update(%s, %s, %s, %s)'%(op_code, cur_count, max_count, message))

def get_commits(url, path, save_path, branch='master'):
    with open(save_path, mode='w', encoding='utf-8') as f:
        repo = None
        if not os.path.exists(path):
            repo = git.Repo.clone_from(url, path, progress=Progress())
        else:
            repo = git.Repo(path)
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
    path = os.path.join('repos', 'gumtree')
    get_commits(url, path, 'commits_gumtree.txt')