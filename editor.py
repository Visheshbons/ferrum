from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from convert_level import decode_level_rows, encode_level_rows


LEVELS_DIR = Path(__file__).resolve().parent / "levels"
DEFAULT_LEVEL_SIZE = (61, 29)
WINDOW_SIZE = (960, 600)
UI_HEIGHT = 72
TILE_SIZE = 32
PAN_SPEED = 900

TILE_ORDER = [".", "#", "_", "P", "T"]
TILE_KEYS = {
    pygame.K_1: ".",
    pygame.K_2: "#",
    pygame.K_3: "_",
    pygame.K_4: "P",
    pygame.K_5: "T",
}
TILE_COLORS = {
    ".": (30, 30, 42),
    "#": (95, 95, 120),
    "_": (135, 135, 185),
    "P": (125, 205, 255),
    "T": (255, 178, 92),
}


def resolve_level_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.suffix:
        path = path.with_suffix(".world")
    if not path.is_absolute() and not path.exists():
        path = LEVELS_DIR / path
    return path


def delete_generated_json(level_path: Path) -> None:
    json_path = level_path.with_suffix(".json")
    if json_path.exists():
        json_path.unlink()


class WorldEditor:
    def __init__(self, level_path: str | Path) -> None:
        pygame.init()
        pygame.display.set_caption("Ferrum World Editor")

        self.level_path = resolve_level_path(level_path)
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.current_tile = "#"
        self.dirty = False
        self.grid = self._load_grid(self.level_path)
        self._center_camera_on_spawn()

    def _blank_grid(self, width: int, height: int) -> list[list[str]]:
        return [["."] * width for _ in range(height)]

    def _load_grid(self, path: Path) -> list[list[str]]:
        if not path.exists():
            width, height = DEFAULT_LEVEL_SIZE
            return self._blank_grid(width, height)

        rows = decode_level_rows(path.read_text(encoding="utf-8").splitlines())
        if not rows:
            width, height = DEFAULT_LEVEL_SIZE
            return self._blank_grid(width, height)

        width = max(len(row) for row in rows)
        grid: list[list[str]] = []
        for row in rows:
            padded = row.ljust(width, ".")
            grid.append(list(padded))
        return grid

    def _grid_width(self) -> int:
        return max((len(row) for row in self.grid), default=0)

    def _grid_height(self) -> int:
        return len(self.grid)

    def _find_spawn_tile(self) -> tuple[int, int] | None:
        for row_index, row in enumerate(self.grid):
            for col_index, tile in enumerate(row):
                if tile == "P":
                    return col_index, row_index
        return None

    def _center_camera(self, col: int, row: int) -> None:
        viewport_width = WINDOW_SIZE[0]
        viewport_height = WINDOW_SIZE[1] - UI_HEIGHT
        max_x = max(0, self._grid_width() * TILE_SIZE - viewport_width)
        max_y = max(0, self._grid_height() * TILE_SIZE - viewport_height)

        self.camera_x = min(max((col * TILE_SIZE + TILE_SIZE / 2) - viewport_width / 2, 0.0), max_x)
        self.camera_y = min(max((row * TILE_SIZE + TILE_SIZE / 2) - viewport_height / 2, 0.0), max_y)

    def _center_camera_on_spawn(self) -> None:
        spawn = self._find_spawn_tile()
        if spawn is not None:
            self._center_camera(*spawn)

    def _normalize_grid(self) -> None:
        width = self._grid_width()
        for row in self.grid:
            if len(row) < width:
                row.extend(["."] * (width - len(row)))

    def _ensure_cell(self, col: int, row: int) -> None:
        width = self._grid_width()
        height = self._grid_height()

        if row >= height:
            for _ in range(row - height + 1):
                self.grid.append(["."] * max(width, DEFAULT_LEVEL_SIZE[0]))

        width = self._grid_width()
        if col >= width:
            extra = col - width + 1
            for grid_row in self.grid:
                grid_row.extend(["."] * extra)

    def _set_cell(self, col: int, row: int, tile: str) -> None:
        self._ensure_cell(col, row)

        if tile == "P":
            for grid_row in self.grid:
                for index, value in enumerate(grid_row):
                    if value == "P":
                        grid_row[index] = "."

        self.grid[row][col] = tile
        self.dirty = True

    def _erase_cell(self, col: int, row: int) -> None:
        self._ensure_cell(col, row)
        self.grid[row][col] = "."
        self.dirty = True

    def _save(self) -> None:
        self._normalize_grid()
        self.level_path.parent.mkdir(parents=True, exist_ok=True)
        rows = ["".join(row) for row in self.grid]
        self.level_path.write_text(
            "\n".join(encode_level_rows(rows)) + "\n",
            encoding="utf-8",
        )
        delete_generated_json(self.level_path)
        self.dirty = False

    def _screen_to_cell(self, position: tuple[int, int]) -> tuple[int, int] | None:
        x, y = position
        if y < UI_HEIGHT:
            return None
        col = int((x + self.camera_x) // TILE_SIZE)
        row = int((y - UI_HEIGHT + self.camera_y) // TILE_SIZE)
        if col < 0 or row < 0:
            return None
        return col, row

    def _paint_from_mouse(self) -> None:
        buttons = pygame.mouse.get_pressed(3)
        if not buttons[0] and not buttons[2]:
            return

        cell = self._screen_to_cell(pygame.mouse.get_pos())
        if cell is None:
            return

        col, row = cell
        if buttons[2]:
            self._erase_cell(col, row)
        else:
            self._set_cell(col, row, self.current_tile)

    def _handle_keydown(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_ESCAPE:
            return False
        if event.key in TILE_KEYS:
            self.current_tile = TILE_KEYS[event.key]
        elif event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
            self._save()
        elif event.key == pygame.K_g and event.mod & pygame.KMOD_CTRL:
            spawn = self._find_spawn_tile()
            if spawn is not None:
                self._center_camera(*spawn)
            else:
                self.camera_x = 0.0
                self.camera_y = 0.0
        return True

    def _draw_palette(self) -> None:
        self.screen.fill((18, 18, 28))

        title = self.font.render(
            f"Ferrum World Editor - {self.level_path}", True, (240, 240, 248)
        )
        self.screen.blit(title, (16, 10))

        status_text = "Unsaved changes" if self.dirty else "Saved"
        status = self.small_font.render(status_text, True, (190, 190, 205))
        self.screen.blit(status, (16, 34))

        palette_x = WINDOW_SIZE[0] - 330
        for index, tile in enumerate(TILE_ORDER):
            box = pygame.Rect(palette_x + index * 60, 14, 38, 38)
            pygame.draw.rect(self.screen, TILE_COLORS[tile], box)
            outline_color = (255, 255, 255) if tile == self.current_tile else (60, 60, 78)
            pygame.draw.rect(self.screen, outline_color, box, 2)

            label = self.small_font.render(tile if tile != "." else "E", True, (12, 12, 18))
            label_rect = label.get_rect(center=box.center)
            self.screen.blit(label, label_rect)

    def _draw_grid(self) -> None:
        grid_top = UI_HEIGHT
        view_width = WINDOW_SIZE[0]
        view_height = WINDOW_SIZE[1] - UI_HEIGHT

        start_col = max(0, int(self.camera_x // TILE_SIZE))
        start_row = max(0, int(self.camera_y // TILE_SIZE))
        end_col = min(
            self._grid_width(),
            int((self.camera_x + view_width) // TILE_SIZE) + 2,
        )
        end_row = min(
            self._grid_height(),
            int((self.camera_y + view_height) // TILE_SIZE) + 2,
        )

        for row_index in range(start_row, end_row):
            row = self.grid[row_index]
            screen_y = grid_top + row_index * TILE_SIZE - self.camera_y
            for col_index in range(start_col, end_col):
                tile = row[col_index]
                if tile == ".":
                    continue

                screen_x = col_index * TILE_SIZE - self.camera_x
                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, TILE_COLORS[tile], rect)

        for col_index in range(start_col, end_col):
            screen_x = col_index * TILE_SIZE - self.camera_x
            pygame.draw.line(
                self.screen,
                (42, 42, 58),
                (screen_x, grid_top),
                (screen_x, WINDOW_SIZE[1]),
                1,
            )

        for row_index in range(start_row, end_row):
            screen_y = grid_top + row_index * TILE_SIZE - self.camera_y
            pygame.draw.line(
                self.screen,
                (42, 42, 58),
                (0, screen_y),
                (WINDOW_SIZE[0], screen_y),
                1,
            )

        pygame.draw.rect(
            self.screen,
            (60, 60, 82),
            pygame.Rect(0, grid_top, view_width, view_height),
            1,
        )

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_keydown(event)
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                    self._paint_from_mouse()

            keys = pygame.key.get_pressed()
            pan = PAN_SPEED * dt * (2 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.camera_x = max(0.0, self.camera_x - pan)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.camera_x += pan
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.camera_y = max(0.0, self.camera_y - pan)
            if (
                keys[pygame.K_DOWN]
                or (keys[pygame.K_s] and not (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]))
            ):
                self.camera_y += pan

            self._draw_palette()
            self._draw_grid()
            pygame.display.flip()

        pygame.quit()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Edit Ferrum world WORLD files.")
    parser.add_argument(
        "path",
        nargs="?",
        default=LEVELS_DIR / "untitled.world",
        type=Path,
        help="Level file to edit or create.",
    )
    return parser


def run_editor(level_path: str | Path) -> None:
    WorldEditor(level_path).run()


def main() -> None:
    args = build_parser().parse_args()
    run_editor(args.path)


if __name__ == "__main__":
    main()