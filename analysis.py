import json
import time
import user_info
import pandas as pd
import numpy as np

if __name__ == "__main__":

    activities = pd.DataFrame(np.array([]),index=[],columns=['user_name','activity_type','time'])  
    users = user_info.User()
    # dump issues
    with open('items_grpc.txt', mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # fetch all user info
        for each_line in lines:
            issue = json.loads(each_line)
            for each_timeline in issue['timeline']:
                if each_timeline == {}:
                    continue
                if each_timeline['item_type'] not in ['referenced_this',]:
                    users.save_user(each_timeline['author'])

        # dump issue activities
        for each_line in lines:
            issue = json.loads(each_line)
            for each_timeline in issue['timeline']:
                if each_timeline['item_type'] not in ['referenced_this',]:
                    activities[activities.shape[0]] = [each_timeline['author'], each_timeline['time'], each_timeline['item_type']]


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

            t = time.localtime(int(commit['authored_date']))
            activity_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', t)

            activities[activities.shape[0]] = [user_name, activity_time, 'commit']

    activities.to_csv("activities.csv",index=False,sep=',')


