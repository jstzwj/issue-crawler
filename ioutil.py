
import json

def read_issues(file_path):
    issues = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            issue = json.loads(each_line)
            issues.append(issue)

    return issues

def read_users(file_path):
    users = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            user = json.loads(each_line)
            users.append(user)

    return users

def read_commits(file_path):
    commits = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            commit = json.loads(each_line)
            commits.append(commit)

    return commits