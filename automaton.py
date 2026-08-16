"""Run and visualize the House of Leaves cellular automaton."""

from __future__ import annotations

from dataclasses import dataclass
import math
import time

import numpy as np


# ============================================================================
# EXPERIMENT KNOBS -- edit these values, save the file, and rerun it.
# ============================================================================

GRID_WIDTH = 200
GRID_HEIGHT = 200

INITIAL_BLACK_PERCENT = 0.5
ROUNDS_PER_SECOND = 2.0
RANDOM_SEED = 40
START_PAUSED = True

# Number of recent rounds displayed in the graph and included in its average.
# If fewer rounds have been recorded, all available rounds are used.
WINDOW_ROUNDS = 100


# ============================================================================
# DISPLAY DETAILS -- not part of the automaton's rules.
# ============================================================================

# The GUI is 720 pixels tall, leaving room for window borders and the taskbar.
GRID_PANEL_PIXELS = 720
GRAPH_WIDTH = 460
GRAPH_SCROLL_ROUNDS = 10
BLACK_RGB = (8, 10, 15)
WHITE_RGB = (245, 246, 250)
TOTAL_LINE_RGB = (242, 244, 248)
MOD3_LINE_RGB = (75, 205, 255)
MOD4_LINE_RGB = (255, 172, 72)
MIN_EVENT_LOOPS_PER_SECOND = 60


NEIGHBOR_OFFSETS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),            (0, 1),
    (1, -1),  (1, 0),   (1, 1),
)


@dataclass(frozen=True)
class AutomatonConfig:
    grid_width: int
    grid_height: int
    initial_black_percent: float
    rounds_per_second: float
    random_seed: int

    @property
    def total_cells(self) -> int:
        return self.grid_width * self.grid_height

    def validate(self) -> None:
        for name, value in {
            "GRID_WIDTH": self.grid_width,
            "GRID_HEIGHT": self.grid_height,
        }.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer.")
        if self.grid_width % 2 or self.grid_height % 2:
            raise ValueError(
                "GRID_WIDTH and GRID_HEIGHT must be even so the wrapped "
                "checkerboard joins correctly."
            )
        if not math.isfinite(self.initial_black_percent) or not (
            0.0 <= self.initial_black_percent <= 100.0
        ):
            raise ValueError("INITIAL_BLACK_PERCENT must be between 0 and 100.")
        if (
            not math.isfinite(self.rounds_per_second)
            or self.rounds_per_second <= 0
        ):
            raise ValueError("ROUNDS_PER_SECOND must be finite and positive.")


