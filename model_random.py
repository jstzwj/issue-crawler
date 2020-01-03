
import random
import recommend

class RandomRecommendModel(recommend.RecommendModel):
    def __init__(self, project):
        self.issues = project.get_issues()
        self.users = project.get_users()
    def get_name(self):
        return 'random'
    def train(self, train_data):
        self.train_data = train_data
    def recommend(self, user_id, k):
        candidate_issues = list(range(len(self.issues)))
        
        for each_data in self.train_data:
            if each_data[0] == user_id:
                candidate_issues.remove(each_data[1])

        random.shuffle(candidate_issues)
        return candidate_issues[:k]