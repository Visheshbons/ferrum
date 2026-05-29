# The code is all hand-written, but comments FROM THIS POINT ON are mainly AI generated.

from __future__ import annotations

import math
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import pygame

Color = Tuple[int, int, int]
# PLAYER_TEXTURE_PATH = Path(__file__).resolve().parent / "assets" / "sprites" / "7754-uno-reverse.png"


@dataclass
class InputState:
    """Snapshot the current keyboard state and edge-triggered button presses."""
    left: bool = False
    right: bool = False
    jump: bool = False
    jump_pressed: bool = False
    left_pressed: bool = False
    right_pressed: bool = False
    dash_pressed: bool = False
    dash: bool = False
    _jump_was_down: bool = False
    _left_was_down: bool = False
    _right_was_down: bool = False
    _dash_was_down: bool = False

    def update(self, keys: Sequence[bool]) -> None:
        """Update held and pressed flags from the pygame keyboard matrix."""
        left_down = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right_down = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump_down = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        dash_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Rising-edge detection lets the game react once per key press.
        self.left_pressed = left_down and not self._left_was_down
        self.right_pressed = right_down and not self._right_was_down
        self.jump_pressed = jump_down and not self._jump_was_down
        self.dash_pressed = dash_pressed and not self._dash_was_down

        self.left = left_down
        self.right = right_down
        self.jump = jump_down
        self.dash = dash_pressed

        self._left_was_down = left_down
        self._right_was_down = right_down
        self._jump_was_down = jump_down
        self._dash_was_down = dash_pressed


@dataclass
class Platform:
    """Represent a solid surface or a one-way platform in the level."""
    rect: pygame.Rect
    color: Color = (90, 90, 110)
    jump_through: bool = False

    def draw(self, surface: pygame.Surface, camera: "Camera") -> None:
        """Render the platform after translating it into camera space."""
        pygame.draw.rect(surface, self.color, camera.apply_rect(self.rect))


