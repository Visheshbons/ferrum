from convert_level import load_level_json
from engine import Game, Level, Player, World


def build_level(level) -> Level:
    grid = load_level_json(f"lv{level}")
    return Level.from_grid(grid, tile_size=32)


def main() -> None:
    game = Game()
    world = World(game.screen.get_size())

    level = build_level(2)
    spawn_x, spawn_y = world.load_level(level)
    player = Player(spawn_x, spawn_y)
    world.add_entity(player, is_player=True)

    game.run(world)


if __name__ == "__main__":
    main()
