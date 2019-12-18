
import datetime
import numpy
import tqdm
from matplotlib import pyplot as plt 
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

    # print(rate_matrix)

    return rate_matrix, users_meta, issues_meta

def PearsonCorrelationSimilarity(vec1, vec2):
	# value = range(len(vec1))
	# sum_vec1 = sum([ vec1[i] for i in value])
	# sum_vec2 = sum([ vec2[i] for i in value])
    sum_vec1 = numpy.sum(vec1)
    sum_vec2 = numpy.sum(vec2)

	# square_sum_vec1 = sum([ pow(vec1[i],2) for i in  value])
	# square_sum_vec2 = sum([ pow(vec2[i],2) for i in  value])
    square_sum_vec1 = numpy.sum(numpy.power(vec1, 2))
    square_sum_vec2 = numpy.sum(numpy.power(vec2, 2))

	# product = sum([ vec1[i]*vec2[i] for i in value])
    product = vec1.dot(vec2)

    numerator = product - (sum_vec1 * sum_vec2 / len(vec1))
    dominator = ((square_sum_vec1 - pow(sum_vec1, 2) / len(vec1)) * (square_sum_vec2 - pow(sum_vec2, 2) / len(vec2))) ** 0.5

    if dominator == 0:
        return 0
    result = numerator / (dominator * 1.0)

    return result

def get_user_similarity(project, rate_matrix, left_index, user_left, right_index, user_right):
    star_map = {}
    for each_star in user_left['star']:
        if each_star not in star_map:
            star_map[each_star] = len(star_map)

    for each_star in user_right['star']:
        if each_star not in star_map:
            star_map[each_star] = len(star_map)

    left_vec = numpy.zeros((len(star_map) + 1))
    right_vec = numpy.zeros((len(star_map) + 1))
    
    for each_star in user_left['star']:
        left_vec[star_map[each_star]] = 1

    # 保证PearsonCorrelationSimilarity中dominator不为0
    left_vec[len(star_map)] = 1

    for each_star in user_right['star']:
        right_vec[star_map[each_star]] = 1

    # 保证PearsonCorrelationSimilarity中dominator不为0
    right_vec[len(star_map)] = 1

    return PearsonCorrelationSimilarity(left_vec, right_vec)


def get_issue_similarity(project, rate_matrix,user_left, user_right):
    pass

'''
get close or open state of an issue until sometime 
'''
def get_issue_state(issue, end_time):
    state = 'open'
    sorted_timeline = []
    for each_timeline in issue['timeline']:
        if each_timeline == {}:
            continue
        if 'time' not in each_timeline.keys():
            continue
        sorted_timeline.append(each_timeline)
    sorted(sorted_timeline, key= lambda x: x['time'])
    for each_timeline in sorted_timeline:
        if each_timeline == {}:
            continue
        if 'time' not in each_timeline.keys():
            continue
        
        if end_time is not None and datetime.datetime.strptime(each_timeline['time'], '%Y-%m-%dT%H:%M:%S') > end_time:
            continue

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
    with tqdm.tqdm(total=len(users)) as pbar:
        user_item_mean = numpy.mean(user_item_matrix, axis=1)
        user_item_mean_minus = user_item_matrix - numpy.repeat(user_item_mean[:, numpy.newaxis], user_item_matrix.shape[1], axis=1)

        for a in range(len(users)):
            avg_ru = numpy.mean(user_item_matrix[a, :])
            k = 1 / (numpy.sum(user_simil_matrix[a, :]) + 0.00001)
            
            prediction_matrix[a, :] = avg_ru
            for u in range(len(users)):
                prediction_matrix[a, :] += k * (user_simil_matrix[a, u] * user_item_mean_minus[a, :])

            pbar.update(1)

    # changes from origin
    change_matrix = (user_item_matrix_origin - user_item_matrix) > 0
    # print(change_matrix)


    # filter and score
    '''
    What we need to do here is valid items and users filtering. If an issue had not been shown before, it should not be used for simulated recommend.
    '''
    sorted_matrix = numpy.argsort(prediction_matrix, axis=1)
    valid_user = []
    valid_issue = []

    for each_issue_index in range(len(issues)):
        is_valid = False

        state = get_issue_state(issues[each_issue_index], end_time)
        if state == 'open':
            if get_issue_state(issues[each_issue_index], None) == 'close':
                is_valid = True
        else:
            is_valid = False
        
        if not is_valid:
            continue
        else:
            valid_issue.append(each_issue_index)

    for each_user_index in range(len(users)):
        for each_issue_index in valid_issue:
            if user_item_matrix_origin[each_user_index, each_issue_index] > 0 and \
                user_item_matrix[each_user_index, each_issue_index] <= 0:
                valid_user.append(each_user_index)
                break

    print(f'valid users number: {len(valid_user)}')
    print(f'valid issues number: {len(valid_issue)}')

    # part of matrix and score
    def predict(top_k):
        correct_counter = 0
        record = []
        for each_user_index in valid_user:
            for each_issue_index in valid_issue:
                record.append(
                    (each_issue_index,
                    prediction_matrix[each_user_index, each_issue_index]
                    )
                )

            sorted(record, key= lambda x: x[1], reverse= True)
            for each_item_index in record[:top_k]:
                if user_item_matrix_origin[each_user_index, each_item_index[0]] > 0:
                    correct_counter += 1
                    break
            
        print(correct_counter/len(valid_user))
        print(f'{correct_counter}/{len(valid_user)}')
        return correct_counter

    # for each_top_k in range(0, 40):
    return predict(3)/len(valid_user), predict(5)/len(valid_user), predict(10)/len(valid_user)

if __name__ == "__main__":
    project = Project()
    # project.load('./data/gumtree', '/GumTreeDiff/gumtree')
    # project.load('./data/deno', '/denoland/deno')
    project.load('./data/FreeRDP', '/FreeRDP/FreeRDP')
    
    time_list = [
        '2019-1-10T05:44:42Z',
        '2019-2-10T05:44:42Z',
        '2019-3-10T05:44:42Z',
        '2019-4-10T05:44:42Z',
        '2019-5-10T05:44:42Z',
        '2019-6-10T05:44:42Z',
        '2019-7-10T05:44:42Z',
        '2019-8-10T05:44:42Z',
        '2019-9-10T05:44:42Z',
        '2019-10-10T05:44:42Z',
        '2019-11-10T05:44:42Z',
    ]
    x_list = list(range(11))
    top_3_list = []
    top_5_list = []
    top_10_list = []
    for each_time in time_list:
        ret = rec_issues(project, datetime.datetime.strptime(each_time, '%Y-%m-%dT%H:%M:%SZ'))
        top_3_list.append(ret[0])
        top_5_list.append(ret[1])
        top_10_list.append(ret[2])

    plt.title("Matplotlib demo") 
    plt.xlabel("x axis caption")
    plt.ylabel("y axis caption")
    plt.plot(x_list,top_3_list,"b")
    plt.plot(x_list,top_5_list,"r") 
    plt.plot(x_list,top_10_list,"y")
    plt.show()
    

    