@dataclass
class VisualTile:
    """Represent a level tile that is visible but has no collision."""
    rect: pygame.Rect
    color: Color = (70, 70, 84)

    def draw(self, surface: pygame.Surface, camera: "Camera") -> None:
        """Render the decorative tile after translating it into camera space."""
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
        texture: str = "",
        texture_alignment: str = "center",
    ) -> None:
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(int(x), int(y), width, height)
        self.vel = pygame.Vector2(0, 0)
        self.color = color
        self.texture = texture
        self.texture_alignment = texture_alignment
        self.texture_surface: Optional[pygame.Surface] = None
        self.on_ground = 0 # Ternary btw

    def load_texture(self) -> Optional[pygame.Surface]:
        """Load and cache the entity texture if one is configured."""
        if not self.texture:
            return None
        if self.texture_surface is None:
            self.texture_surface = pygame.image.load(self.texture).convert_alpha()
        return self.texture_surface

    def get_texture_rect(self, texture_surface: pygame.Surface) -> pygame.Rect:
        """Position the texture relative to the entity according to alignment."""
        texture_rect = texture_surface.get_rect()
        texture_rect.centerx = self.rect.centerx
        if self.texture_alignment == "top":
            texture_rect.top = self.rect.top
        elif self.texture_alignment == "bottom":
            texture_rect.bottom = self.rect.bottom
        else:
            texture_rect.centery = self.rect.centery
        return texture_rect

    def update(self, dt: float, world: "World") -> None:
        """Apply gravity and resolve movement for the frame."""
        self.vel.y += world.gravity * dt
        self.move_and_collide(world.platforms, dt)

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Draw the entity using the camera offset."""
        texture_surface = self.load_texture()
        if texture_surface is not None:
            texture_rect = self.get_texture_rect(texture_surface)
            surface.blit(texture_surface, camera.apply_rect(texture_rect))
            return

        pygame.draw.rect(surface, self.color, camera.apply_rect(self.rect))

    def move_and_collide(self, platforms: Iterable[Platform], dt: float) -> None:
        """Move along each axis and stop when colliding with platforms."""
        self.on_ground = 0
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
                        self.on_ground = 1
                        self.pos.y = self.rect.y
                        self.vel.y = 0
                    else:
                        # Ignore collisions while rising or entering from the side.
                        continue
                else:
                    if self.vel.y > 0:
                        self.rect.bottom = platform.rect.top
                        self.on_ground = 1
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
        texture: str = "", # str(PLAYER_TEXTURE_PATH),
        texture_alignment: str = "bottom",
        double_jump: bool = True,
    ) -> None:
        super().__init__(x, y, width, height, color, texture, texture_alignment)
        self.accel = 2000  # Horizontal acceleration applied while a direction is held.
        self.max_speed = 240  # Clamp top speed so movement stays controllable.
        self.dash_speed = 3000  # Velocity used while dashing (px/s)
        self.dash_duration = 0.15  # Dash time (seconds)
        self.dash_timer = 0.0
        self.dash_active = False
        self.dash_direction = 1.0
        self.post_dash_grace = 0.1  # Delay
        self.dash_recover_timer = 0.0
        self.jump_speed = 650  # Vertical launch speed used when the player jumps.
        self.friction = 12  # Ground drag applied when no horizontal input is pressed.
        # Double-jump can be disabled when stuff like effects are active
        self.double_jump_enabled = double_jump
        self.max_jumps = 2 if self.double_jump_enabled else 1
        self.jumps_remaining = self.max_jumps

    def update(self, dt: float, world: "World") -> None:
        """Read player input, apply movement forces, and resolve collisions."""
        input_state = world.input_state
        # ignore while dahsing
        if not self.dash_active:
            if input_state.left:
                self.vel.x -= self.accel * dt
            if input_state.right:
                self.vel.x += self.accel * dt

        if not self.dash_active and not input_state.left and not input_state.right:
            self.vel.x -= self.vel.x * min(1.0, self.friction * dt)
            if abs(self.vel.x) < 1.0:
                self.vel.x = 0

        # Dash
        if input_state.dash_pressed and not self.dash_active:
            if input_state.left:
                dir_sign = -1.0
            elif input_state.right:
                dir_sign = 1.0
            else:
                dir_sign = math.copysign(1.0, self.vel.x) if self.vel.x != 0 else 1.0
            self.dash_active = True
            self.dash_timer = self.dash_duration
            self.dash_direction = dir_sign
            # Immediately set dash velocity
            self.vel.x = self.dash_direction * self.dash_speed

        # Maintain dash for its duration (ignore friction/accel while active)
        if self.dash_active:
            self.dash_timer -= dt
            if self.dash_timer > 0:
                self.vel.x = self.dash_direction * self.dash_speed
            else:
                # Dash ended: delay integration
                self.dash_active = False
                self.dash_recover_timer = self.post_dash_grace

        # Decrease delay timer
        if self.dash_recover_timer > 0:
            self.dash_recover_timer -= dt

        # Clamp horizontal speed only when not dashing and not in post-dash grace.
        if not self.dash_active and self.dash_recover_timer <= 0:
            if abs(self.vel.x) > self.max_speed:
                self.vel.x = math.copysign(self.max_speed, self.vel.x)

        # Jumping logic (supports double jump)
        if input_state.jump_pressed and self.jumps_remaining > 0:
            self.vel.y = -self.jump_speed
            self.jumps_remaining -= 1

        # Gravity is applied here so the player follows the same physics model as other entities.
        self.vel.y += world.gravity * dt
        self.move_and_collide(world.platforms, dt)

        # Reset available jumps when landing on the ground.
        if self.on_ground == 1:
            self.jumps_remaining = self.max_jumps


@dataclass
class Level:
    """Describe a parsed level, including geometry, spawn, and finish tiles."""
    size: Tuple[int, int]
    platforms: List[Platform]
    visual_tiles: List[VisualTile]
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
        visual_tiles: str = "X",            # Tiles that only render and do not collide
        spawn_tile: str = "P",              # Player spawn point, only one allowed
        finish_tile: str = "T",             # Level exit / next level / cutscene / anything rly
    ) -> "Level":
        """Convert an ASCII tile grid into geometry and spawn metadata."""
        platforms: List[Platform] = []
        decorative_tiles: List[VisualTile] = []
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
                elif ch in visual_tiles:
                    rect = pygame.Rect(
                        x * tile_size, y * tile_size, tile_size, tile_size
                    )
                    decorative_tiles.append(VisualTile(rect, color=(72, 72, 88)))
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
            visual_tiles=decorative_tiles,
            spawn=spawn,
            finish_tiles=finish_tiles,
            background=(18, 18, 28),
        )


class World:
    """Own the active level state, physics settings, camera, and runtime entities."""
    def __init__(self, viewport_size: Tuple[int, int], gravity: float = 2000) -> None:
        self.gravity = gravity
        self.platforms: List[Platform] = []
        self.visual_tiles: List[VisualTile] = []
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
        self.visual_tiles = list(level.visual_tiles)
        self.bounds = pygame.Rect(0, 0, level.size[0], level.size[1])
        self.finish_tiles = list(level.finish_tiles)
        self.finish_wait_time = 0.0
        self.background = level.background
        return level.spawn

    def player_touching_finish(self) -> bool:
        """Report whether the player overlaps any finish tile."""
        if not self.player or not self.finish_tiles:
            return False

        # # The exit only counts once the player has come to a complete stop.
        # stationary = self.player.vel.x == 0 and self.player.vel.y == 0
        # return stationary and any(
        return any(
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
        for visual_tile in self.visual_tiles:
            visual_tile.draw(surface, self.camera)
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
