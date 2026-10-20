
import copy
import numpy as np

from bee_brain import BeeBrain
from bee_gym_env import BeeGymEnv


class Evolution:
    def __init__(
        self,
        population_size=10,
        elite_count=2,
        mutation_rate=0.10,
        mutation_strength=0.30,
        seed=42,
    ):
        if population_size < 2:
            raise ValueError("Population must contain at least 2 bees.")
        if not 1 <= elite_count < population_size:
            raise ValueError("Elite count must be smaller than population.")

        self.rng = np.random.default_rng(seed)
        self.population_size = population_size
        self.elite_count = elite_count
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength

        self.population = [
            BeeBrain(seed=int(self.rng.integers(0, 2**31)))
            for _ in range(population_size)
        ]

        self.best_brain = None
        self.best_fitness = -float("inf")

    def evaluate(self, brain, episodes=2):
        """Evaluate one brain on repeatable environment seeds."""
        total_rewards = []
        nectar_values = []

        for episode in range(episodes):
            env = BeeGymEnv()
            observation, info = env.reset(seed=100 + episode)

            total_reward = 0.0
            terminated = False
            truncated = False

            while not (terminated or truncated):
                action = brain.choose_action(observation)

                observation, reward, terminated, truncated, info = (
                    env.step(action)
                )
                total_reward += reward

            nectar_values.append(info["nectar_delivered"])
            total_rewards.append(total_reward)
            env.close()

        mean_reward = float(np.mean(total_rewards))
        mean_nectar = float(np.mean(nectar_values))

        # Make delivered nectar the primary objective.
        fitness = mean_nectar * 10.0 + mean_reward

        return {
            "fitness": fitness,
            "mean_reward": mean_reward,
            "mean_nectar": mean_nectar,
        }

    def mutate(self, parent):
        child = copy.deepcopy(parent)

        for name in ("weights1", "bias1", "weights2", "bias2"):
            values = getattr(child, name)
            mask = self.rng.random(values.shape) < self.mutation_rate
            noise = self.rng.normal(
                0.0, self.mutation_strength, size=values.shape
            )
            values += mask * noise

        return child

    def run_generation(self, episodes=2):
        results = [
            self.evaluate(brain, episodes)
            for brain in self.population
        ]

        ranked = sorted(
            zip(self.population, results),
            key=lambda item: item[1]["fitness"],
            reverse=True,
        )

        generation_best_brain, generation_best = ranked[0]

        if generation_best["fitness"] > self.best_fitness:
            self.best_fitness = generation_best["fitness"]
            self.best_brain = copy.deepcopy(generation_best_brain)

        next_population = [
            copy.deepcopy(brain)
            for brain, _ in ranked[:self.elite_count]
        ]

        while len(next_population) < self.population_size:
            parent_index = int(self.rng.integers(0, self.elite_count))
            parent = ranked[parent_index][0]
            next_population.append(self.mutate(parent))

        self.population = next_population

        return {
            "best_fitness": generation_best["fitness"],
            "mean_fitness": float(
                np.mean([r["fitness"] for r in results])
            ),
            "best_nectar": generation_best["mean_nectar"],
            "best_reward": generation_best["mean_reward"],
        }

    def save_best(self, path="best_bee.npz"):
        if self.best_brain is None:
            raise RuntimeError("Run at least one generation first.")

        np.savez(
            path,
            weights1=self.best_brain.weights1,
            bias1=self.best_brain.bias1,
            weights2=self.best_brain.weights2,
            bias2=self.best_brain.bias2,
        )


if __name__ == "__main__":
    evolution = Evolution(
        population_size=10,
        elite_count=2,
        seed=42,
    )

    generations = 5

    for generation in range(1, generations + 1):
        metrics = evolution.run_generation(episodes=2)

        print(
            f"Generation {generation:02d} | "
            f"Best fitness: {metrics['best_fitness']:.3f} | "
            f"Mean fitness: {metrics['mean_fitness']:.3f} | "
            f"Best nectar: {metrics['best_nectar']:.2f} | "
            f"Best reward: {metrics['best_reward']:.3f}"
        )

    evolution.save_best()
    print("\nSaved best network to best_bee.npz")