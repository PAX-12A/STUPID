import pygame
import sys
from font_manager import get_font
from fight import *
from help import HelpSystem
from colors import *
import json

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
    def __init__(self,get_player_data):
        from AbilityTree import TechTree
        # 创建标签页
        self.tabs = self.create_tabs(
            ["Character", "Ability", "Inventory", "Settings"],
            start_pos=(50, SCREEN_HEIGHT - TOOLBAR_HEIGHT + 10),
            direction="row"
        )
        self.active_tab_index = None  # 主界面默认
            
        # 创建科技树
        self.Ability_tree = TechTree(get_player_data)

        self.get_player_data = get_player_data

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
        # 绘制标签边框
        self.draw_tab_border(screen, icon_font, self.tabs)
        
        # 如果有激活的标签页
        if self.tabs and self.active_tab_index is not None:
            active_tab = self.tabs[self.active_tab_index]
            
            # 根据标签名调用对应的绘制方法
            draw_method = {
                "Ability": self.draw_ability_page,
                "Inventory": self.draw_inventory_page,
                "Character": self.draw_character_page,
                "Settings": self.draw_settings_page
            }.get(active_tab.name, None)

            if draw_method:
                draw_method(screen, icon_font, content_font, content_font_small,player=self.get_player_data())

    # ==== 以下是分离的页面绘制函数 ====

    def draw_ability_page(self, screen, icon_font, content_font, content_font_small,player):
        self.Ability_tree.draw(screen, icon_font, content_font_small,player)

    def draw_inventory_page(self, screen, icon_font, content_font, content_font_small,player=None):
        content_lines = [
            "这里是你的物品背包",
            "可以存放武器、装备和道具",
            "点击物品查看详细属性"
        ]
        for i, line in enumerate(content_lines):
            text_surface = content_font.render(line, True, WHITE)
            screen.blit(text_surface, (50, 100 + i * 25))

    def draw_character_page(self, screen, icon_font, content_font, content_font_small,player=None):
        self.draw_character(screen)

    def draw_settings_page(self, screen, icon_font, content_font, content_font_small,player=None):
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

    def draw_character(self,screen):
        character = load_image('assets/programmer.jpg',(366,366))
        screen.blit(character, (100, 100))
        Title_font=get_font("en","Cogmind",30)
        content_font=get_font("en","DOS",30)
        text_surface = Title_font.render("The harmful effect of programming", True, WHITE)
        screen.blit(text_surface, (50, 30))
        brain_pos=(300, 210)
        body_pos=(350, 300)
        TEXT_BEGIN_x= 550
        TEXT_BEGIN_y= 550

        pygame.draw.line(screen, GRAY, brain_pos, (TEXT_BEGIN_x, 100), 5)
        pygame.draw.line(screen, GRAY, body_pos, (TEXT_BEGIN_x, 300), 5)

        data = self.get_player_data()  # 调用回调拿到玩家数据
        stats_lines = [
            f"HP: {data['health']}/{data['max_health']}",
            f"Sequence Limit: {data['sequence_limit']}",
            f"DP: {data['damage_multiplier']}",
        ]
        
        start_x, start_y = 50, 500  # 起始位置
        line_height = content_font.get_height() + 5  # 行距

        for i, line in enumerate(stats_lines):
            text_surface = content_font.render(line, True, WHITE)
            screen.blit(text_surface, (start_x, start_y + i * line_height))

        self.draw_status(screen,Title_font,500,100,data['status'])

    def draw_status(self,screen, font, x, y, status_list):
        # 先按 body_part 分类
        categorized = {}
        for s in status_list:
            if s.is_illness:  # 只显示疾病类
                categorized.setdefault(s.body_part, []).append(s)

        current_y = y
        for body_part, illnesses in categorized.items():
            # 绘制部位标题
            part_text = font.render(f"{body_part.capitalize()}:", True, WHITE)
            screen.blit(part_text, (x, current_y))
            current_y += font.get_height() + 2

            # 绘制每个病
            for illness in illnesses:
                # 假设 illness 有 duration 属性
                name_line = f"{illness.name}({illness.duration})"
                illness_text = font.render(name_line, True, WHITE)
                screen.blit(illness_text, (x + 20, current_y))
                current_y += font.get_height() + 2

            # 每个部位之间空一行
            current_y += 5

