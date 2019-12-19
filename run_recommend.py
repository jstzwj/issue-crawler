
import datetime
import numpy
import tqdm
import random
from matplotlib import pyplot as plt 
from project import Project
import recommend
import model_star_based

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

    # reorder activities by time
    for i, each_issue in enumerate(issues):
        if len(each_issue) <= 0:
            continue
        
        counter = {}
        for each_timeline in each_issue['timeline'][1:]:
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
                ret.append((users_meta[1][each_user], i, each_count/len(each_issue['timeline'][1:])))

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

def valid(model, test_data, k):
    # test data acceleration structure
    test_users = {}
    test_issues = {}
    for each_data in test_data:
        # add to test users
        if each_data[0] not in test_users.keys():
            test_users[each_data[0]] = []
        test_users[each_data[0]].append(each_data)

        # add to test issues
        if each_data[1] not in test_issues.keys():
            test_issues[each_data[1]] = []
        test_issues[each_data[1]].append(each_data)

    # valid
    counter = {}
    precision = 0.0
    recall = 0.0
    for each_user, data_list in test_users.items():
        recommend_result = model.recommend(each_user, k)
        counter[each_user] = 0
        for user_id, item_id, rate in data_list:
            if item_id in recommend_result:
                counter[user_id] += 1
        precision += counter[each_user] / k
        recall += counter[each_user] / len(data_list)
    precision = precision / len(test_users)
    recall = recall / len(test_users)

    correct_user_count = 0
    for each_user, correct_count in counter.items():
        if correct_count != 0:
            correct_user_count += 1

    print(f'accuracy: {correct_user_count}/{len(test_users)}, {correct_user_count/len(test_users)}')
    print(f'precision: {precision}')
    print(f'recall: {recall}')
    return correct_user_count/len(test_users), recall, precision
    
if __name__ == "__main__":
    project = Project()
    # project.load('./data/gumtree', '/GumTreeDiff/gumtree')
    # project.load('./data/deno', '/denoland/deno')
    project.load('./data/FreeRDP', '/FreeRDP/FreeRDP')
    dataset = extract_recommend_dataset(project)
    
    # model = RandomRecommendModel(project)
    model = model_star_based.StarBasedRecommendModel(project)

    x_list = [3, 5, 10, 20]
    acc_plot = []
    prec_plot = []
    recall_plot = []

    for each_k in x_list:
        accuracy_mean = []
        precision_mean = []
        recall_mean = []
        for ex_count in range(10):
            # split data
            train_data, test_data = dataset_split(dataset)
            # train
            model.train(train_data)
            # valid
            accuracy, recall, precision = valid(model, test_data, each_k)
            accuracy_mean.append(accuracy)
            precision_mean.append(precision)
            recall_mean.append(recall)

        acc_plot.append(numpy.mean(accuracy_mean))
        recall_plot.append(numpy.mean(recall_mean))
        prec_plot.append(numpy.mean(precision_mean))
        print(f'mean: acc:{numpy.mean(accuracy_mean)} recall:{numpy.mean(recall_mean)} prec:{numpy.mean(precision_mean)}')
    
    plt.title("Issue recommend") 
    plt.xlabel("x axis caption")
    plt.ylabel("y axis caption")
    plt.plot(x_list,acc_plot,"b", label='accuracy')
    plt.plot(x_list,recall_plot,"r", label='recall')
    plt.plot(x_list,prec_plot,"y", label='precision')
    plt.legend(loc='upper left')
    plt.show()
    

