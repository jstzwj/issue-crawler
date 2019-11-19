import json
import csv
import os
import ioutil
import project

def item_similarity():
    pass


def user_similarity():
    pass

def labels_to_string(labels):
    ret = ''
    for i, each_label in enumerate(labels):
        if i != 0:
            ret += ','
        ret += each_label

    return ret

def first_type_count(repo, path):

    repo_owner, repo_name = project.parse_repo_name(repo)

    users = {}

    prj = project.Project()
    prj.load(path, repo)

    
    issues = prj.get_issues()

    activities_list = []

    # reorder activities by time
    for each_issue in issues:
        if len(each_issue) <= 0:
            continue
        
        labels = project.get_issue_labels(each_issue)
        # create issue
        first_issue = each_issue['timeline'][0]
        item = {}
        item['user'] = first_issue['author']
        item['time'] = first_issue['time']
        item['type'] = 'create_issue'
        item['labels'] = labels

        activities_list.append(item)

        # issue timeline
        for each_timeline in each_issue['timeline'][1:]:
            if each_timeline == {}:
                continue
            if 'author' not in each_timeline.keys():
                continue
            item = {}
            item['user'] = each_timeline['author']
            item['time'] = each_timeline['time']
            item['type'] = each_timeline['item_type']
            item['labels'] = labels

            activities_list.append(item)

    # sort by time
    activities_list.sort(key=lambda x:x['time'])

    # find first
    for each_activity in activities_list:
        if each_activity['user'] not in users.keys():
            users[each_activity['user']] = each_activity

    # write to csv
    with open(f"activities_{repo_name}.csv","w", newline='') as csvfile:
        writer = csv.writer(csvfile)

        #先写入columns_name
        writer.writerow(["user_name", "type", "time", 'labels'])
        for name, activity_type in users.items():
            writer.writerow([name, activity_type['type'], activity_type['time'], labels_to_string(activity_type['labels'])])


# first_type_count('/glfw/glfw', './data/glfw')
first_type_count('/ray-project/ray', './data/ray')

