import pygame as pg
import pymunk as pm
from config import *

class Peg(pg.sprite.Sprite):
    def __init__(self, space, x, y, surf):
        super().__init__()

        self.health = 2  # starting health
        self.max_health = self.health

        self.original_image = surf.copy()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))

        self.body = pm.Body(body_type=pm.Body.STATIC)
        self.body.position = x, y

        self.shape = pm.Circle(self.body, PEG_RADIUS)

        self.shape.elasticity = 0.8
        self.shape.friction = 0.5
        self.shape.collision_type = 2

        space.add(self.body, self.shape)

class Camera:
    def __init__(self, screen_width, screen_height):
        self.x = screen_width / 2
        self.y = screen_height / 2
        self.zoom = 0.55
        self.screen_width = screen_width
        self.screen_height = screen_height

    def apply(self, pos):
        x = (pos[0] - self.x) * self.zoom + self.screen_width / 2
        y = (pos[1] - self.y) * self.zoom + self.screen_height / 2
        return int(x), int(y)

    def get_pm_transform(self):
        return (pm.Transform.translation(self.screen_width / 2, self.screen_height / 2) @
                pm.Transform.scaling(self.zoom) @
                pm.Transform.translation(-self.x, -self.y))
    
class GameState:
    AIMING = "aiming"
    DIVING = "diving"
    DEAD = "dead"

# Set the initial state
current_state = GameState.AIMING