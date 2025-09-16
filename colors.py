# 颜色定义（1bit风格）
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (100, 220, 100)
GRAY = (100, 100, 100)
SHADOW = (50, 50, 50)
RED = (220, 20, 60)

BOARDSIZE=8

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
TOOLBAR_HEIGHT = 60

import pygame
import os

# def load_image(path, scale=None):
#     image = pygame.image.load(path)
#     if scale:
#         image = pygame.transform.scale(image, scale)
#     return image

# 全局集合，记录已经提示过的缺失图片
_missing_logged = set()

def load_image(path, scale=None):
    if not os.path.exists(path):
        if path not in _missing_logged:
            print(f"[警告] 找不到图片: {path}")
            _missing_logged.add(path)
        # 返回占位图，避免崩溃
        w, h = scale if scale else (64, 64)
        return pygame.Surface((w, h), pygame.SRCALPHA)

    try:
        image = pygame.image.load(path).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except Exception as e:
        if path not in _missing_logged:
            print(f"[错误] 无法加载图片 {path}: {e}")
            _missing_logged.add(path)
        w, h = scale if scale else (64, 64)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((255, 0, 0, 128))  # 半透明红色方块作为占位
        return surf
    
def render_1bit_sprite(screen, image, pos, color):
        """
        渲染 1bit 精灵图并染色
        image: pygame.Surface (白色前景 + 透明背景 PNG)
        color: (R,G,B)
        """
        base = image.convert_alpha()
        tinted = base.copy()
        # alpha 保持原图
        tinted.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(tinted, pos)

TAB_WIDTH = 220
TAB_HEIGHT = 40
GAME_STATE_MENU = "menu"
GAME_STATE_PLAYING = "playing"