class HouseOfLeavesAutomaton:
    """Alternate the mod-3 and mod-4 rules in a fixed checkerboard."""

    def __init__(self, config: AutomatonConfig):
        config.validate()
        self.config = config
        rows, columns = np.indices((config.grid_height, config.grid_width))
        self.mod3_cells = (rows + columns) % 2 == 0
        self.mod4_cells = ~self.mod3_cells
        self.rng = np.random.default_rng(config.random_seed)
        self.grid = np.empty(
            (config.grid_height, config.grid_width), dtype=np.bool_
        )
        self.round_number = 0
        self.reset()

    def reset(self) -> None:
        """Restore the configured seeded-random black percentage."""
        self.rng = np.random.default_rng(self.config.random_seed)
        black_count = math.floor(
            self.config.total_cells
            * self.config.initial_black_percent
            / 100.0
            + 0.5
        )
        self.grid.fill(False)
        black_indices = self.rng.permutation(self.config.total_cells)[:black_count]
        self.grid.flat[black_indices] = True
        self.round_number = 0

    def neighbor_sums(self) -> np.ndarray:
        """Count each cell's eight black neighbors, wrapping at every edge."""
        totals = np.zeros(self.grid.shape, dtype=np.uint8)
        for row_offset, column_offset in NEIGHBOR_OFFSETS:
            totals += np.roll(
                self.grid,
                shift=(-row_offset, -column_offset),
                axis=(0, 1),
            )
        return totals

    @staticmethod
    def states_from_neighbor_sums(
        neighbor_sums: np.ndarray,
        mod3_cells: np.ndarray,
    ) -> np.ndarray:
        """Apply the mod-3 or mod-4 rule assigned to each cell."""
        neighbor_sums = np.asarray(neighbor_sums)
        mod3_cells = np.asarray(mod3_cells, dtype=np.bool_)
        if neighbor_sums.shape != mod3_cells.shape:
            raise ValueError("neighbor_sums and mod3_cells must have the same shape.")
        mod3_result = neighbor_sums % 3 == 1
        mod4_result = neighbor_sums % 4 == 1
        return np.where(mod3_cells, mod3_result, mod4_result).astype(np.bool_)

    def step(self) -> None:
        """Calculate every cell's next color, then update the grid together."""
        self.grid = self.states_from_neighbor_sums(
            self.neighbor_sums(),
            self.mod3_cells,
        )
        self.round_number += 1

    def population_percentages(self) -> tuple[float, float, float]:
        """Return the total, mod-3, and mod-4 black percentages."""
        total = 100.0 * np.count_nonzero(self.grid) / self.config.total_cells
        mod3_count = np.count_nonzero(self.mod3_cells)
        mod4_count = np.count_nonzero(self.mod4_cells)
        mod3 = (
            100.0 * np.count_nonzero(self.grid & self.mod3_cells) / mod3_count
        )
        mod4 = (
            100.0
            * np.count_nonzero(self.grid & self.mod4_cells)
            / mod4_count
        )
        return total, mod3, mod4


def configured_automaton() -> HouseOfLeavesAutomaton:
    """Build an automaton from the experiment knobs at the top of this file."""
    return HouseOfLeavesAutomaton(
        AutomatonConfig(
            grid_width=GRID_WIDTH,
            grid_height=GRID_HEIGHT,
            initial_black_percent=INITIAL_BLACK_PERCENT,
            rounds_per_second=ROUNDS_PER_SECOND,
            random_seed=RANDOM_SEED,
        )
    )


def grid_surface(pygame: object, grid: np.ndarray) -> object:
    rgb = np.empty((*grid.shape, 3), dtype=np.uint8)
    rgb[~grid] = WHITE_RGB
    rgb[grid] = BLACK_RGB
    return pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))


def scaled_grid_size(config: AutomatonConfig) -> tuple[int, int]:
    scale = min(
        GRID_PANEL_PIXELS / config.grid_width,
        GRID_PANEL_PIXELS / config.grid_height,
    )
    return (
        max(1, round(config.grid_width * scale)),
        max(1, round(config.grid_height * scale)),
    )


PopulationPoint = tuple[float, float, float]


def window_rounds() -> int:
    """Return the validated graph and running-average window size."""
    if (
        isinstance(WINDOW_ROUNDS, bool)
        or not isinstance(WINDOW_ROUNDS, int)
        or WINDOW_ROUNDS < 1
    ):
        raise ValueError("WINDOW_ROUNDS must be a positive integer.")
    return WINDOW_ROUNDS


def running_average_at(
    history: list[PopulationPoint],
    view_end: int | None,
) -> PopulationPoint:
    """Average the rounds ending at the currently displayed graph endpoint."""
    if not history:
        return 0.0, 0.0, 0.0
    resolved_end = len(history) if view_end is None else view_end
    resolved_end = min(max(resolved_end, 1), len(history))
    start = max(0, resolved_end - window_rounds())
    samples = np.asarray(history[start:resolved_end], dtype=np.float64)
    averages = np.mean(samples, axis=0)
    return float(averages[0]), float(averages[1]), float(averages[2])


