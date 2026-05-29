# The code is all hand-written, but comments FROM THIS POINT ON are mainly AI generated.

from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from convert_level import load_level_json
from engine import Game, Level, Player, World
from editor import run_editor


LEVELS_DIR = Path(__file__).resolve().parent / "levels"


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for game and editor launch modes."""
    parser = argparse.ArgumentParser(description="Ferrum")
    parser.add_argument(
        "--edit",
        nargs="?",
        const=LEVELS_DIR / "untitled.world",
        type=Path,
        help="Open the world editor instead of the game.",
    )
    return parser


def delete_level_json(level_number: int) -> None:
    """Remove the generated JSON file for a level after it has been cleared."""
    level_json_path = LEVELS_DIR / f"lv{level_number}.json"
    if level_json_path.exists():
        # Clean up the converted level so the next run starts from the source world file.
        level_json_path.unlink()


def build_level(level) -> Level:
    """Load a level and convert it into the in-memory Level representation."""
    grid = load_level_json(f"lv{level}")
    return Level.from_grid(grid, tile_size=32)


def player_touching_finish(world: World) -> bool:
    """Check whether the player is touching a finish tile."""
    return world.player_touching_finish()


def next_level_number(current_level: int) -> int | None:
    """Find the next available level number after the current one."""
    level_numbers = sorted(
        {
            int(path.stem[2:])
            for path in LEVELS_DIR.glob("lv*.world")
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
    """Replace the current world contents with the requested level and spawn."""
    level = build_level(level_number)
    spawn_x, spawn_y = world.load_level(level)
    player = Player(spawn_x, spawn_y)
    # Clear any previous state before inserting the new player entity.
    world.entities = []
    world.player = None
    world.add_entity(player, is_player=True)
    return player


def main() -> None:
    """Run the main game loop and advance through levels in sequence."""
    args = build_parser().parse_args()
    if args.edit is not None:
        run_editor(args.edit)
        return

    game = Game()
    world = World(game.screen.get_size())

    # Start on the first level and load its world state.
    current_level = 1
    load_level_into_world(world, current_level)

    running = True
    while running:
        # Convert the clock tick into seconds for simulation updates.
        dt = game.clock.tick(game.fps) / 1000.0

        # Process window events so the application can be closed cleanly.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Read the current keyboard state and store edge-triggered inputs.
        keys = pygame.key.get_pressed()
        game.input_state.update(keys)

        # Advance the world one frame.
        world.update(dt, game.input_state)

        # Progress immediately when the player touches the exit.
        if player_touching_finish(world):
            # Remove the completed level and advance if another one exists.
            delete_level_json(current_level)
            next_level = next_level_number(current_level)
            if next_level is not None:
                current_level = next_level
                load_level_into_world(world, current_level)
            else:
                # No further levels remain, so exit the game loop.
                running = False

        # Draw the current frame and present it to the display.
        world.draw(game.screen)
        pygame.display.flip()

    # Shut down pygame once the loop has ended.
    pygame.quit()


if __name__ == "__main__":
    main()
