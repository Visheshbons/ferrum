from engine import Game, Level, Player, World


def build_level() -> Level:
    # Hear me out...
    # So "." is air
    # "#" is solid block
    # "P" is player spawn
    grid = [
        "#...............................#",
        "#...............................#",
        "#............###................#",
        "#............########...........#",
        "#......###......................#",
        "#...............................#",
        "#....................___........#",
        "#...............................#",
        "#...P...........................#",
        "#################################",
    ]
    return Level.from_grid(grid, tile_size=32)


def main() -> None:
    game = Game()
    world = World(game.screen.get_size())

    level = build_level()
    spawn_x, spawn_y = world.load_level(level)
    player = Player(spawn_x, spawn_y)
    world.add_entity(player, is_player=True)

    game.run(world)


if __name__ == "__main__":
    main()
