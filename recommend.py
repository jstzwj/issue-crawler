
import datetime
import numpy
import tqdm
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
            if 'time' not in each_timeline.keys():
                continue
            
            if end_time is not None and datetime.datetime.strptime(each_timeline['time'], '%Y-%m-%dT%H:%M:%S') > end_time:
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

    return rate_matrix, users_meta, issues_meta

def PearsonCorrelationSimilarity(vec1, vec2):
	value = range(len(vec1))
 
	sum_vec1 = sum([ vec1[i] for i in value])
	sum_vec2 = sum([ vec2[i] for i in value])
 
	square_sum_vec1 = sum([ pow(vec1[i],2) for i in  value])
	square_sum_vec2 = sum([ pow(vec2[i],2) for i in  value])
 
	product = sum([ vec1[i]*vec2[i] for i in value])
 
	numerator = product - (sum_vec1 * sum_vec2 / len(vec1))
	dominator = ((square_sum_vec1 - pow(sum_vec1, 2) / len(vec1)) * (square_sum_vec2 - pow(sum_vec2, 2) / len(vec2))) ** 0.5
 
	if dominator == 0:
		return 0
	result = numerator / (dominator * 1.0)
 
	return result

def get_user_similarity(project, rate_matrix, left_index, user_left, right_index, user_right):
    return PearsonCorrelationSimilarity(rate_matrix[left_index,:], rate_matrix[right_index,:])


def get_issue_similarity(project, rate_matrix,user_left, user_right):
    pass

if __name__ == "__main__":
    project = Project()
    project.load('./data/gumtree', '/GumTreeDiff/gumtree')

    users = project.get_users()
    issues = project.get_issues()

    user_item_matrix, users_meta, issues_meta = get_user_item_matrix(project, datetime.datetime.strptime('2019-01-10T05:44:42Z', '%Y-%m-%dT%H:%M:%SZ'))

    user_simil_matrix = numpy.zeros((len(users), len(users)))


    with tqdm.tqdm(total=len(users)*len(users)//2) as pbar:
        for i, each_user_i in enumerate(users):
            for j, each_user_j in enumerate(users):
                if j > i:
                    continue
                tmp = get_user_similarity(project, user_item_matrix, i, each_user_i, j, each_user_j)
                user_simil_matrix[i, j] = tmp
                user_simil_matrix[j, i] = tmp
                pbar.update(1)

    prediction_matrix = numpy.zeros((len(users), len(issues)))

    # top k
    k = 9
    for a in range(len(users)):
        avg_ru = numpy.mean(user_item_matrix[a, :])
        k = 1 / numpy.sum(user_simil_matrix[a, :])
        for i in range(len(issues)):
            prediction_matrix[a, i] = avg_ru + \
                numpy.sum(user_simil_matrix[a, :] @ (user_item_matrix[:,i] - numpy.mean(user_item_matrix, axis=1))) * k


    print(prediction_matrix[:])