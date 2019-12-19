import datetime

class RecommendModel(object):
    def __init__(self):
        pass
    def train(self, train_data):
        pass
    def recommend(self, user_ids) -> list:
        pass



'''
get close or open state of an issue until sometime 
'''
def get_issue_state(issue, end_time):
    state = 'nofound'
    sorted_timeline = []
    for each_timeline in issue['timeline']:
        if each_timeline == {}:
            continue
        if 'time' not in each_timeline.keys():
            continue
        sorted_timeline.append(each_timeline)
    sorted_timeline.sort(key= lambda x: x['time'])
    for i, each_timeline in enumerate(sorted_timeline):
        if each_timeline == {}:
            continue
        if 'time' not in each_timeline.keys():
            continue
        
        if end_time is not None and datetime.datetime.strptime(each_timeline['time'], '%Y-%m-%dT%H:%M:%S') > end_time:
            continue

        if each_timeline['item_type'] == 'comment' and state == 'nofound':
            state = 'open'
        if each_timeline['item_type'] == 'close_this':
            state = 'close'
        elif each_timeline['item_type'] == 'reopen_this':
            state = 'open'

    return state