from __future__ import annotations

from pathlib import Path

import pygame

from convert_level import load_level_json
from engine import Game, Level, Player, World


LEVELS_DIR = Path(__file__).resolve().parent / "levels"


def build_level(level) -> Level:
    grid = load_level_json(f"lv{level}")
    return Level.from_grid(grid, tile_size=32)


def player_touching_finish(world: World) -> bool:
    return world.player_touching_finish()


def next_level_number(current_level: int) -> int | None:
    level_numbers = sorted(
        {
            int(path.stem[2:])
            for path in LEVELS_DIR.glob("lv*.txt")
            if path.stem[2:].isdigit()
        }
        | {
            int(path.stem[2:])
            for path in LEVELS_DIR.glob("lv*.json")
            if path.stem[2:].isdigit()
        }
    )
    if not level_numbers:
        return current_level + 1

    for level_number in level_numbers:
        if level_number > current_level:
            return level_number

    return None


def load_level_into_world(world: World, level_number: int) -> Player:
    level = build_level(level_number)
    spawn_x, spawn_y = world.load_level(level)
    player = Player(spawn_x, spawn_y)
    world.entities = []
    world.player = None
    world.add_entity(player, is_player=True)
    return player


def main() -> None:
    game = Game()
    world = World(game.screen.get_size())

    current_level = 2
    load_level_into_world(world, current_level)

    running = True
    while running:
        dt = game.clock.tick(game.fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        game.input_state.update(keys)

        world.update(dt, game.input_state)

        if player_touching_finish(world):
            if (
                game.input_state.left_pressed
                or game.input_state.right_pressed
                or game.input_state.jump_pressed
            ):
                world.reset_finish_wait()
            elif world.tick_finish_wait(dt):
                next_level = next_level_number(current_level)
                if next_level is not None:
                    current_level = next_level
                    load_level_into_world(world, current_level)
                else:
                    running = False
        else:
            world.reset_finish_wait()

        world.draw(game.screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
