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

class Page:
    def __init__(self, name):
        self.name = name
        self.is_active = False

    def handle_event(self, event, player):
        """处理用户输入"""
        return False

    def update(self, player):
        """更新页面逻辑"""
        pass

    def draw(self, screen, font, player):
        """绘制页面内容"""
        pass

class AbilityPage(Page):
    def __init__(self, get_player_data):
        super().__init__("Ability")
        from AbilityTree import TechTree
        self.tech_tree = TechTree(get_player_data)

    def handle_event(self, event, player):
        return self.tech_tree.handle_event(player, event)

    def update(self, player):
        self.tech_tree.update(player)

    def draw(self, screen, font, player):
        self.tech_tree.draw(screen, player)

class InventoryPage(Page):
    def __init__(self):
        super().__init__("Inventory")

    def draw(self, screen, font, player=None):
        lines = [
            "这里是你的物品背包",
            "可以存放武器、装备和道具",
            "点击物品查看详细属性"
        ]
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, WHITE)
            screen.blit(text_surface, (50, 100 + i * 25))

# === Character 页面 ===
class CharacterPage(Page):
    def __init__(self, get_player_data):
        super().__init__("Character")
        self.get_player_data = get_player_data

    def draw(self, screen, font, player=None):
        character = load_image('assets/programmer.jpg',(736/4,736/4))
        screen.blit(character, (100, 100))
        title_font = get_font("en","Cogmind",30)
        content_font = get_font("en","DOS",20)
        text_surface = title_font.render("The harmful effect of programming", True, WHITE)
        screen.blit(text_surface, (50, 30))

        data = self.get_player_data()
        stats_lines = [
            f"HP: {data['health']}/{data['max_health']}",
            f"Sequence Limit: {data['sequence_limit']}",
            f"DP: {data['damage_multiplier']}",
        ]
        start_x, start_y = 50, 500
        line_height = content_font.get_height() + 5

        for i, line in enumerate(stats_lines):
            text_surface = content_font.render(line, True, WHITE)
            screen.blit(text_surface, (start_x, start_y + i * line_height))

        for i, (key, val) in enumerate(data['base_stats'].items()):
            stat_surface = content_font.render(f"{key}: {val}", True, WHITE)
            screen.blit(stat_surface, (400, start_y + i * line_height))

        self.draw_status(screen,content_font,500,100,data['status'])

    def draw_status(self,screen, font, x, y, status_list):
        # 先按 body_part 分类
        categorized = {}
        for s in status_list:
            # if s.is_illness:  # 只显示疾病类
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
                name_line = f"{illness.name}({illness.stack},{illness.duration}t to reduce 1 layer)"
                illness_text = font.render(name_line, True, GREEN if illness.is_illness else WHITE)
                screen.blit(illness_text, (x + 20, current_y))
                current_y += font.get_height() + 2

            # 每个部位之间空一行
            current_y += 5

# === Settings 页面 ===
class SettingsPage(Page):
    def __init__(self):
        super().__init__("Settings")

    def draw(self, screen, font, player=None):
        content_lines = [
            "调整游戏设置和选项",
            "包括音效、画质和操作设置",
            "保存和加载游戏进度"
        ]
        for i, line in enumerate(content_lines):
            text_surface = font.render(line, True, WHITE)
            screen.blit(text_surface, (50, 100 + i * 25))

class Tab:
    def __init__(self, name, x, y):
        self.name = name
        self.rect = pygame.Rect(x, y, TAB_WIDTH, TAB_HEIGHT)
        self.is_active = False
        self.is_hovered = False
        
    def draw(self, screen, font,img=True):
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
        if img:
            render_1bit_sprite(screen, load_image(f"arts/sprite/{self.name}.png",(48,48)), (self.rect.x-3, self.rect.y-3), text_color)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False
    
class Toolbar:
    def __init__(self, get_player_data):
        self.tabs = []
        self.pages = {}
        self.active_page = None
        self.get_player_data = get_player_data

        # 注册页面
        self.register_page(AbilityPage(get_player_data))
        self.register_page(InventoryPage())
        self.register_page(CharacterPage(get_player_data))
        self.register_page(SettingsPage())

    def register_page(self, page):
        x, y = 50, SCREEN_HEIGHT - TOOLBAR_HEIGHT + 10
        tab_x = x + len(self.tabs) * (TAB_WIDTH + 10)
        tab_y = y
        tab = Tab(page.name, tab_x, tab_y)

        self.tabs.append(tab)
        self.pages[page.name] = page

    def handle_event(self, player, event):
        # Tab 点击切换
        for tab in self.tabs:
            if tab.handle_event(event):
                if tab.is_active:
                    tab.is_active = False
                    self.active_page = None
                else:
                    for t in self.tabs:
                        t.is_active = False
                    tab.is_active = True
                    self.active_page = self.pages[tab.name]
                return True

        # 事件交给当前页面
        if self.active_page:
            return self.active_page.handle_event(event, player)

    def update(self, player):
        if self.active_page:
            self.active_page.update(player)

    def draw(self, screen, font, player):
        self.draw_tabs(screen, self.tabs)
        if self.active_page:
            self.active_page.draw(screen, font, player)

    def draw_tabs(self, screen, tabs, img=True):
        icon_font = get_font("en","Cogmind",20)
        pygame.draw.line(screen, WHITE, (0, SCREEN_HEIGHT - TOOLBAR_HEIGHT),
                         (SCREEN_WIDTH, SCREEN_HEIGHT - TOOLBAR_HEIGHT), 3)
        for tab in tabs:
            tab.draw(screen, icon_font, img)

    def close_all_tabs(self):
        for tab in self.tabs:
            tab.is_active = False
        self.active_page = None

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
                raise ValueError("direction not valid")
            
            tab = Tab(name, tab_x, tab_y)
            tabs.append(tab)
        
        return tabs

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
        menu_font = get_font("en","Patriot",50)
        title_surface = menu_font.render("Simplicity is all YOU Need", True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
        screen.blit(title_surface, title_rect)


        for i, option in enumerate(self.options):
            color=WHITE
            if i == self.selected:
                color = GREEN 
                pic = f"girl{i+1}"
                render_ascii_art(screen, label=pic, font_size=16, x=380, y=50, color=WHITE)

            image = load_image(f"arts/sprite/{self.options[i]}.png")
            render_1bit_sprite(screen, image, (380, 270 + i*50 - image.get_width()//2), color)
            text_surface = self.font.render(option, True, color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, 270 + i*50))
            screen.blit(text_surface, text_rect)
            

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
            toolbar.draw(screen, ch_Pixel_20,fight_scene.get_player_data())
            help_system.draw(screen, ch_Pixel_20)
                

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()