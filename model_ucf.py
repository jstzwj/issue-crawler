
import numpy
import tqdm
import recommend

from scipy.spatial.distance import cosine

from sentence_transformers import SentenceTransformer


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

class UCFRecommendModel(recommend.RecommendModel):
    def __init__(self, project):
        self.project = project
        self.issues = project.get_issues()
        self.users = project.get_users()
        self.build_acceleration_structure()

    def build_acceleration_structure(self):
        self.issues2id = {}
        self.id2issues = {}
        self.users2id = {}
        self.id2users = {}

        for i, each_issue in enumerate(self.issues):
            self.id2issues[i] = each_issue['id']
            self.issues2id[each_issue['id']] = i

        for i, each_user in enumerate(self.users):
            self.id2users[i] = each_user['user_name']
            self.users2id[each_user['user_name']] = i

    def get_user_item_matrix(self, train_data):
        rate_matrix = numpy.zeros((len(self.users), len(self.issues)))

        # reorder activities by time
        for user_id, item_id, rate in train_data:
            rate_matrix[user_id, item_id] = rate
        # print(rate_matrix)
        return rate_matrix

    def train(self, train_data):
        self.train_data = train_data
        self.issue_similarity_matrix = self.get_issue_similarity_matrix()
        self.user_item_matrix = self.get_user_item_matrix(train_data)

        k = 30
        for i in range(len(self.issues)):
            ind = numpy.argsort(self.issue_similarity_matrix[:, i])
            self.issue_similarity_matrix[ind[:-k],i] = 0

        self.prediction_matrix = self.user_item_matrix @ self.issue_similarity_matrix

    def recommend(self, user_id, k):
        candidate_issues = self.prediction_matrix[user_id, :].tolist()

        for each_data in self.train_data:
            if each_data[0] == user_id:
                candidate_issues[each_data[1]] = 0


        # delete issue which active users are more than 2
        issue_user_count = {}
        for each_data in self.train_data:
            if each_data[1] not in issue_user_count.keys():
                issue_user_count[each_data[1]] = 0
            issue_user_count[each_data[1]] += 1

        # 评论人数特多的筛掉
        for each_issue, each_count in issue_user_count.items():
            if each_count > 1:
                candidate_issues[each_issue] = 0

        # sort and recommend
        sorted_orders = numpy.argsort(candidate_issues)
        # random.shuffle(candidate_issues)

        return sorted_orders[-k:]