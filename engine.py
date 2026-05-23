# The code is all hand-written, but comments FROM THIS POINT ON are mainly AI generated.

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import pygame

Color = Tuple[int, int, int]


@dataclass
class InputState:
    """Snapshot the current keyboard state and edge-triggered button presses."""
    left: bool = False
    right: bool = False
    jump: bool = False
    jump_pressed: bool = False
    left_pressed: bool = False
    right_pressed: bool = False
    _jump_was_down: bool = False
    _left_was_down: bool = False
    _right_was_down: bool = False

    def update(self, keys: Sequence[bool]) -> None:
        """Update held and pressed flags from the pygame keyboard matrix."""
        left_down = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right_down = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump_down = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

        # Rising-edge detection lets the game react once per key press.
        self.left_pressed = left_down and not self._left_was_down
        self.right_pressed = right_down and not self._right_was_down
        self.jump_pressed = jump_down and not self._jump_was_down

        self.left = left_down
        self.right = right_down
        self.jump = jump_down

        self._left_was_down = left_down
        self._right_was_down = right_down
        self._jump_was_down = jump_down


@dataclass
class Platform:
    """Represent a solid surface or a one-way platform in the level."""
    rect: pygame.Rect
    color: Color = (90, 90, 110)
    jump_through: bool = False

    def draw(self, surface: pygame.Surface, camera: "Camera") -> None:
        """Render the platform after translating it into camera space."""
        pygame.draw.rect(surface, self.color, camera.apply_rect(self.rect))


class Camera:
    """Track a viewport-sized offset that follows the player around the level."""
    def __init__(self, width: int, height: int) -> None:
        self.viewport = pygame.Rect(0, 0, width, height)
        self.offset = pygame.Vector2(0, 0)

    def follow(self, target: pygame.Rect, bounds: Optional[pygame.Rect] = None) -> None:
        """Center the camera on a target and clamp it to the level bounds."""
        self.offset.x = target.centerx - self.viewport.width / 2
        self.offset.y = target.centery - self.viewport.height / 2

        if bounds:
            # Prevent the camera from showing space outside the playable area.
            self.offset.x = max(
                bounds.left, min(self.offset.x, bounds.right - self.viewport.width)
            )
            self.offset.y = max(
                bounds.top, min(self.offset.y, bounds.bottom - self.viewport.height)
            )

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Translate a world-space rectangle into screen-space coordinates."""
        return rect.move(-self.offset.x, -self.offset.y)


class Entity:
    """Base movable object with position, velocity, and collision handling."""
    def __init__(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        color: Color = (220, 220, 240),
    ) -> None:
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(int(x), int(y), width, height)
        self.vel = pygame.Vector2(0, 0)
        self.color = color
        self.on_ground = False

    def update(self, dt: float, world: "World") -> None:
        """Apply gravity and resolve movement for the frame."""
        self.vel.y += world.gravity * dt
        self.move_and_collide(world.platforms, dt)

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Draw the entity using the camera offset."""
        pygame.draw.rect(surface, self.color, camera.apply_rect(self.rect))

    def move_and_collide(self, platforms: Iterable[Platform], dt: float) -> None:
        """Move along each axis and stop when colliding with platforms."""
        self.on_ground = False
        self.pos.x += self.vel.x * dt
        self.rect.x = int(round(self.pos.x))
        for platform in platforms:
            # skip horizontal collisions for one-way (jump-through) platforms
            if getattr(platform, "jump_through", False):
                continue
            if self.rect.colliderect(platform.rect):
                if self.vel.x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel.x < 0:
                    self.rect.left = platform.rect.right
                self.pos.x = self.rect.x
                self.vel.x = 0

        # Handle vertical movement separately so floor, ceiling, and one-way logic can diverge.
        prev_bottom = self.rect.bottom
        self.pos.y += self.vel.y * dt
        self.rect.y = int(round(self.pos.y))
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # One-way platforms only stop the entity when it lands on them from above.
                if platform.jump_through:
                    if self.vel.y > 0 and prev_bottom <= platform.rect.top:
                        self.rect.bottom = platform.rect.top
                        self.on_ground = True
                        self.pos.y = self.rect.y
                        self.vel.y = 0
                    else:
                        # Ignore collisions while rising or entering from the side.
                        continue
                else:
                    if self.vel.y > 0:
                        self.rect.bottom = platform.rect.top
                        self.on_ground = True
                    elif self.vel.y < 0:
                        self.rect.top = platform.rect.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0


class Player(Entity):
    """Specialize Entity with player controls, acceleration, and jump behavior."""
    def __init__(
        self,
        x: float,
        y: float,
        width: int = 28,
        height: int = 40,
        color: Color = (130, 190, 255),
    ) -> None:
        super().__init__(x, y, width, height, color)
        self.accel = 2000  # Horizontal acceleration applied while a direction is held.
        self.max_speed = 240  # Clamp top speed so movement stays controllable.
        self.jump_speed = 650  # Vertical launch speed used when the player jumps.
        self.friction = 12  # Ground drag applied when no horizontal input is pressed.

    def update(self, dt: float, world: "World") -> None:
        """Read player input, apply movement forces, and resolve collisions."""
        input_state = world.input_state
        if input_state.left:
            self.vel.x -= self.accel * dt
        if input_state.right:
            self.vel.x += self.accel * dt

        if not input_state.left and not input_state.right:
            self.vel.x -= self.vel.x * min(1.0, self.friction * dt)
            if abs(self.vel.x) < 1.0:
                self.vel.x = 0

        if abs(self.vel.x) > self.max_speed:
            self.vel.x = math.copysign(self.max_speed, self.vel.x)

        # Only jump when the press is new and the player is on the ground.
        if input_state.jump_pressed and self.on_ground:
            self.vel.y = -self.jump_speed
            self.on_ground = False

        # Gravity is applied here so the player follows the same physics model as other entities.
        self.vel.y += world.gravity * dt
        self.move_and_collide(world.platforms, dt)


