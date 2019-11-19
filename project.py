import os
import re
import ioutil

def parse_repo_name(repo):
    repo_name = ''
    repo_owner = ''
    repo_idf = repo.split('/')
    if len(repo_idf) == 2:
        repo_owner = repo_idf[0]
        repo_name = repo_idf[1]
    elif len(repo_idf) == 3:
        repo_owner = repo_idf[1]
        repo_name = repo_idf[2]
    else:
        print('invalid repo name')
        return None, None

    return repo_owner, repo_name

def parse_repo_url(url):
    url_groups = re.match(r"https://github.com/([0-9a-zA-Z_\-]+)/([0-9a-zA-Z_\-]+)\.git", url)
    if url_groups is None:
        print('Error: invalid url')
        return None, None

    return url_groups.group(1), url_groups.group(2)

def get_issue_labels(issue):
    labels = set()

    if len(issue['timeline']) <= 0:
        return list(labels)

    # issue timeline
    for each_timeline in issue['timeline']:
        if each_timeline == {}:
            continue
        if 'author' not in each_timeline.keys():
            continue

        if each_timeline['item_type'] == 'add_and_remove_label':
            pass
        elif each_timeline['item_type'] == 'add_label':
            for each_label in each_timeline['labels']:
                labels.add(each_label)
        elif each_timeline['item_type'] == 'remove_label':
            for each_label in each_timeline['labels']:
                if each_label in labels:
                    labels.remove(each_label)

    return list(labels)

class Project(object):
    def __init__(self):
        self.commits = []
        self.issues = []
        self.users = []

    '''
    /org_name/repo_name
    '''
    def load(self, path, repo):
        if not os.path.exists(path):
            print('project load: path no found')
            return

        repo_owner, repo_name = parse_repo_name(repo)

        issue_file = os.path.join(path, f'{repo_owner}_{repo_name}_issue.txt')
        commit_file = os.path.join(path, f'{repo_owner}_{repo_name}_commit.txt')
        user_file = os.path.join(path, f'{repo_owner}_{repo_name}_user.txt')

        self.commits = ioutil.read_commits(commit_file)
        self.issues = ioutil.read_issues(issue_file)
        self.users = ioutil.read_users(user_file)

    def save(self, path, repo):
        if not os.path.exists(path):
            os.mkdir(path)

        repo_owner, repo_name = parse_repo_name(repo)

        issue_file = os.path.join(path, f'{repo_owner}_{repo_name}_issue.txt')
        commit_file = os.path.join(path, f'{repo_owner}_{repo_name}_commit.txt')
        user_file = os.path.join(path, f'{repo_owner}_{repo_name}_user.txt')

        ioutil.write_table(commit_file, self.commits)
        ioutil.write_table(issue_file, self.issues)
        ioutil.write_table(user_file, self.users)


    def get_issues(self):
        return self.issues

    def get_commits(self):
        return self.commits

    def get_users(self):
        return self.users
