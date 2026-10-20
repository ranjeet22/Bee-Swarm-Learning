
import gymnasium as gym
import numpy as np
from gymnasium import spaces

from bee_simulation import BeeWorld


class BeeGymEnv(gym.Env):
    """Gymnasium wrapper for the bee foraging simulation."""

    metadata = {"render_modes": []}

    def __init__(self, width=900, height=600, seed=42):
        super().__init__()

        self.world = BeeWorld(
            width=width,
            height=height,
            seed=seed,
        )

        # Six possible actions, represented by integers 0 through 5.
        self.action_space = spaces.Discrete(
            self.world.ACTION_COUNT
        )

        # Eleven numerical observations from BeeWorld.observe().
        self.observation_space = spaces.Box(
            low=np.array(
                [-1, -1, 0, 0, -1, -1, 0, 0, 0, -1, -1],
                dtype=np.float32,
            ),
            high=np.ones(11, dtype=np.float32),
            dtype=np.float32,
        )

    def _get_observation(self):
        """Convert the simulation observation to a NumPy array."""
        return np.asarray(
            self.world.observe(),
            dtype=np.float32,
        )

    def reset(self, seed=None, options=None):
        """Start a new episode."""
        super().reset(seed=seed)

        observation = self.world.reset(seed=seed)

        info = {
            "nectar_delivered": self.world.delivered,
            "energy": self.world.energy,
            "steps": self.world.steps,
        }

        return (
            np.asarray(observation, dtype=np.float32),
            info,
        )

    def step(self, action):
        """Execute one action using the Gymnasium API."""
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action: {action}")

        observation, reward, done, info = self.world.step(
            int(action)
        )

        # Energy depletion is a natural terminal condition.
        terminated = self.world.energy <= 0

        # The maximum number of steps is a time limit.
        truncated = (
            self.world.steps >= 2500 and not terminated
        )

        return (
            np.asarray(observation, dtype=np.float32),
            float(reward),
            terminated,
            truncated,
            info,
        )

    def close(self):
        """Release environment resources if needed."""
        pass


if __name__ == "__main__":
    from gymnasium.utils.env_checker import check_env

    env = BeeGymEnv()

    print("Checking Gymnasium compatibility...")
    check_env(env)
    print("PASS: Gymnasium environment checks")

    observation, info = env.reset(seed=42)

    print("\nObservation shape:", observation.shape)
    print("Action space:", env.action_space)
    print("Observation space:", env.observation_space)

    for step_number in range(5):
        action = env.action_space.sample()

        observation, reward, terminated, truncated, info = (
            env.step(action)
        )

        print(
            f"Step {step_number + 1}: "
            f"action={action}, "
            f"reward={reward:.3f}, "
            f"delivered={info['nectar_delivered']:.1f}"
        )

        if terminated or truncated:
            print("Episode ended.")
            break

    env.close()
