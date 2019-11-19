import json
import csv
import os
import ioutil

def item_similarity():
    pass


def user_similarity():
    pass


def first_type_count(repo_name, path):

    users = {}
    issues = ioutil.read_issues(os.path.join(path, f'{repo_name}_issue.txt'))

    activities_list = []

    # reorder activities by time
    for each_issue in issues:
        if len(each_issue) <= 0:
            continue

        # create issue
        first_issue = each_issue['timeline'][0]
        item = {}
        item['user'] = first_issue['author']
        item['time'] = first_issue['time']
        item['type'] = 'create_issue'

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
        writer.writerow(["user_name", "type", "time"])
        for name, activity_type in users.items():
            writer.writerow([name, activity_type['type'], activity_type['time']])


first_type_count('gumtree', './data/gumtree')

