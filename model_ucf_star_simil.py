
import numpy
import tqdm
import recommend


class UCFStarSimilRecommendModel(recommend.RecommendModel):
    def __init__(self, project):
        self.project = project
        self.issues = project.get_issues()
        self.users = project.get_users()
        self.build_acceleration_structure()

    def get_name(self):
        return 'UCFStarSimil'

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

    def get_user_similarity(self, left_index, right_index):
        user_left = self.users[left_index]
        user_right = self.users[right_index]
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
        left_vec[len(star_map)] = 1

        for each_star in user_right['star']:
            right_vec[star_map[each_star]] = 1
        right_vec[len(star_map)] = 1

        return numpy.dot(left_vec, right_vec)/(numpy.linalg.norm(left_vec)*numpy.linalg.norm(right_vec))

    def get_user_similarity_matrix(self):
        user_simil_matrix = numpy.zeros((len(self.users), len(self.users)))

        with tqdm.tqdm(total=len(self.users)*len(self.users)//2) as pbar:
            user_num = len(self.users)
            for i in range(user_num):
                for j in range(i + 1):
                    if j > i:
                        continue
                    if i == j:
                        user_simil_matrix[i, j] = 1
                        continue
                    tmp = self.get_user_similarity(i, j)
                    user_simil_matrix[i, j] = tmp
                    user_simil_matrix[j, i] = tmp
                    pbar.update(1)

        return user_simil_matrix

    def train(self, train_data):
        self.train_data = train_data
        self.user_similarity_matrix = self.get_user_similarity_matrix()
        self.user_item_matrix = self.get_user_item_matrix(train_data)
        self.prediction_matrix = self.user_similarity_matrix @ self.user_item_matrix
    def recommend(self, user_id, k):
        candidate_issues = self.prediction_matrix[user_id, :].tolist()

        '''
        for each_data in self.train_data:
            if each_data[0] == user_id:
                candidate_issues[each_data[1]] = 0
        '''

        '''
        # delete issue which active users are more than 2
        issue_user_count = {}
        for each_data in self.train_data:
            if each_data[1] not in issue_user_count.keys():
                issue_user_count[each_data[1]] = 0
            issue_user_count[each_data[1]] += 1

        for each_issue, each_count in issue_user_count.items():
            if each_count > 1:
                candidate_issues[each_issue] = 0
        '''
        # sort and recommend
        sorted_orders = numpy.argsort(candidate_issues)
        # random.shuffle(candidate_issues)

        return sorted_orders[-k:]