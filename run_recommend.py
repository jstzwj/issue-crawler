
import datetime
import numpy
import tqdm
import random
from matplotlib import pyplot as plt 
from project import Project
import recommend
import model_icf_tittle_simil
import model_ucf
import model_ucf_star_simil
import model_random

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
    precision_sum = 0.0
    recall_sum = 0.0
    for each_user, data_list in test_users.items():
        recommend_result = model.recommend(each_user, k)
        counter[each_user] = 0
        for user_id, item_id, rate in data_list:
            if item_id in recommend_result:
                counter[user_id] += 1
        precision_sum += counter[each_user] / k
        recall_sum += counter[each_user] / len(data_list)
    precision = precision_sum / len(test_users)
    recall = recall_sum / len(test_users)

    correct_user_count = 0
    for each_user, correct_count in counter.items():
        if correct_count != 0:
            correct_user_count += 1

    print(f'accuracy: {correct_user_count}/{len(test_users)}, {correct_user_count/len(test_users)}')
    print(f'precision: {precision}')
    print(f'recall: {recall}')
    return correct_user_count/len(test_users), recall, precision


def run_evaluation():
    project = Project()
    project.load('./data/gumtree', '/GumTreeDiff/gumtree')
    # project.load('./data/deno', '/denoland/deno')
    # project.load('./data/FreeRDP', '/FreeRDP/FreeRDP')
    # project.load('./data/jd-gui', '/java-decompiler/jd-gui')
    print(f'user number: {len(project.get_users())}')
    print(f'issue number: {len(project.get_issues())}')
    dataset = extract_recommend_dataset(project)

    # filter for new comer
    '''
    filter_counter = {}
    for each_data in dataset:
        if each_data[0] not in filter_counter.keys():
            filter_counter[each_data[0]] = []
        filter_counter[each_data[0]].append(each_data)
    
    filtered_dataset = []
    for each_user, data_list in filter_counter.items():
        if len(data_list) > 2:
            for each_data in data_list:
                filtered_dataset.append(each_data)

    dataset = filtered_dataset
    '''

    # model = RandomRecommendModel(project)
    # model = model_star_based.StarBasedRecommendModel(project)
    # model = model_issue_similarity_based.IssueSimilarityBasedRecommendModel(project)
    model = model_ucf.UCFRecommendModel(project)
    
    x_list = [3, 5, 10, 20, 40]
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
    plt.xlabel("recommend top k issues")
    plt.ylabel("accuracy or recall or precision")
    plt.plot(x_list,acc_plot,"b", label='accuracy')
    plt.plot(x_list,recall_plot,"r", label='recall')
    plt.plot(x_list,prec_plot,"y", label='precision')
    plt.legend(loc='upper left')
    plt.show()


def run_all_method_evaluation():
    project = Project()
    # project.load('./data/gumtree', '/GumTreeDiff/gumtree')
    project.load('./data/deno', '/denoland/deno')
    print(f'user number: {len(project.get_users())}')
    print(f'issue number: {len(project.get_issues())}')
    dataset = extract_recommend_dataset(project)

    models = []
    models.append(model_random.RandomRecommendModel(project))
    models.append(model_ucf_star_simil.UCFStarSimilRecommendModel(project))
    models.append(model_icf_tittle_simil.ICFTittleSimilRecommendModel(project))
    models.append(model_ucf.UCFRecommendModel(project))
    
    x_list = [3, 5, 10, 20, 40]
    
    plt.title("Issue recommend")
    plt.xlabel("recommend top k issues")
    plt.ylabel("accuracy")

    for each_model in models:
        acc_plot = []
        for each_k in x_list:
            accuracy_mean = []
            for ex_count in range(10):
                # split data
                train_data, test_data = dataset_split(dataset)
                # train
                each_model.train(train_data)
                # valid
                accuracy, recall, precision = valid(each_model, test_data, each_k)
                accuracy_mean.append(accuracy)

            acc_plot.append(numpy.mean(accuracy_mean))
            print(f'mean: acc:{numpy.mean(accuracy_mean)}')
        plt.plot(x_list,acc_plot, label=each_model.get_name())
    plt.legend(loc='upper left')
    plt.show()


if __name__ == "__main__":
    # run_evaluation()
    run_all_method_evaluation()
    

