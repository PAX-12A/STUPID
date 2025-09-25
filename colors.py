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
import json
from font_manager import get_font

# 全局集合，记录已经提示过的缺失图片
_missing_logged = set()

def load_image(path, scale=None, fallback="arts/sprite/Character/enemy.png"):
    if not os.path.exists(path):
        if path not in _missing_logged:
            print(f"[警告] 找不到图片: {path}")
            _missing_logged.add(path)

        # 如果设置了 fallback 且 fallback 存在，就用它
        if fallback and os.path.exists(fallback):
            return load_image(fallback, scale, fallback=None)

        # 否则返回占位图
        w, h = scale if scale else (64, 64)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((128, 128, 128, 128))  # 半透明灰色占位
        return surf

    try:
        image = pygame.image.load(path).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except Exception as e:
        if path not in _missing_logged:
            print(f"[错误] 无法加载图片 {path}: {e}")
            _missing_logged.add(path)

        if fallback and os.path.exists(fallback):
            return load_image(fallback, scale, fallback=None)

        w, h = scale if scale else (64, 64)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((255, 0, 0, 128))  # 半透明红色方块占位
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

def render_ascii_art(screen, label, font_size=16, x=10, y=20, color=WHITE):
    # 加载 ASCII art 索引
    with open("ASCII.json", "r", encoding="utf-8") as f:
        arts = json.load(f)

    # 查找对应标签
    art_entry = next((a for a in arts if a["label"] == label), None)
    if not art_entry:
        print(f"[!] 未找到标签: {label}")
        return

    # 从文件加载 ASCII 内容
    with open(art_entry["file"], "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 渲染
    font = pygame.font.Font("Saitamaar-Regular.ttf", font_size)
    for i, line in enumerate(lines):
        text_surface = font.render(line.rstrip("\n"), False, color)  # False = 关闭抗锯齿
        screen.blit(text_surface, (x, y + i * font_size))

TAB_WIDTH = 220
TAB_HEIGHT = 40
GAME_STATE_MENU = "menu"
GAME_STATE_PLAYING = "playing"
