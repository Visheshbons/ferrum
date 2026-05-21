from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import pygame

Color = Tuple[int, int, int]


@dataclass
class InputState:
    left: bool = False
    right: bool = False
    jump: bool = False
    jump_pressed: bool = False
    _jump_was_down: bool = False

    def update(self, keys: Sequence[bool]) -> None:
        self.left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        self.right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump_down = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        self.jump_pressed = jump_down and not self._jump_was_down
        self.jump = jump_down
        self._jump_was_down = jump_down


@dataclass
class Platform:
    rect: pygame.Rect
    color: Color = (90, 90, 110)
    jump_through: bool = False

    def draw(self, surface: pygame.Surface, camera: "Camera") -> None:
        pygame.draw.rect(surface, self.color, camera.apply_rect(self.rect))


class Camera:
    def __init__(self, width: int, height: int) -> None:
        self.viewport = pygame.Rect(0, 0, width, height)
        self.offset = pygame.Vector2(0, 0)

    def follow(self, target: pygame.Rect, bounds: Optional[pygame.Rect] = None) -> None:
        self.offset.x = target.centerx - self.viewport.width / 2
        self.offset.y = target.centery - self.viewport.height / 2

        if bounds:
            self.offset.x = max(
                bounds.left, min(self.offset.x, bounds.right - self.viewport.width)
            )
            self.offset.y = max(
                bounds.top, min(self.offset.y, bounds.bottom - self.viewport.height)
            )

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-self.offset.x, -self.offset.y)


class Entity:
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
        self.vel.y += world.gravity * dt
        self.move_and_collide(world.platforms, dt)

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        pygame.draw.rect(surface, self.color, camera.apply_rect(self.rect))

    def move_and_collide(self, platforms: Iterable[Platform], dt: float) -> None:
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

        # vertical movement with support for one-way (jump-through) platforms
        prev_bottom = self.rect.bottom
        self.pos.y += self.vel.y * dt
        self.rect.y = int(round(self.pos.y))
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # jump-through platforms only collide when falling from above
                if platform.jump_through:
                    if self.vel.y > 0 and prev_bottom <= platform.rect.top:
                        self.rect.bottom = platform.rect.top
                        self.on_ground = True
                        self.pos.y = self.rect.y
                        self.vel.y = 0
                    else:
                        # ignore collision when moving up or from the side
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
    def __init__(
        self,
        x: float,
        y: float,
        width: int = 28,
        height: int = 40,
        color: Color = (130, 190, 255),
    ) -> None:
        super().__init__(x, y, width, height, color)
        self.accel = 2000  # Not as fast as it seems dw
        self.max_speed = 240  # See?
        self.jump_speed = 650  # Good jump height tho
        self.friction = 12  # Still pretty slippy

    def update(self, dt: float, world: "World") -> None:
        input_state = world.input_state
        if input_state.left:
            self.vel.x -= self.accel * dt
        if input_state.right:
            self.vel.x += self.accel * dt

        if not input_state.left and not input_state.right:
            self.vel.x -= self.vel.x * min(1.0, self.friction * dt)

        if abs(self.vel.x) > self.max_speed:
            self.vel.x = math.copysign(self.max_speed, self.vel.x)

        if input_state.jump_pressed and self.on_ground:
            self.vel.y = -self.jump_speed
            self.on_ground = False

        self.vel.y += world.gravity * dt
        self.move_and_collide(world.platforms, dt)


@dataclass
class Level:
    size: Tuple[int, int]
    platforms: List[Platform]
    spawn: Tuple[int, int]
    background: Color = (18, 18, 28)

    @classmethod
    def from_grid(
        cls,
        grid: Sequence[str],
        tile_size: int = 32,
        solid_tiles: str = "#",             # Solid blocks, full collision
        jump_through_tiles: str = "_",      # Platforms you can jump through from below
        spawn_tile: str = "P",              # Player spawn point, only one allowed
    ) -> "Level":
        platforms: List[Platform] = []
        spawn = (0, 0)

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

        width = max(len(row) for row in grid) * tile_size if grid else 0
        height = len(grid) * tile_size
        return cls((width, height), platforms, spawn)


class World:
    def __init__(self, viewport_size: Tuple[int, int], gravity: float = 2000) -> None:
        self.gravity = gravity
        self.platforms: List[Platform] = []
        self.entities: List[Entity] = []
        self.player: Optional[Entity] = None
        self.camera = Camera(*viewport_size)
        self.bounds: Optional[pygame.Rect] = None
        self.input_state = InputState()
        self.background: Color = (18, 18, 28)

    def load_level(self, level: Level) -> Tuple[int, int]:
        self.platforms = list(level.platforms)
        self.bounds = pygame.Rect(0, 0, level.size[0], level.size[1])
        self.background = level.background
        return level.spawn

    def add_entity(self, entity: Entity, is_player: bool = False) -> None:
        self.entities.append(entity)
        if is_player:
            self.player = entity

    def update(self, dt: float, input_state: InputState) -> None:
        self.input_state = input_state
        for entity in self.entities:
            entity.update(dt, self)

        if self.player:
            self.camera.follow(self.player.rect, self.bounds)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self.background)
        for platform in self.platforms:
            platform.draw(surface, self.camera)
        for entity in self.entities:
            entity.draw(surface, self.camera)


class Game:
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
        running = True
        while running:
            dt = self.clock.tick(self.fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            self.input_state.update(keys)

            world.update(dt, self.input_state)
            world.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
