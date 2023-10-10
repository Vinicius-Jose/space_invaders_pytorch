import gymnasium as gym
import torch.nn as nn
import torch
import numpy as np


class AtariGame:
    def __init__(self, game: str) -> None:
        self.game = game
        self.env: gym.Env = None

    def initialize_atari_env_game(self, render_mode="rgb_array"):
        self.env = gym.make(self.game, render_mode=render_mode)
        return self.env


class AtariAI:
    def __init__(
        self,
        save_dir: str,
        save_file_name: str,
        module: nn.Module,
        optimizer: torch.optim.Optimizer = None,
        criterion: nn.MSELoss = None,
    ) -> None:
        self.save_dir = save_dir
        self.save_file_name = save_file_name
        self.save_path = self.save_dir + f"{self.save_file_name}.chkpt"
        self.module = module
        self.optimizer: torch.optim.Optimizer = (
            optimizer if optimizer else torch.optim.SGD(module.parameters(), lr=0.01)
        )
        self.criterion: torch.nn.MSELoss = (
            criterion if criterion else torch.nn.MSELoss()
        )

    def train(self, epochs: int, env: gym.Env) -> None:
        state, info = env.reset()
        self.module.train()
        for _ in range(epochs):
            state = torch.tensor(np.array([state]), dtype=torch.float32)
            self.optimizer.zero_grad()
            action = self.module(state, model="online")
            action = action.topk(1)[1][0].item()
            next_state, reward, n_state, done, info = env.step(action)
            target = self.module(state, model="target")
            loss = self.criterion(next_state, target)
            loss.backward()
            self.optimizer.step()
            state = next_state
        self.save()
        env.close()

    def play(self, env: gym.Env) -> int:
        state = env.reset()
        done = False
        self.module.eval()
        score = 0
        while not done:
            state = env.render()
            action = self.module(state)
            next_state, reward, n_state, done, info = env.step(action)
            done = info.get("lives") == 0
            score += reward
        env.close()
        return reward

    def load(self) -> None:
        state_dict = torch.load(self.save_path)
        self.module.load_state_dict(state_dict)

    def save(self) -> None:
        torch.save(
            self.module.state_dict(),
            self.save_path,
        )
