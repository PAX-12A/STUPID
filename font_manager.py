# font_manager.py

import pygame

_font_cache = {}

def get_font(lang: str, name: str, size: int = 16):
    key = (lang, name, size)
    if key not in _font_cache:
        if lang == "ch":
            if name == "Lolita":
                font_path = "assets/fonts/Lolita.ttf"
            elif name == "Pixel":
                font_path = "assets/fonts/Pixel.ttf"
            # ... add more styles if needed
        elif lang == "en":
            if name == "DOS":
                font_path = "assets/fonts/DOS.ttf"
            elif name == "Cogmind":
                font_path = "assets/fonts/Cogmind.ttf"
            elif name == "Time":
                font_path = "assets/fonts/Time.ttf"
            elif name == "Patriot":
                font_path = "assets/fonts/Patriot.ttf"
            # ... add more styles
        else:
            raise ValueError("Unsupported language or name")

        _font_cache[key] = pygame.font.Font(font_path, size)

    return _font_cache[key]
