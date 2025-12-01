
# rl_model.py
# Linear Q-learning for satellite activation

import numpy as np

class RLModel:
    def __init__(self, state_dim=5, alpha=0.05, gamma=0.9, epsilon=0.1):
        self.state_dim = state_dim
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.weights = {}  # action_id -> weight vector

    def ensure_action(self, action_id):
        if action_id not in self.weights:
            self.weights[action_id] = np.zeros(self.state_dim)

    def q_value(self, state, action_id):
        self.ensure_action(action_id)
        return np.dot(self.weights[action_id], state)

    def select_action(self, state, available_actions):
        # epsilon-greedy
        if np.random.rand() < self.epsilon:
            return np.random.choice(available_actions)

        qs = {a: self.q_value(state, a) for a in available_actions}
        return max(qs, key=qs.get)

    def update(self, state, action_id, reward, next_state, next_actions):
        self.ensure_action(action_id)
        q_old = self.q_value(state, action_id)

        if len(next_actions) == 0:
            q_target = reward
        else:
            q_next = max([self.q_value(next_state, a) for a in next_actions])
            q_target = reward + self.gamma * q_next

        td_error = q_target - q_old
        self.weights[action_id] += self.alpha * td_error * state

# 加在 RLModel class 裡面
    def select_best(self, feasible_dict, feature_table):
        best_sat = None
        max_q = -float('inf')
        
        # 假設 action_id = 0 代表 "Activate" 這個動作
        # 我們用同一組權重來評估每一顆衛星的品質
        action_key = 0 
        
        for sat_id, is_feasible in feasible_dict.items():
            if not is_feasible:
                continue
            
            # 取得該衛星的特徵向量 (state)
            state = np.array(feature_table[sat_id])
            
            # 計算分數
            q_val = self.q_value(state, action_key)
            
            # 找最大值
            if q_val > max_q:
                max_q = q_val
                best_sat = sat_id
                
        return best_sat