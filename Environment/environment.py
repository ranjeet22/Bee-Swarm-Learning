"""Bee Meadow: a compact environment builder. No bees or training logic yet."""
import math
import os
import random
import pygame
from settings import *

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(ROOT, "assets")


def load_sprite(filename):
    """Load a transparent PNG if present; return None if it cannot be loaded."""
    path = os.path.join(ASSET_DIR, filename)
    try:
        return pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None


def fit_sprite(image, max_width, max_height):
    if image is None:
        return None
    factor = min(max_width / image.get_width(), max_height / image.get_height())
    size = (max(1, int(image.get_width() * factor)),
            max(1, int(image.get_height() * factor)))
    return pygame.transform.smoothscale(image, size)


class Meadow:
    def __init__(self):
        self.tree_sprite = load_sprite("tree.png")
        self.flower_sprite = load_sprite("flower_patch.png")
        self.trees = []
        self.flowers = []
        self.decor = []
        self.seed = 42
        self.tree_count = 8
        self.flower_count = 14
        self.generate(8, 14, 42)

    def generate(self, tree_count, flower_count, seed):
        """Create a new reproducible layout while avoiding major overlaps."""
        self.seed = int(seed)
        self.tree_count = max(0, min(80, int(tree_count)))
        self.flower_count = max(0, min(150, int(flower_count)))
        rng = random.Random(self.seed)
        self.trees, self.flowers = [], []
        self.decor = [(rng.randrange(WORLD_WIDTH), rng.randrange(WORLD_HEIGHT),
                       rng.choice([1, 2])) for _ in range(360)]

        hive = (WORLD_WIDTH * 0.5, WORLD_HEIGHT * 0.52)
        occupied = [(hive[0], hive[1], 70)]

        attempts = 0
        while len(self.trees) < self.tree_count and attempts < self.tree_count * 100 + 100:
            attempts += 1
            w = rng.randint(145, 210)
            h = int(w * 0.9)
            x = rng.randint(w // 2 + 12, WORLD_WIDTH - w // 2 - 12)
            y = rng.randint(h // 2 + 12, WORLD_HEIGHT - h // 2 - 12)
            radius = max(w, h) * 0.42
            if any(math.hypot(x-ox, y-oy) < radius + other + 26
                   for ox, oy, other in occupied):
                continue
            self.trees.append((x, y, w, h))
            occupied.append((x, y, radius))

        attempts = 0
        while len(self.flowers) < self.flower_count and attempts < self.flower_count * 100 + 200:
            attempts += 1
            w = rng.randint(75, 120)
            h = rng.randint(75, 120)
            x = rng.randint(w // 2 + 8, WORLD_WIDTH - w // 2 - 8)
            y = rng.randint(h // 2 + 8, WORLD_HEIGHT - h // 2 - 8)
            radius = max(w, h) * 0.40
            if math.hypot(x-hive[0], y-hive[1]) < radius + 125:
                continue
            if any(math.hypot(x-ox, y-oy) < radius + other + 10
                   for ox, oy, other in occupied):
                continue
            self.flowers.append((x, y, w, h, rng.randint(50, 100)))
            occupied.append((x, y, radius))

    def draw(self, screen, view, show_grid=False):
        sx, sy = view.width / WORLD_WIDTH, view.height / WORLD_HEIGHT
        scale = min(sx, sy)

        # Flat, calm base color with sparse hand-drawn grass strokes.
        screen.fill(GRASS, view)
        for x, y, size in self.decor:
            px, py = view.x + int(x*sx), view.y + int(y*sy)
            if size == 1:
                pygame.draw.line(screen, GRASS_DARK, (px, py), (px+2, py-2), 1)
            else:
                pygame.draw.line(screen, GRASS_LIGHT, (px, py), (px+3, py-1), 1)

        for x, y, w, h, resource in self.flowers:
            px, py = view.x + int(x*sx), view.y + int(y*sy)
            sprite = fit_sprite(self.flower_sprite, max(12, int(w*sx)), max(12, int(h*sy)))
            if sprite:
                screen.blit(sprite, sprite.get_rect(center=(px, py)))
            else:
                self.draw_fallback_flower(screen, px, py, max(7, int(18*scale)))

        for x, y, w, h in self.trees:
            px, py = view.x + int(x*sx), view.y + int(y*sy)
            sprite = fit_sprite(self.tree_sprite, max(12, int(w*sx)), max(12, int(h*sy)))
            if sprite:
                screen.blit(sprite, sprite.get_rect(center=(px, py)))
            else:
                pygame.draw.circle(screen, (59, 105, 47), (px, py), max(10, int(w*scale/2)))
                pygame.draw.circle(screen, (91, 143, 63), (px-5, py-5), max(6, int(w*scale/3)))

        hx, hy = view.x + int(WORLD_WIDTH*0.5*sx), view.y + int(WORLD_HEIGHT*0.52*sy)
        self.draw_hive(screen, hx, hy, max(0.5, scale))

        if show_grid:
            for wx in range(0, WORLD_WIDTH+1, 100):
                px = view.x + int(wx*sx)
                pygame.draw.line(screen, (203, 224, 176), (px, view.top), (px, view.bottom), 1)
            for wy in range(0, WORLD_HEIGHT+1, 100):
                py = view.y + int(wy*sy)
                pygame.draw.line(screen, (203, 224, 176), (view.left, py), (view.right, py), 1)

        pygame.draw.rect(screen, GRASS_DARK, view, 2)

    @staticmethod
    def draw_fallback_flower(screen, x, y, radius):
        colors = [(243, 100, 130), (255, 220, 100), (248, 248, 233), (180, 122, 221)]
        for i, color in enumerate(colors):
            angle = i * math.pi / 2
            center = (x + int(math.cos(angle)*radius*.55),
                      y + int(math.sin(angle)*radius*.55))
            pygame.draw.circle(screen, color, center, max(3, radius//3))
        pygame.draw.circle(screen, (255, 195, 52), (x, y), max(3, radius//4))

    @staticmethod
    def draw_hive(screen, x, y, scale):
        w, h = int(72*scale), int(64*scale)
        pygame.draw.ellipse(screen, (104, 79, 43), (x-w//2+3, y-h//2+5, w, h))
        pygame.draw.ellipse(screen, (234, 190, 112), (x-w//2, y-h//2, w, h))
        for offset in (-15, 3, 20):
            yy = y + int(offset*scale)
            pygame.draw.arc(screen, (169, 115, 57),
                (x-w//2+5, yy-int(13*scale), w-10, int(26*scale)), math.pi, math.tau,
                max(1, int(2*scale)))
        pygame.draw.ellipse(screen, (52, 40, 27),
                            (x-int(9*scale), y+int(7*scale), int(18*scale), int(12*scale)))


def draw_sidebar(screen, rect, meadow, fonts, message, show_grid):
    font, small, heading = fonts
    pygame.draw.rect(screen, PANEL, rect)
    x = rect.x + 20
    y = rect.y + 22
    screen.blit(heading.render("BEE MEADOW", True, INK), (x, y))
    screen.blit(small.render("Environment builder", True, MUTED), (x, y+31))
    pygame.draw.line(screen, BORDER, (x, y+61), (rect.right-20, y+61), 2)
    screen.blit(font.render("WORLD SETTINGS", True, INK), (x, y+80))

    field_defs = [
        ("trees", "Number of trees", str(meadow.tree_count), y+113),
        ("flowers", "Flower patches", str(meadow.flower_count), y+178),
        ("seed", "Random seed", str(meadow.seed), y+243),
    ]
    for key, label, value, fy in field_defs:
        screen.blit(font.render(label, True, INK), (x, fy))
        box = pygame.Rect(x, fy+25, rect.width-40, 34)
        pygame.draw.rect(screen, (255, 255, 250), box, border_radius=6)
        pygame.draw.rect(screen, BORDER, box, 2, border_radius=6)
        screen.blit(font.render(value, True, INK), (box.x+10, box.y+6))
        INPUT_RECTS[key] = box

    generate_rect = pygame.Rect(x, y+325, rect.width-40, 42)
    pygame.draw.rect(screen, BUTTON, generate_rect, border_radius=7)
    screen.blit(font.render("GENERATE WORLD", True, WHITE),
                font.render("GENERATE WORLD", True, WHITE).get_rect(center=generate_rect.center))
    reset_rect = pygame.Rect(x, y+377, rect.width-40, 36)
    pygame.draw.rect(screen, (233, 233, 218), reset_rect, border_radius=7)
    label = font.render("Reset defaults", True, INK)
    screen.blit(label, label.get_rect(center=reset_rect.center))
    GRID_RECT.update(x, y+435, rect.width-40, 36)
    pygame.draw.rect(screen, (233, 233, 218), GRID_RECT, border_radius=7)
    label = font.render("Grid: ON" if show_grid else "Grid: OFF", True, INK)
    screen.blit(label, label.get_rect(center=GRID_RECT.center))

    screen.blit(font.render("WORLD CONTENTS", True, INK), (x, y+493))
    lines = ["Meadow background", "Trees (provided sprite)",
             "Flower patches (provided sprite)", "Procedural beehive",
             "No bees or training logic"]
    for i, line in enumerate(lines):
        color = MUTED if i == 4 else INK
        screen.blit(small.render("• " + line, True, color), (x+2, y+524+i*28))
    # screen.blit(small.render("Click a field and type a number.", True, MUTED), (x, rect.bottom-75))
    # screen.blit(small.render("Enter = generate  |  G = grid  |  Esc = quit", True, MUTED),
    #             (x, rect.bottom-51))
    screen.blit(small.render(message[:36], True, INK), (x, rect.bottom-27))


# Shared rectangles for the very small UI, avoiding a separate UI module.
INPUT_RECTS = {}
GRID_RECT = pygame.Rect(0, 0, 0, 0)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Bee Meadow | Environment Builder")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 16)
    small = pygame.font.SysFont("arial", 13)
    heading = pygame.font.SysFont("arial", 24, bold=True)
    fonts = (font, small, heading)

    meadow = Meadow()
    show_grid = False
    active_field = None
    field_text = {key: str(value) for key, value in
                  {"trees": 8, "flowers": 14, "seed": 42}.items()}
    message = "World generated."
    running = True

    while running:
        clock.tick(FPS)
        width, height = screen.get_size()
        view = pygame.Rect(0, 0, max(320, width-SIDEBAR_WIDTH), height)
        sidebar = pygame.Rect(view.width, 0, width-view.width, height)
        INPUT_RECTS.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                elif active_field:
                    if event.key == pygame.K_RETURN:
                        try:
                            meadow.generate(int(field_text["trees"]), int(field_text["flowers"]),
                                            int(field_text["seed"]))
                            active_field = None
                            message = "World generated."
                        except ValueError:
                            message = "Please enter whole numbers."
                    elif event.key == pygame.K_BACKSPACE:
                        field_text[active_field] = field_text[active_field][:-1]
                    elif event.unicode.isdigit() or (event.unicode == "-" and not field_text[active_field]):
                        if len(field_text[active_field]) < 10:
                            field_text[active_field] += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if GRID_RECT.collidepoint(event.pos):
                    show_grid = not show_grid
                elif sidebar.collidepoint(event.pos):
                    for key, box in INPUT_RECTS.items():
                        if box.collidepoint(event.pos):
                            active_field = key
                            field_text[key] = ""
                            break
                    else:
                        local_y = event.pos[1]
                        if sidebar.x+20 <= event.pos[0] <= sidebar.right-20:
                            if sidebar.y+347 <= local_y <= sidebar.y+389:
                                try:
                                    meadow.generate(int(field_text["trees"] or 0),
                                                    int(field_text["flowers"] or 0),
                                                    int(field_text["seed"] or 0))
                                    field_text = {"trees": str(meadow.tree_count),
                                                  "flowers": str(meadow.flower_count),
                                                  "seed": str(meadow.seed)}
                                    active_field = None
                                    message = "World generated."
                                except ValueError:
                                    message = "Please enter whole numbers."
                            elif sidebar.y+399 <= local_y <= sidebar.y+435:
                                meadow.generate(8, 14, 42)
                                field_text = {"trees": "8", "flowers": "14", "seed": "42"}
                                active_field = None
                                message = "Defaults restored."
                            else:
                                active_field = None
                else:
                    active_field = None

        screen.fill(GRASS)
        meadow.draw(screen, view, show_grid)
        draw_sidebar(screen, sidebar, meadow, fonts, message, show_grid)

        # Redraw active input text over its displayed value.
        for key, box in INPUT_RECTS.items():
            if active_field == key:
                pygame.draw.rect(screen, BUTTON, box, 2, border_radius=6)
                screen.fill((255, 255, 250), box.inflate(-4, -4))
                screen.blit(font.render(field_text[key], True, INK), (box.x+10, box.y+6))
                pygame.draw.rect(screen, BUTTON, box, 2, border_radius=6)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
