import pygame
import sys
from font_manager import get_font
from fight import *
from help import HelpSystem
from colors import *


# 初始化pygame
pygame.init()

pygame.mixer.init()  # 初始化音频系统
# 载入背景音乐
try:
    pygame.mixer.music.load("assets/music/illusion.mp3")  # 替换为你的音乐文件路径
    pygame.mixer.music.set_volume(0)  # 设置音量（0.0 到 1.0）
    pygame.mixer.music.play(-1)  # -1 表示循环播放
except pygame.error as e:
    print(f"无法载入背景音乐: {e}")


class Tab:
    def __init__(self, name, x, y):
        self.name = name
        self.rect = pygame.Rect(x, y, TAB_WIDTH, TAB_HEIGHT)
        self.is_active = False
        self.is_hovered = False
        
    def draw(self, screen, font):
        # 选择颜色
        if self.is_active:
            color = WHITE
            text_color = BLACK
        elif self.is_hovered:
            color = GRAY
            text_color = WHITE
        else:
            color = BLACK
            text_color = WHITE
            
        # 绘制标签背景（带边框效果）
        pygame.draw.rect(screen, SHADOW, (self.rect.x + 2, self.rect.y + 2, self.rect.width, self.rect.height))
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # 绘制文字
        text_surface = font.render(self.name, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class Toolbar:
    def __init__(self):
        from AbilityTree import TechTree
        # 创建标签页
        self.tabs = self.create_tabs(
            ["Character", "Ability", "Inventory", "Settings"],
            start_pos=(50, SCREEN_HEIGHT - TOOLBAR_HEIGHT + 10),
            direction="row"
        )
        self.active_tab_index = None  # 主界面默认
            
        # 创建科技树
        self.Ability_tree = TechTree()

    def create_tabs( self ,names, start_pos, direction="row", spacing=10):
        tabs = []
        x, y = start_pos
        
        for i, name in enumerate(names):
            if direction == "row":
                tab_x = x + i * (TAB_WIDTH + spacing)
                tab_y = y
            elif direction == "col":
                tab_x = x
                tab_y = y + i * (TAB_HEIGHT + spacing)
            else:
                raise ValueError("direction 应该为 'horizontal' 或 'vertical'")
            
            tab = Tab(name, tab_x, tab_y)
            tabs.append(tab)
        
        return tabs
    
    def draw_tab_border(self, screen,icon_font,tabs):# 绘制按钮
        # 绘制装饰性边框
        pygame.draw.line(screen, WHITE, (0, SCREEN_HEIGHT - TOOLBAR_HEIGHT), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - TOOLBAR_HEIGHT), 3)
        
        # 绘制所有标签
        for tab in tabs:
            tab.draw(screen, icon_font)
    
    def close_all_tabs(self):
        for tab in self.tabs:
            tab.is_active = False
        self.active_tab_index = None

    def update(self, player):
        """处理所有与游戏逻辑相关的更新"""
        if self.tabs and self.active_tab_index is not None:
            active_tab = self.tabs[self.active_tab_index]
            if active_tab.name == "Ability":
                self.Ability_tree.update(player)  # 研究进度逻辑
    
    def draw(self, screen, icon_font, content_font, content_font_small):
        
        self.draw_tab_border(screen,icon_font,self.tabs)
            
        # 显示当前标签的内容
        if self.tabs and self.active_tab_index is not None:
            active_tab = self.tabs[self.active_tab_index]

            if active_tab.name == "Ability":
                # 绘制科技树
                self.Ability_tree.draw(screen, icon_font, content_font_small)
                    
            elif active_tab.name == "Inventory":
                
                content_lines = [
                    "这里是你的物品背包",
                    "可以存放武器、装备和道具",
                    "点击物品查看详细属性"
                ]
                for i, line in enumerate(content_lines):
                    text_surface = content_font.render(line, True, WHITE)
                    screen.blit(text_surface, (50, 100 + i * 25))
                    
            elif active_tab.name == "Character":
                
                content_lines = [
                    "查看角色的属性和状态",
                    "包括等级、血量、法力值",
                    "以及力量、敏捷、智力等属性"
                ]
                for i, line in enumerate(content_lines):
                    text_surface = content_font.render(line, True, WHITE)
                    screen.blit(text_surface, (50, 100 + i * 25))
                    
            elif active_tab.name == "Settings":
                
                content_lines = [
                    "调整游戏设置和选项",
                    "包括音效、画质和操作设置",
                    "保存和加载游戏进度"
                ]
                for i, line in enumerate(content_lines):
                    text_surface = content_font.render(line, True, WHITE)
                    screen.blit(text_surface, (50, 100 + i * 25))

    def handle_hover_event(self, event):
        # 处理标签切换事件
        for i, tab in enumerate(self.tabs):
            if tab.handle_event(event):
                if tab.is_active:
                    # 如果点击的是当前激活的标签，则关闭所有标签
                    tab.is_active = False
                    self.active_tab_index = None
                else:
                    # 否则激活这个标签
                    for t in self.tabs:
                        t.is_active = False
                    tab.is_active = True
                    self.active_tab_index = i
                return True
    
    def handle_event(self, player,event):
        # 如果当前是科技页面，处理科技树事件
        if self.active_tab_index is not None:
            if self.tabs and self.tabs[self.active_tab_index].name == "Ability":
                if self.Ability_tree.handle_event(player,event):
                    return True
                
        self.handle_hover_event(event)


def main():
    # 设置屏幕
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("复古D&D风格工具栏")
    clock = pygame.time.Clock()

    en_Cogmind_20 = get_font("en", "Cogmind", 20)
    ch_Pixel_20 = get_font("ch", "Pixel", 20)
    ch_Pixel_16 = get_font("ch", "Pixel", 16)
    
    # 创建工具栏
    toolbar = Toolbar()

    # 创建战斗场景
    fight_scene = FightScene()

    help_system = HelpSystem()
    running = True
    while running:
        # 1. 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if help_system.is_visible:
                        help_system.is_visible = False
                    else:
                        toolbar.close_all_tabs()

                elif event.key == pygame.K_QUESTION or (
                    event.key == pygame.K_SLASH and pygame.key.get_mods() & pygame.KMOD_SHIFT
                ):
                    print("Help toggled")

            elif event.type == pygame.USEREVENT + 1:
                if fight_scene.game_state == "enemy_turn":
                    fight_scene.execute_enemy_turn()
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)

            # 工具栏事件
            toolbar.handle_event(fight_scene.player, event)

            # 战斗事件（只有主界面才生效）
            if not toolbar.tabs or not any(tab.is_active for tab in toolbar.tabs):
                fight_scene.handle_event(event)

        # 2. 更新逻辑
        if not toolbar.tabs or not any(tab.is_active for tab in toolbar.tabs):
            fight_scene.update()
        toolbar.update(fight_scene.player)  # 这里处理科技树等进度

        # 3. 绘制
        screen.fill(BLACK)
        if not toolbar.tabs or not any(tab.is_active for tab in toolbar.tabs):
            fight_scene.draw(screen, ch_Pixel_20)
        toolbar.draw(screen, en_Cogmind_20, ch_Pixel_20, ch_Pixel_16)
        help_system.draw(screen, ch_Pixel_20)

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()