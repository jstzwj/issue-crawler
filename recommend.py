
import datetime
import numpy
from project import Project

def get_user_item_matrix(project, end_time):
    issues = project.get_issues()
    users = project.get_users()

    issues_meta = ({}, {})
    users_meta = ({}, {})

    for i, each_issue in enumerate(issues):
        issues_meta[0][i] = each_issue['id']
        issues_meta[1][each_issue['id']] = i

    for i, each_user in enumerate(users):
        users_meta[0][i] = each_user['user_name']
        users_meta[1][each_user['user_name']] = i

    rate_matrix = numpy.zeros((len(users), len(issues)))


    # reorder activities by time
    for i, each_issue in enumerate(issues):
        if len(each_issue) <= 0:
            continue
        
        counter = {}
        for each_timeline in each_issue['timeline']:
            if each_timeline == {}:
                continue
            if 'author' not in each_timeline.keys():
                continue
            
            if each_timeline['author'] in counter.keys():
                counter[each_timeline['author']] += 1
            else:
                counter[each_timeline['author']] = 0
        for each_user, each_count in counter.items():
            if each_user is not None:
                rate_matrix[users_meta[1][each_user], i] = each_count/len(each_issue['timeline'])

    print(rate_matrix)


def get_user_similarity(project, rate_matrix, user_left, user_right):
    pass


def get_issue_similarity(project, rate_matrix,user_left, user_right):
    pass


if __name__ == "__main__":
    project = Project()
    project.load('./data/deno', '/denoland/deno')

    user_item_matrix = get_user_item_matrix(project, datetime.datetime.strptime('2019-01-10T05:44:42Z', '%Y-%m-%dT%H:%M:%SZ'))