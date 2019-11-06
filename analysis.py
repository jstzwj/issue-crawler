import json
import time
import user_info

if __name__ == "__main__":

    activities = []
    users = user_info.User()
    # dump issues
    with open('items_grpc.txt', mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            issue = json.loads(each_line)
            for each_timeline in issue['timeline']:
                if each_timeline['item_type'] not in ['referenced_this',]:
                    users.save_user(each_timeline['author'])

        # dump issue activities
        for each_line in lines:
            issue = json.loads(each_line)
            for each_timeline in issue['timeline']:
                if each_timeline['item_type'] not in ['referenced_this',]:
                    activities.append((each_timeline['author'], each_timeline['time'], each_timeline['item_type']))


    # dump commits
    with open('commits_grpc.txt', mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all commits
        for each_line in lines:
            commit = json.loads(each_line)
            user_name = 'UNKNOWN'
            u = users.get_user_by_name(commit['author'])
            if u is not None:
                user_name = u['user_name']

            activity_time = time.strptime(int(commit['authored_date']), '%Y-%m-%dT%H:%M:%SZ')

            activities.append((user_name, activity_time, 'commit'))


