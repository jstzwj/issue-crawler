
import numpy
import tqdm
import recommend


class StarBasedRecommendModel(recommend.RecommendModel):
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

    def get_user_item_matrix(self, end_time=None):
        rate_matrix = numpy.zeros((len(self.users), len(self.issues)))

        # reorder activities by time
        for i, each_issue in enumerate(self.issues):
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
                    rate_matrix[self.users2id[each_user], i] = each_count/len(each_issue['timeline'])

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
            for i, each_user_i in enumerate(self.users):
                for j, each_user_j in enumerate(self.users):
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
        self.user_item_matrix = self.get_user_item_matrix()
        self.prediction_matrix = self.user_similarity_matrix @ self.user_item_matrix
    def recommend(self, user_id, k):
        candidate_issues = self.prediction_matrix[user_id, :].tolist()
        for each_data in self.train_data:
            if each_data[0] == user_id:
                candidate_issues[each_data[1]] = 0

        sorted_orders = numpy.argsort(candidate_issues)
        # random.shuffle(candidate_issues)

        return sorted_orders[-k:]