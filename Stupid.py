import pygame
import sys
from fight import *
from help import HelpSystem
from colors import *
from pages import *

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
                    pass
                elif event.type == pygame.USEREVENT + 1:
                    if fight_scene.game_state == "enemy_turn":
                        fight_scene.execute_enemy_turn(fight_scene)
                        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
            # 工具栏事件
            toolbar.handle_event(event,fight_scene.player)

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