class MainMenu:
    def __init__(self, font):
        self.font = font
        self.options = ["Start Game", "Help", "Quit"]
        self.selected = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selected]
        return None

    def draw(self, screen):
        screen.fill(BLACK)
        title_surface = self.font.render("Stupid Game", True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
        screen.blit(title_surface, title_rect)


        for i, option in enumerate(self.options):
            color=WHITE
            if i == self.selected:
                color = GREEN 
                pic = f"girl{i+1}"
                self.render_ascii_art(screen, label=pic, font_size=16, x=380, y=50, color=WHITE)
            text_surface = self.font.render(option, True, color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, 270 + i*50))
            screen.blit(text_surface, text_rect)

    def render_ascii_art(self, screen, label, font_size=16, x=10, y=20, color=WHITE):
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


    def intro(self,screen):
        screen.fill(BLACK)
        intro_text = [
        "Welcome to the glorious world of S.T.U.P.I.D.",
        "The game itself is developed by a stupid programmer,",
        "But the world is created by a non-stupid writer.",
        "Programming language is your sword",
        "and your brain is the shield.",
        "However,high IQ is not always a good thing.",
        "Please remember: Simplicity is All You Need.",
        ]
        self.draw_multiline_dialog(screen,intro_text,self.font)

    def draw_text(self,screen,text, x, y, font, color=WHITE):
        rendered = font.render(text, True, color)
        screen.blit(rendered, (x, y))

    # 像视觉小说一样显示文字
    def draw_multiline_dialog(self,screen, text_lines, font ,start_y=80, color=WHITE, line_spacing=40):
        
        self.draw_text(screen,"Press ENTER to continue...", 50, SCREEN_HEIGHT - 60,font,GREEN)

        line_index = 0
        self.draw_text(screen,text_lines[line_index], 50, start_y + line_index * line_spacing, font,color)
        line_index += 1
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    if line_index < len(text_lines):
                        self.draw_text(screen,text_lines[line_index], 50,start_y + line_index * line_spacing, font,color)
                        line_index += 1
                        pygame.display.flip()
                    else:
                        waiting = False

def main():
    # 设置屏幕
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Stupid Game")
    clock = pygame.time.Clock()

    en_Cogmind_20 = get_font("en", "Cogmind", 20)
    ch_Pixel_20 = get_font("ch", "Pixel", 20)
    ch_Pixel_16 = get_font("ch", "Pixel", 16)

    # 创建战斗场景
    fight_scene = FightScene()
    
    # 创建工具栏
    toolbar = Toolbar(fight_scene.get_player_data)

    skillLib = SkillLibrary
    skillLib.init_skills()

    help_system = HelpSystem()
    menu = MainMenu(en_Cogmind_20)
    game_state = GAME_STATE_MENU  # ✅ 初始状态是菜单
    running = True
    while running:
        # 1. 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_state == GAME_STATE_MENU:
                choice = menu.handle_event(event)
                if choice == "Start Game":
                    menu.intro(screen)
                    game_state = GAME_STATE_PLAYING
                elif choice == "Help":
                    help_system.is_visible = True
                elif choice == "Quit":
                    running = False
            elif game_state == GAME_STATE_PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if help_system.is_visible:
                        help_system.is_visible = False
                    else:
                        toolbar.close_all_tabs()
                elif event.type == pygame.USEREVENT + 1:
                    if fight_scene.game_state == "enemy_turn":
                        fight_scene.execute_enemy_turn(fight_scene)
                        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
            # 工具栏事件
            toolbar.handle_event(fight_scene.player, event)

            # 战斗事件（只有主界面才生效）
            if not toolbar.tabs or not any(tab.is_active for tab in toolbar.tabs):
                fight_scene.handle_event(event)
            # GameOver 
            if fight_scene.game_state == "game_over":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_state = "menu"   # 回主菜单
                        fight_scene = FightScene() 
                    elif event.key == pygame.K_r:
                        fight_scene = FightScene()  # 重新开始 

            

        if game_state == GAME_STATE_MENU:
            menu.draw(screen)
        elif game_state == GAME_STATE_PLAYING:
            toolbar.update(fight_scene.player)  # 这里处理科技树等进度
            screen.fill(BLACK)
            if not toolbar.tabs or not any(tab.is_active for tab in toolbar.tabs):
                fight_scene.draw(screen)
            toolbar.draw(screen, en_Cogmind_20, ch_Pixel_20, ch_Pixel_16)
            help_system.draw(screen, ch_Pixel_20)
                

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()