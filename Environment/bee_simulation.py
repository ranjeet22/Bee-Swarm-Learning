
import math
import random


class BeeWorld:
    # Actions available to the bee's neural network
    TURN_LEFT = 0
    TURN_RIGHT = 1
    FLY_FORWARD = 2
    FORAGE = 3
    RETURN_TO_HIVE = 4
    EXPLORE = 5

    ACTION_COUNT = 6
    OBSERVATION_SIZE = 11

    def __init__(self, width=900, height=600, seed=42):
        self.width = width
        self.height = height
        self.seed = seed
        self.rng = random.Random(seed)

        self.hive = (width / 2, height / 2)
        self.reset()

    def reset(self, seed=None):
        """Start a fresh episode."""
        if seed is not None:
            self.rng.seed(seed)

        margin = 35

        self.flowers = [
            {
                "x": self.rng.uniform(margin, self.width - margin),
                "y": self.rng.uniform(margin, self.height - margin),
                "nectar": 1.0,
            }
            for _ in range(12)
        ]

        self.x, self.y = self.hive
        self.heading = self.rng.uniform(-math.pi, math.pi)

        self.energy = 1.0
        self.cargo = 0.0
        self.capacity = 3.0
        self.delivered = 0.0
        self.steps = 0

        return self.observe()

    def distance(self, x, y):
        """Calculate distance from the bee to a position."""
        return math.hypot(self.x - x, self.y - y)

    def nearest_flower(self):
        """Find the nearest flower that still contains nectar."""
        available = [
            flower
            for flower in self.flowers
            if flower["nectar"] > 0
        ]

        if not available:
            return None

        return min(
            available,
            key=lambda flower: self.distance(
                flower["x"], flower["y"]
            ),
        )

    def get_target_distance(self):
        """Distance to the bee's current useful target."""
        # Head toward the hive when carrying a full load
        # or when energy is running low.
        if self.cargo >= self.capacity or self.energy < 0.25:
            return self.distance(*self.hive)

        flower = self.nearest_flower()

        if flower is not None:
            return self.distance(flower["x"], flower["y"])

        return self.distance(*self.hive)

    def observe(self):
        """
        Return 11 numerical features:
        0-2: nearest flower direction and distance
        3:   flower nectar availability
        4-6: hive direction and distance
        7:   remaining energy
        8:   cargo fraction
        9-10: heading represented by sine and cosine
        """
        flower = self.nearest_flower()
        scale = math.hypot(self.width, self.height)

        if flower is None:
            fx, fy = self.hive
            flower_available = 0.0
        else:
            fx, fy = flower["x"], flower["y"]
            flower_available = 1.0

        flower_dx = (fx - self.x) / self.width
        flower_dy = (fy - self.y) / self.height

        hive_dx = (self.hive[0] - self.x) / self.width
        hive_dy = (self.hive[1] - self.y) / self.height

        return [
            max(-1.0, min(1.0, flower_dx * 2)),
            max(-1.0, min(1.0, flower_dy * 2)),
            min(1.0, self.distance(fx, fy) / scale),
            flower_available,
            max(-1.0, min(1.0, hive_dx * 2)),
            max(-1.0, min(1.0, hive_dy * 2)),
            min(1.0, self.distance(*self.hive) / scale),
            self.energy,
            self.cargo / self.capacity,
            math.sin(self.heading),
            math.cos(self.heading),
        ]

    def step(self, action):
        """Perform one action and return observation, reward, done, info."""
        if action not in range(self.ACTION_COUNT):
            raise ValueError(f"Invalid action: {action}")

        # Record distance before taking the action.
        old_distance = self.get_target_distance()

        reward = -0.001
        self.steps += 1

        if action == self.TURN_LEFT:
            self.heading -= 0.3

        elif action == self.TURN_RIGHT:
            self.heading += 0.3

        elif action in (self.FLY_FORWARD, self.EXPLORE):
            if action == self.EXPLORE:
                self.heading += self.rng.uniform(-0.2, 0.2)

            self.x += math.cos(self.heading) * 3
            self.y += math.sin(self.heading) * 3
            self.energy -= 0.0005

        elif action == self.FORAGE:
            flower = self.nearest_flower()

            if (
                flower is not None
                and self.distance(flower["x"], flower["y"]) <= 18
                and self.cargo < self.capacity
            ):
                amount = min(
                    1.0,
                    flower["nectar"],
                    self.capacity - self.cargo,
                )

                flower["nectar"] -= amount
                self.cargo += amount
                reward += 0.2 * amount
            else:
                reward -= 0.01

        elif action == self.RETURN_TO_HIVE:
            target_x, target_y = self.hive

            desired = math.atan2(
                target_y - self.y,
                target_x - self.x,
            )

            difference = (
                desired - self.heading + math.pi
            ) % (2 * math.pi) - math.pi

            self.heading += max(
                -0.3,
                min(0.3, difference),
            )

            self.x += math.cos(self.heading) * 3
            self.y += math.sin(self.heading) * 3
            self.energy -= 0.0005

        # Keep the bee inside the world.
        self.x = max(5, min(self.width - 5, self.x))
        self.y = max(5, min(self.height - 5, self.y))
        self.energy = max(0.0, self.energy)

        # Reward movement toward the current target.
        new_distance = self.get_target_distance()
        reward += 0.02 * (old_distance - new_distance) / 3.0

        # Deliver nectar whenever the bee is near the hive.
        if self.distance(*self.hive) <= 24 and self.cargo > 0:
            amount = self.cargo
            self.delivered += amount
            reward += 3.0 * amount
            self.cargo = 0.0

        done = self.energy <= 0 or self.steps >= 2500

        info = {
            "nectar_delivered": self.delivered,
            "cargo": self.cargo,
            "energy": self.energy,
            "steps": self.steps,
            "remaining_flowers": sum(
                flower["nectar"] > 0
                for flower in self.flowers
            ),
        }

        return self.observe(), reward, done, info

    def test_foraging(self):
        """Test nectar collection and delivery deterministically."""
        self.reset(seed=123)

        hive_x, hive_y = self.hive
        flower = self.flowers[0]

        # Place a flower 40 pixels to the right of the hive.
        flower["x"] = hive_x + 40
        flower["y"] = hive_y
        flower["nectar"] = 1.0

        # Empty the other flowers.
        for other in self.flowers[1:]:
            other["nectar"] = 0.0

        # Position the bee at the flower.
        self.x = flower["x"]
        self.y = flower["y"]

        _, _, _, _ = self.step(self.FORAGE)

        assert abs(self.cargo - 1.0) < 1e-9
        assert abs(flower["nectar"]) < 1e-9

        print("PASS: Nectar collection")
        print("Cargo after foraging:", self.cargo)
        print("Flower nectar remaining:", flower["nectar"])

        # Simulate the bee arriving at the hive.
        self.x, self.y = self.hive

        _, _, _, _ = self.step(self.RETURN_TO_HIVE)

        assert abs(self.cargo) < 1e-9
        assert abs(self.delivered - 1.0) < 1e-9

        print("PASS: Nectar delivery")
        print("Cargo after delivery:", self.cargo)
        print("Total nectar delivered:", self.delivered)
        print("Observation size:", len(self.observe()))
        print("Available actions:", self.ACTION_COUNT)

    def test_movement(self):
        """Check that movement and turning work."""
        self.reset(seed=123)

        old_position = (self.x, self.y)
        self.step(self.FLY_FORWARD)

        assert (self.x, self.y) != old_position
        print("PASS: Forward movement")

        old_heading = self.heading
        self.step(self.TURN_LEFT)

        assert self.heading != old_heading
        print("PASS: Turning")

    def test_observations(self):
        """Check observation size and numerical validity."""
        obs = self.reset(seed=123)

        assert len(obs) == self.OBSERVATION_SIZE
        assert all(math.isfinite(value) for value in obs)

        print("PASS: Observations")
        print("Observation:", obs)

    def run_tests(self):
        print("Testing BeeWorld...\n")
        self.test_movement()
        self.test_observations()
        self.test_foraging()
        print("\nAll tests passed!")


if __name__ == "__main__":
    world = BeeWorld()
    world.run_tests()