@dataclass
class Level:
    """Describe a parsed level, including geometry, spawn, and finish tiles."""
    size: Tuple[int, int]
    platforms: List[Platform]
    spawn: Tuple[int, int]
    finish_tiles: List[pygame.Rect]
    background: Color = (18, 18, 28)

    @classmethod
    def from_grid(
        cls,
        grid: Sequence[str],
        tile_size: int = 32,
        solid_tiles: str = "#",             # Solid blocks, full collision
        jump_through_tiles: str = "_",      # Platforms you can jump through from below
        spawn_tile: str = "P",              # Player spawn point, only one allowed
        finish_tile: str = "T",             # Level exit / next level / cutscene / anything rly
    ) -> "Level":
        """Convert an ASCII tile grid into geometry and spawn metadata."""
        platforms: List[Platform] = []
        spawn = (0, 0)
        finish_tiles: List[pygame.Rect] = []

        # Walk the map row by row and interpret each symbol.
        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                if ch in solid_tiles:
                    rect = pygame.Rect(
                        x * tile_size, y * tile_size, tile_size, tile_size
                    )
                    platforms.append(Platform(rect))
                elif ch in jump_through_tiles:
                    rect = pygame.Rect(
                        x * tile_size, y * tile_size, tile_size, tile_size
                    )
                    platforms.append(
                        Platform(rect, color=(120, 120, 170), jump_through=True)
                    )
                elif ch == spawn_tile:
                    spawn = (x * tile_size, y * tile_size)
                elif ch == finish_tile:
                    finish_tiles.append(
                        pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                    )

        # Derive level dimensions from the WORLDual grid.
        width = max(len(row) for row in grid) * tile_size if grid else 0
        height = len(grid) * tile_size
        return cls(
            size=(width, height),
            platforms=platforms,
            spawn=spawn,
            finish_tiles=finish_tiles,
            background=(18, 18, 28),
        )


class World:
    """Own the active level state, physics settings, camera, and runtime entities."""
    def __init__(self, viewport_size: Tuple[int, int], gravity: float = 2000) -> None:
        self.gravity = gravity
        self.platforms: List[Platform] = []
        self.entities: List[Entity] = []
        self.player: Optional[Entity] = None
        self.finish_tiles: List[pygame.Rect] = []
        # self.finish_wait_duration = 0.15                   # six seven
        self.finish_wait_time = 0.0
        self.camera = Camera(*viewport_size)
        self.bounds: Optional[pygame.Rect] = None
        self.input_state = InputState()
        self.background: Color = (18, 18, 28)

    def load_level(self, level: Level) -> Tuple[int, int]:
        """Replace the current level data and return the level's player spawn point."""
        self.platforms = list(level.platforms)
        self.bounds = pygame.Rect(0, 0, level.size[0], level.size[1])
        self.finish_tiles = list(level.finish_tiles)
        self.finish_wait_time = 0.0
        self.background = level.background
        return level.spawn

    def player_touching_finish(self) -> bool:
        """Report whether a motionless player overlaps any finish tile."""
        if not self.player or not self.finish_tiles:
            return False

        # The exit only counts once the player has come to a complete stop.
        stationary = self.player.vel.x == 0 and self.player.vel.y == 0
        return stationary and any(
            self.player.rect.colliderect(finish_tile)
            for finish_tile in self.finish_tiles
        )

    # def has_finish_wait_elapsed(self) -> bool:
    #     return self.finish_wait_time >= self.finish_wait_duration

    def tick_finish_wait(self, dt: float) -> bool:
        """Advance the finish timer; the current implementation always allows progression."""
        # self.finish_wait_time = min(
        #     self.finish_wait_duration, self.finish_wait_time + dt
        # )
        # return self.has_finish_wait_elapsed()
        return True

    def reset_finish_wait(self) -> None:
        """Clear any pending finish timer state."""
        self.finish_wait_time = 0.0

    def add_entity(self, entity: Entity, is_player: bool = False) -> None:
        """Register an entity in the world and optionally mark it as the player."""
        self.entities.append(entity)
        if is_player:
            self.player = entity

    def update(self, dt: float, input_state: InputState) -> None:
        """Advance every entity and keep the camera locked to the player."""
        self.input_state = input_state
        for entity in self.entities:
            entity.update(dt, self)

        if self.player:
            self.camera.follow(self.player.rect, self.bounds)

    def draw(self, surface: pygame.Surface) -> None:
        """Paint the world background, platforms, and entities to the screen."""
        surface.fill(self.background)
        for platform in self.platforms:
            platform.draw(surface, self.camera)
        for entity in self.entities:
            entity.draw(surface, self.camera)


class Game:
    """Wrap pygame setup, the display surface, and the frame timer."""
    def __init__(
        self,
        width: int = 960,
        height: int = 540,
        title: str = "Ferrum",
        fps: int = 60,
    ) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.input_state = InputState()

    def run(self, world: World) -> None:
        """Run a self-contained game loop against the provided world."""
        running = True
        while running:
            # Convert the frame step to seconds for simulation code.
            dt = self.clock.tick(self.fps) / 1000.0
            # Allow the window to be closed while the loop is active.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Sample keyboard input once per frame.
            keys = pygame.key.get_pressed()
            self.input_state.update(keys)

            # Update simulation, then draw the resulting frame.
            world.update(dt, self.input_state)
            world.draw(self.screen)
            pygame.display.flip()

        # Tear down pygame cleanly after exiting the loop.
        pygame.quit()
