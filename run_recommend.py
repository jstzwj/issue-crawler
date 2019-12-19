
import datetime
import numpy
import tqdm
import random
from matplotlib import pyplot as plt 
from project import Project
import recommend
import model_star_based

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
            if 'time' not in each_timeline.keys():
                continue
            
            if end_time is not None and datetime.datetime.strptime(each_timeline['time'], '%Y-%m-%dT%H:%M:%S') > end_time:
                continue

            if 'author' not in each_timeline.keys():
                continue
            
            if each_timeline['author'] in counter.keys():
                counter[each_timeline['author']] += 1
            else:
                counter[each_timeline['author']] = 1
        for each_user, each_count in counter.items():
            if each_user is not None:
                rate_matrix[users_meta[1][each_user], i] = each_count/len(each_issue['timeline'])

    # print(rate_matrix)

    return rate_matrix, users_meta, issues_meta

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


def rec_issues(project, end_time):
    
    users = project.get_users()
    issues = project.get_issues()

    print(f'users number: {len(users)}')
    print(f'issues number: {len(issues)}')

    user_item_matrix, users_meta, issues_meta = get_user_item_matrix(project, end_time)

    user_item_matrix_origin, users_meta_origin, issues_meta_origin = get_user_item_matrix(project, None)

    # filter and score
    '''
    What we need to do here is filtering valid items and users. If an issue had not been shown before, it shall not be used for simulated recommend.
    '''
    valid_user = []
    valid_issue = []
    issue_state_before = []
    issue_state_after = []

    for each_issue_index in range(len(issues)):
        issue_state_before.append(get_issue_state(issues[each_issue_index], end_time))
        issue_state_after.append(get_issue_state(issues[each_issue_index], None))
    
    for each_issue_index in range(len(issues)):
        if issue_state_before[each_issue_index] == 'open':
            # and issue_state_after[each_issue_index] == 'close' ?
            valid_issue.append(each_issue_index)

    for each_user_index in range(len(users)):
        for each_issue_index in valid_issue:
            if user_item_matrix_origin[each_user_index, each_issue_index] > 0 and \
                issue_state_before[each_user_index] == 'open':
                # user_item_matrix[each_user_index, each_issue_index] <= 0 and \
                # len(issues) - numpy.sum(user_item_matrix[each_user_index, :] == 0) > 3:
                valid_user.append(each_user_index)
                break

    print(f'valid users number: {len(valid_user)}')
    print(f'valid issues number: {len(valid_issue)}')

    # part of matrix and score
    def predict(top_k):
        correct_counter = 0
        
        for each_user_index in valid_user:
            record = []
            for each_issue_index in valid_issue:
                record.append(
                    (each_issue_index,
                    random.random()
                    )
                )

            record.sort(key= lambda x: x[1], reverse= True)
            # print(record[:top_k])
            for each_item_index in record[:top_k]:
                # print(record[:top_k])
                if user_item_matrix_origin[each_user_index, each_item_index[0]] > 0:
                    correct_counter += 1
                    # print(users[each_user_index])
                    break
            
        print(correct_counter/len(valid_user))
        print(f'{correct_counter}/{len(valid_user)}')
        return correct_counter

    # for each_top_k in range(0, 40):
    return predict(3)/len(valid_user), predict(5)/len(valid_user), predict(10)/len(valid_user)

def extract_recommend_dataset(project, end_time=None):
    ret = []
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
            if 'time' not in each_timeline.keys():
                continue
            
            if end_time is not None and datetime.datetime.strptime(each_timeline['time'], '%Y-%m-%dT%H:%M:%S') > end_time:
                continue

            if 'author' not in each_timeline.keys():
                continue
            
            if each_timeline['author'] in counter.keys():
                counter[each_timeline['author']] += 1
            else:
                counter[each_timeline['author']] = 1
        for each_user, each_count in counter.items():
            if each_user is not None:
                ret.append((users_meta[1][each_user], i, each_count/len(each_issue['timeline'])))

    return ret

def dataset_split(dataset):
    length = len(dataset)
    split_pos = int(length*0.6)
    random.shuffle(dataset)
    return dataset[:split_pos], dataset[split_pos:]

class RandomRecommendModel(recommend.RecommendModel):
    def __init__(self, project):
        self.issues = project.get_issues()
        self.users = project.get_users()
    def train(self, train_data):
        self.train_data = train_data
    def recommend(self, user_id, k):
        candidate_issues = list(range(len(self.issues)))
        for each_data in self.train_data:
            if each_data[0] == user_id:
                candidate_issues.remove(each_data[1])

        random.shuffle(candidate_issues)
        return candidate_issues[:k]

if __name__ == "__main__":
    project = Project()
    # project.load('./data/gumtree', '/GumTreeDiff/gumtree')
    # project.load('./data/deno', '/denoland/deno')
    project.load('./data/FreeRDP', '/FreeRDP/FreeRDP')
    
    dataset = extract_recommend_dataset(project)
    train_data, test_data = dataset_split(dataset)
    # model = RandomRecommendModel(project)
    model = model_star_based.StarBasedRecommendModel(project)
    model.train(train_data)

    # test data acceleration structure
    users = {}
    for each_data in test_data:
        if each_data[0] in users.keys():
            users[each_data[0]].append(each_data)
        else:
            users[each_data[0]] = []

    # valid
    counter = 0
    for each_user, data_list in users.items():
        recommend_result = model.recommend(each_user, 10)
        for user_id, item_id, rate in data_list:
            if item_id in recommend_result:
                counter+=1
                break

    print(f'precision: {counter}/{len(users)}, {counter/len(users)}')


