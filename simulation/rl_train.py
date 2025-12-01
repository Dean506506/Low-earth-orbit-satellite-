
# rl_train.py
# Train RLModel over multiple episodes and log rewards

import numpy as np
from rl_model import RLModel

def train_rl(env, episodes=100):
    model = RLModel()
    reward_curve = []

    for ep in range(episodes):
        ep_rewards = []
        env.reset()

        while True:
            done, state, actions = env.get_state()
            if done:
                break

            action = model.select_action(state, actions)
            reward, next_state, next_actions = env.step(action)
            model.update(state, action, reward, next_state, next_actions)
            ep_rewards.append(reward)

        reward_curve.append(np.mean(ep_rewards))

    return model, reward_curve