def probability_model_step(
    mod3_probability: float,
    mod4_probability: float,
) -> tuple[float, float]:
    """Apply one round of the independent-cell probability model."""
    sum_probabilities = np.zeros(9, dtype=np.float64)
    for mod3_black_neighbors in range(5):
        mod3_term = (
            math.comb(4, mod3_black_neighbors)
            * mod3_probability**mod3_black_neighbors
            * (1.0 - mod3_probability) ** (4 - mod3_black_neighbors)
        )
        for mod4_black_neighbors in range(5):
            mod4_term = (
                math.comb(4, mod4_black_neighbors)
                * mod4_probability**mod4_black_neighbors
                * (1.0 - mod4_probability) ** (4 - mod4_black_neighbors)
            )
            sum_probabilities[
                mod3_black_neighbors + mod4_black_neighbors
            ] += mod3_term * mod4_term
    next_mod3 = sum(
        probability
        for neighbor_sum, probability in enumerate(sum_probabilities)
        if neighbor_sum % 3 == 1
    )
    next_mod4 = sum(
        probability
        for neighbor_sum, probability in enumerate(sum_probabilities)
        if neighbor_sum % 4 == 1
    )
    return float(next_mod3), float(next_mod4)


def probability_model_prediction(
    config: AutomatonConfig,
    max_iterations: int = 5_000,
    tolerance: float = 1e-13,
) -> PopulationPoint:
    """Calculate the stable percentages predicted by the probability model."""
    black_count = math.floor(
        config.total_cells * config.initial_black_percent / 100.0 + 0.5
    )
    initial_probability = black_count / config.total_cells
    mod3_probability = initial_probability
    mod4_probability = initial_probability
    for _ in range(max_iterations):
        next_mod3, next_mod4 = probability_model_step(
            mod3_probability,
            mod4_probability,
        )
        difference = max(
            abs(next_mod3 - mod3_probability),
            abs(next_mod4 - mod4_probability),
        )
        mod3_probability, mod4_probability = next_mod3, next_mod4
        if difference < tolerance:
            break
    else:
        raise RuntimeError(
            f"Probability model did not stabilize within {max_iterations} rounds."
        )
    total_probability = (mod3_probability + mod4_probability) / 2.0
    return (
        100.0 * total_probability,
        100.0 * mod3_probability,
        100.0 * mod4_probability,
    )


def graph_history_window(
    history: list[PopulationPoint],
    view_end: int | None,
) -> tuple[list[PopulationPoint], int, int]:
    """Return one visible window; history index zero is the initial state."""
    if not history:
        return [], 0, 0
    resolved_end = len(history) if view_end is None else view_end
    resolved_end = min(max(resolved_end, 1), len(history))
    start = max(0, resolved_end - window_rounds())
    return history[start:resolved_end], start, resolved_end - 1


def scroll_graph_view(
    history_length: int,
    view_end: int | None,
    round_delta: int,
) -> int | None:
    """Move the graph endpoint by a number of rounds, or return to live view."""
    visible_rounds = window_rounds()
    if history_length <= visible_rounds:
        return None
    current_end = history_length if view_end is None else view_end
    new_end = min(
        history_length,
        max(visible_rounds, current_end + round_delta),
    )
    return None if new_end == history_length else new_end


def _draw_legend_item(
    pygame: object,
    screen: object,
    x: int,
    y: int,
    color: tuple[int, int, int],
    label: str,
    small_font: object,
) -> int:
    pygame.draw.line(screen, color, (x, y + 8), (x + 18, y + 8), 3)
    rendered = small_font.render(label, True, color)
    screen.blit(rendered, (x + 25, y))
    return x + 25 + rendered.get_width() + 16


