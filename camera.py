import pygame
from util import *
from grid import Vec2


class Camera:

    def __init__(self):
        # 
        self.map_pixel_width = GRID_WIDTH * CELL_WIDTH
        self.map_pixel_height = GRID_HEIGHT * CELL_HEIGHT

        # camera位置（世界坐标）
        self.x = 0
        self.y = 0


    def update(self, target):

        # 玩家世界坐标
        target_x = target.render_pos.x * CELL_WIDTH
        target_y = target.render_pos.y * CELL_HEIGHT

        # 目标camera位置（让玩家居中）
        self.x = target_x - SCREEN_WIDTH // 2
        self.y = target_y - SCREEN_HEIGHT // 2

        # 防止camera超出地图

        self.x = max(0, min(self.x, self.map_pixel_width - SCREEN_WIDTH ))
        self.y = max(0, min(self.y, self.map_pixel_height - SCREEN_HEIGHT + CELL_HEIGHT * 3))


    def apply(self, world_pos):

        world_x = world_pos.x * CELL_WIDTH
        world_y = world_pos.y * CELL_HEIGHT

        return world_x - self.x, world_y - self.y
