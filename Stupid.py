import pygame
import sys
from fight import FightScene
from charactor import SkillLibrary
from util import *
from pages import *

# 初始化pygame
pygame.init()

pygame.mixer.init()  # 初始化音频系统
# 载入背景音乐
# try:

#     pygame.mixer.muic.load("assets/music/illusion.mp3")  # 音乐文件路径
#     pygame.mixer.music.set_volume(0)  # 设置音量（0.0 到 1.0）
#     pygame.mixer.music.play(-1)  # -1 表示循环播放


# except pygame.error as e:
#     print(f"无法载入背景音乐: {e}")

class MainMenu:
    def __init__(self, font):
        self.font = font
        self.options = ["Start", "Help", "Quit"]
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

        opt_font = get_font("Cogmind",20)


        for i, option in enumerate(self.options):
            color=WHITE
            if i == self.selected:
                color = GREEN 
                pic = f"girl{i+1}"
                render_ascii_art(screen, label=pic, font_size=16, x=150, y=-70, color=WHITE)

            image = load_image(f"arts/sprite/{self.options[i]}.png",(32,32))
            render_1bit_sprite(screen, image, (190, 135 + i*50 - image.get_width()//2), color)
            icon = load_image(f"arts/stack.png",(64,64))
            screen.blit(icon,(25,25))

            text_surface = opt_font.render(option, True, color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, 140 + i*50))
            screen.blit(text_surface, text_rect)

            title_surface = load_image(f"arts/stackOverflow.png")
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
            screen.blit(title_surface, title_rect)
            
class GameApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.RESIZABLE)
        self.base_size = (SCREEN_WIDTH, SCREEN_HEIGHT)  # 你的设计分辨率
        self.virtual_surface = pygame.Surface(self.base_size)
        self.window_size = self.screen.get_size()

        # --- 新增：初始化缩放参数 ---
        self.scale = 1
        self.offset_x = 0
        self.offset_y = 0
        self.update_scale()

        pygame.display.set_caption("Stack Overflow")
        self.clock = pygame.time.Clock()

        self.font_en = get_font("Cogmind", 10)
        self.font_ch = get_font("Pixel", 10)

        self.menu = MainMenu(self.font_en)
        self.scene = FightScene()
        self.toolbar = Toolbar(self.scene.get_player_data)

        SkillLibrary.init_skills()
        self.state = MenuState(self)

        self.running = True
        is_fullscreen = False

    # --- 新增：更新缩放参数的方法 ---
    def update_scale(self):
        screen_w, screen_h = self.window_size
        base_w, base_h = self.base_size

        # 计算缩放比例 (//1 保持整数缩放，如果你想支持小数缩放，可以直接用 min)
        self.scale = max(1, min(screen_w / base_w, screen_h / base_h) // 1)
        
        
        new_w = int(base_w * self.scale)
        new_h = int(base_h * self.scale)

        self.offset_x = (screen_w - new_w) // 2
        self.offset_y = (screen_h - new_h) // 2

class GameState:
    def handle_event(self, event): pass
    def update(self): pass
    def draw(self): pass

class MenuState(GameState):
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        choice = self.app.menu.handle_event(event)
        if choice == "Start":
            self.app.state = IntroState(self.app)
        elif choice == "Quit":
            self.app.running = False

    def draw_to(self, surface):
        self.app.menu.draw(surface)

class IntroState(GameState):
    def __init__(self, app):
        self.app = app
        # 预载入图片和半透明遮罩
        self.welcome_img = load_image("arts/terminal of life.png")
        
        # 优化遮罩大小，使其与图片一致
        self.overlay = pygame.Surface(self.welcome_img.get_size()).convert_alpha()
        self.overlay.fill((0, 0, 0, 180))
        
        # 视觉小说文字配置
        self.intro_text = [
            "Welcome to Stack Overflow",
            "In the game, Programming language is your sword,",
            "and your brain is the shield.",
            "Here is a simple tutorial:",
            "A,D for move ,",
            "S to "
            " your turn.", 
            "W to turn around,",
            "X/Space to execute sequence",
            "Don't make your brain 'Stack Overflow'.",
        ]
        
        self.line_index = 1     # 初始显示第 1 行
        self.line_spacing = 25  # 行间距
        self.start_y = 50       # 起始 Y 坐标

    def handle_event(self, event):
        # 只有按下特定键（如回车/空格）或点击鼠标时才推进剧情
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
                self._advance_story()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._advance_story()

    def _advance_story(self):
        if self.line_index < len(self.intro_text):
            self.line_index += 1
        else:
            # 所有文字播放完毕，切入游戏试玩状态
            self.app.state = PlayingState(self.app)

    def update(self):
        # 如果以后想做文字逐字打印的动画（Typewriter Effect），可以在这里更新计时器
        pass

    def draw_to(self, surface):
        # 1. 清屏
        surface.fill(BLACK)
        
        # 2. 绘制居中的背景图与遮罩
        img_w, img_h = self.welcome_img.get_size()
        img_x = (self.app.base_size[0] - img_w) // 2
        img_y = 100
        
        surface.blit(self.welcome_img, (img_x, img_y))
        surface.blit(self.overlay, (img_x, img_y))
        
        # 3. 绘制底部提示语
        prompt_surf = self.app.font_en.render("Press ENTER / CLICK to continue...", True, GREEN)
        surface.blit(prompt_surf, (20, self.app.base_size[1] - 30))
        
        # 4. 逐行绘制当前已经解锁的文本
        for i in range(self.line_index):
            # 保留你原本的设计：第一行缩进 40，后续行缩进 50
            x_pos = 40 if i == 0 else 50
            y_pos = self.start_y + i * self.line_spacing
            
            text_surf = self.app.font_en.render(self.intro_text[i], True, WHITE)
            surface.blit(text_surf, (x_pos, y_pos))

class PlayingState(GameState):
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        scene = self.app.scene
        toolbar = self.app.toolbar

        toolbar.handle_event(event, scene.player)
        scene.handle_event(event)


    def update(self):
        self.app.toolbar.update(self.app.scene.player)
        self.app.scene.update()

        if self.app.scene.game_state == "game_over":
            self.app.state = GameOverState(self.app)

    def draw_to(self, surface):
        surface.fill(BLACK)

        self.app.scene.draw(surface)

        self.app.toolbar.draw(
            surface,
            self.app.font_ch,
            self.app.scene.get_player_data()
        )


        pygame.display.flip() 

class GameOverState(GameState):
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.app.scene = FightScene()
                self.app.state = MenuState(self.app)
            elif event.key == pygame.K_r:
                self.app.scene = FightScene()
                self.app.state = PlayingState(self.app)

    def draw_to(self, surface):
        self.app.scene.draw(surface)
        
def main():
    pygame.init()
    app = GameApp()

    while app.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.running = False
            elif event.type == pygame.VIDEORESIZE:
                app.window_size = (event.w, event.h)
                app.screen = pygame.display.set_mode(app.window_size, pygame.RESIZABLE)
                app.update_scale() # 窗口改变时重新计算缩放

            # --- 新增：鼠标事件坐标系转换核心逻辑 ---
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                mx, my = event.pos
                # 将物理窗口坐标逆运算为虚拟画布坐标
                vx = int((mx - app.offset_x) / app.scale)
                vy = int((my - app.offset_y) / app.scale)

                
                # 创建一个替换了 pos 的新事件往下传
                event_dict = event.dict.copy()
                event_dict['pos'] = (vx, vy)
                mapped_event = pygame.event.Event(event.type, **event_dict)
                
                app.state.handle_event(mapped_event)
                app.scene.mouse_pos = (vx, vy) #给scene映射后的位置
            # ----------------------------------------
            else:
                app.state.handle_event(event)

        app.state.update()

        # 1. 所有内容画到虚拟画布
        app.virtual_surface.fill((0,0,0))
        app.state.draw_to(app.virtual_surface)

        # 2. 等比缩放 + 黑边 (现在直接使用 app 中计算好的参数)
        new_w = int(app.base_size[0] * app.scale)
        new_h = int(app.base_size[1] * app.scale)
        scaled = pygame.transform.scale(app.virtual_surface, (new_w, new_h))

        app.screen.fill((0,0,0))
        app.screen.blit(scaled, (app.offset_x, app.offset_y))

        pygame.display.flip()
        app.clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()