def draw_population_graph(
    pygame: object,
    screen: object,
    rectangle: object,
    history: list[PopulationPoint],
    view_end: int | None,
    expected: PopulationPoint,
    font: object,
    small_font: object,
) -> None:
    """Draw total, mod-3, and mod-4 percentages on a fixed 0-100% scale."""
    background = (18, 22, 30)
    grid_color = (55, 64, 80)
    text_color = (220, 225, 235)
    muted_text = (150, 160, 178)
    live_color = (100, 220, 160)
    plot_left = rectangle.left + 62
    plot_right = rectangle.right - 18
    plot_top = rectangle.top + 205
    plot_bottom = rectangle.bottom - 54
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    pygame.draw.rect(screen, background, rectangle)
    screen.blit(
        font.render("Black cell proportion tracker", True, text_color),
        (rectangle.left + 22, rectangle.top + 18),
    )
    visible, first_round, last_round = graph_history_window(history, view_end)
    current = visible[-1] if visible else (0.0, 0.0, 0.0)
    average = running_average_at(history, view_end)
    visible_rounds = window_rounds()
    mode = "LIVE" if view_end is None else "HISTORY"
    screen.blit(
        small_font.render(
            f"{mode}  |  window: {visible_rounds} rounds",
            True,
            live_color if view_end is None else muted_text,
        ),
        (rectangle.left + 22, rectangle.top + 51),
    )
    screen.blit(
        small_font.render(
            f"End: total {current[0]:.1f}%   mod-3 {current[1]:.1f}%   "
            f"mod-4 {current[2]:.1f}%",
            True,
            muted_text,
        ),
        (rectangle.left + 22, rectangle.top + 78),
    )
    screen.blit(
        small_font.render(
            f"Avg {visible_rounds}: total {average[0]:.3f}%   "
            f"mod-3 {average[1]:.3f}%   mod-4 {average[2]:.3f}%",
            True,
            muted_text,
        ),
        (rectangle.left + 22, rectangle.top + 103),
    )
    screen.blit(
        small_font.render(
            f"Model: total {expected[0]:.3f}%   "
            f"mod-3 {expected[1]:.3f}%   mod-4 {expected[2]:.3f}%",
            True,
            muted_text,
        ),
        (rectangle.left + 22, rectangle.top + 128),
    )
    legend_x = rectangle.left + 22
    legend_y = rectangle.top + 158
    legend_x = _draw_legend_item(
        pygame, screen, legend_x, legend_y, TOTAL_LINE_RGB, "Total", small_font
    )
    legend_x = _draw_legend_item(
        pygame, screen, legend_x, legend_y, MOD3_LINE_RGB, "Mod-3", small_font
    )
    _draw_legend_item(
        pygame,
        screen,
        legend_x,
        legend_y,
        MOD4_LINE_RGB,
        "Mod-4",
        small_font,
    )

    for fraction in (0.0, 0.5, 1.0):
        y = round(plot_bottom - fraction * plot_height)
        pygame.draw.line(screen, grid_color, (plot_left, y), (plot_right, y), 1)
        label = small_font.render(f"{round(fraction * 100)}%", True, muted_text)
        screen.blit(
            label,
            (plot_left - label.get_width() - 8, y - label.get_height() // 2),
        )
    pygame.draw.line(screen, grid_color, (plot_left, plot_top), (plot_left, plot_bottom), 2)
    pygame.draw.line(screen, grid_color, (plot_left, plot_bottom), (plot_right, plot_bottom), 2)

    if visible:
        if len(visible) == 1:
            x_positions = [plot_right]
        else:
            x_positions = [
                plot_left + index * plot_width / (len(visible) - 1)
                for index in range(len(visible))
            ]
        for series_index, color in enumerate(
            (TOTAL_LINE_RGB, MOD3_LINE_RGB, MOD4_LINE_RGB)
        ):
            points = [
                (round(x), round(plot_bottom - point[series_index] * plot_height / 100.0))
                for x, point in zip(x_positions, visible)
            ]
            if len(points) == 1:
                pygame.draw.circle(screen, color, points[0], 3)
            else:
                pygame.draw.lines(screen, color, False, points, 2)
        first_label = small_font.render(str(first_round), True, muted_text)
        last_label = small_font.render(str(last_round), True, muted_text)
        screen.blit(first_label, (plot_left, plot_bottom + 12))
        screen.blit(last_label, (plot_right - last_label.get_width(), plot_bottom + 12))
    controls = small_font.render(
        "Left/Right: scroll   Home: oldest   End: live", True, muted_text
    )
    screen.blit(
        controls,
        (rectangle.left + (rectangle.width - controls.get_width()) // 2, rectangle.bottom - 26),
    )


def run() -> None:
    """Open the animation and run until the user quits."""
    if not isinstance(START_PAUSED, bool):
        raise ValueError("START_PAUSED must be True or False.")
    try:
        import pygame
    except ImportError as error:
        raise SystemExit(
            "Pygame is not installed. Run: python -m pip install pygame"
        ) from error

    automaton = configured_automaton()
    expected = probability_model_prediction(automaton.config)
    grid_size = scaled_grid_size(automaton.config)
    grid_position = (
        (GRID_PANEL_PIXELS - grid_size[0]) // 2,
        (GRID_PANEL_PIXELS - grid_size[1]) // 2,
    )
    pygame.init()
    screen = pygame.display.set_mode(
        (GRID_PANEL_PIXELS + GRAPH_WIDTH, GRID_PANEL_PIXELS)
    )
    graph_rectangle = pygame.Rect(GRID_PANEL_PIXELS, 0, GRAPH_WIDTH, GRID_PANEL_PIXELS)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 22)
    interval = 1.0 / automaton.config.rounds_per_second
    next_round_at = time.perf_counter() + interval
    event_rate = max(
        MIN_EVENT_LOOPS_PER_SECOND,
        math.ceil(automaton.config.rounds_per_second * 2),
    )
    history = [automaton.population_percentages()]
    graph_view_end: int | None = None
    paused = START_PAUSED
    single_step = False
    running = True
    redraw = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                        next_round_at = time.perf_counter() + interval
                    elif event.key == pygame.K_n and paused:
                        single_step = True
                    elif event.key == pygame.K_r:
                        automaton.reset()
                        history[:] = [automaton.population_percentages()]
                        graph_view_end = None
                        paused = START_PAUSED
                        redraw = True
                        next_round_at = time.perf_counter() + interval
                    elif event.key in (pygame.K_LEFT, pygame.K_LEFTBRACKET):
                        graph_view_end = scroll_graph_view(
                            len(history), graph_view_end, -GRAPH_SCROLL_ROUNDS
                        )
                        redraw = True
                    elif event.key in (pygame.K_RIGHT, pygame.K_RIGHTBRACKET):
                        graph_view_end = scroll_graph_view(
                            len(history), graph_view_end, GRAPH_SCROLL_ROUNDS
                        )
                        redraw = True
                    elif event.key == pygame.K_HOME:
                        graph_view_end = scroll_graph_view(
                            len(history), graph_view_end, -len(history)
                        )
                        redraw = True
                    elif event.key == pygame.K_END:
                        graph_view_end = None
                        redraw = True
                elif event.type == pygame.MOUSEWHEEL:
                    mouse_x, _ = pygame.mouse.get_pos()
                    if mouse_x >= GRID_PANEL_PIXELS:
                        graph_view_end = scroll_graph_view(
                            len(history),
                            graph_view_end,
                            -event.y * GRAPH_SCROLL_ROUNDS,
                        )
                        redraw = True

            now = time.perf_counter()
            if single_step or (not paused and now >= next_round_at):
                automaton.step()
                history.append(automaton.population_percentages())
                single_step = False
                redraw = True
                next_round_at = time.perf_counter() + interval

            if redraw:
                screen.fill(BLACK_RGB)
                surface = grid_surface(pygame, automaton.grid)
                screen.blit(pygame.transform.scale(surface, grid_size), grid_position)
                draw_population_graph(
                    pygame,
                    screen,
                    graph_rectangle,
                    history,
                    graph_view_end,
                    expected,
                    font,
                    small_font,
                )
                state = "PAUSED" if paused else "RUNNING"
                pygame.display.set_caption(
                    "House of Leaves Automaton | mod-3 / mod-4 checkerboard | "
                    f"round {automaton.round_number} | "
                    f"black {history[-1][0]:.1f}% | {state} | "
                    "Space: pause  N: step  R: reset  Q: quit"
                )
                pygame.display.flip()
                redraw = False

            clock.tick(event_rate)
    finally:
        pygame.quit()


if __name__ == "__main__":
    run()
