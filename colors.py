# 颜色定义（1bit风格）
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (100, 220, 100)
GRAY = (100, 100, 100)
SHADOW = (50, 50, 50)

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
TOOLBAR_HEIGHT = 60

import pygame

def load_image(path, scale=None):
    image = pygame.image.load(path)
    if scale:
        image = pygame.transform.scale(image, scale)
    return image
TAB_WIDTH = 200
TAB_HEIGHT = 40

