import json
import csv

def read_issues(repo_name):
    issues = []
    with open(f'issue_{repo_name}.txt', mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            issue = json.loads(each_line)
            issues.append(issue)

    return issues

def item_similarity():
    pass


def user_similarity():
    pass


def first_type_count(repo_name):

    users = {}
    issues = read_issues('deno')

    activities_list = []

    # reorder activities by time
    for each_issue in issues:
        if len(each_issue) <= 0:
            continue
        first_issue = each_issue['timeline'][0]
        item = {}
        item['user'] = first_issue['author']
        item['time'] = first_issue['time']
        item['type'] = 'create_issue'

        activities_list.append(item)
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
        if each_activity['user'] not in users:
            users[each_activity['user']] = each_activity['type']

    # write to csv
    with open(f"activities_{repo_name}.csv","w", newline='') as csvfile:
        writer = csv.writer(csvfile)

        #先写入columns_name
        writer.writerow(["user_name", "type"])
        for name, activity_type in users.items():
            writer.writerow([name, activity_type])


first_type_count('deno')

