import numpy as np

class BeeBrain:
    """A small neural network mapping bee observations to action scores."""

    def __init__(self, input_size=11, hidden_size=16, output_size=6, seed=None):
        rng = np.random.default_rng(seed)

        self.weights1 = rng.normal(
            0, np.sqrt(2 / input_size), (input_size, hidden_size)
        )
        self.bias1 = np.zeros(hidden_size)

        self.weights2 = rng.normal(
            0, np.sqrt(2 / hidden_size), (hidden_size, output_size)
        )
        self.bias2 = np.zeros(output_size)

    def predict(self, observation):
        """Return one score for each of the six available actions."""
        inputs = np.asarray(observation, dtype=np.float64)

        if inputs.shape != (11,):
            raise ValueError(
                f"Expected 11 observation values, received {inputs.shape}"
            )

        hidden = np.tanh(inputs @ self.weights1 + self.bias1)
        scores = hidden @ self.weights2 + self.bias2

        return scores

    def choose_action(self, observation):
        """Choose the action with the highest score."""
        scores = self.predict(observation)
        return int(np.argmax(scores))


if __name__ == "__main__":
    brain = BeeBrain(seed=42)

    # A sample observation with 11 features.
    observation = np.zeros(11, dtype=np.float32)

    scores = brain.predict(observation)
    action = brain.choose_action(observation)

    action_names = [
        "TURN_LEFT",
        "TURN_RIGHT",
        "FLY_FORWARD",
        "FORAGE",
        "RETURN_TO_HIVE",
        "EXPLORE",
    ]

    print("Input features:", len(observation))
    print("Output scores:", scores)
    print("Number of action scores:", len(scores))
    print("Selected action:", action_names[action])
