import pygame
import random
from font_manager import get_font
from colors import *
from Charactor import *

class FightScene:
    def __init__(self):
        # 游戏状态
        self.grid_size = BOARDSIZE + 1
        self.cell_width = 100
        self.cell_height = 80
        self.grid_start_x = (SCREEN_WIDTH - self.grid_size * self.cell_width) // 2
        self.grid_start_y = 300
        
        # 玩家和敌人
        self.player = Player(2)  # 开始在中间位置
        self.enemies = [Enemy(4)]  # 敌人在最右边
        
        # 游戏状态
        self.game_state = "player_turn"  # player_turn, enemy_turn, game_over
        self.turn_count = 0
        self.message = ""
        self.message_timer = 0
        
        # 字体
        self.font = get_font("en","Cogmind",20)
        self.small_font = get_font("en","DOS",20)
        self.large_font = get_font("ch","Lolita",16)
        
        # 初始化敌人攻击意图
        self.setup_enemy_intents()
        self.player.on_move_check = self.handle_move#回调函数绑定

    def get_player_data(self):
        return {
            "health": self.player.health,
            "max_health": self.player.max_health,
            "sequence_limit":self.player.sequence_limit,
            "damage_multiplier":self.player.damage_multiplier,
            "status":self.player.status
        }
    
    def setup_enemy_intents(self):
        for enemy in self.enemies:
            # 随机选择攻击目标（通常是玩家周围的位置）
            target_positions = [random.randint(0, BOARDSIZE) for _ in range(random.randint(1, 2))]
            enemy.show_attack_intent(target_positions)
    
    def show_message(self, text, duration=120):
        self.message = text
        self.message_timer = duration
    
    def get_cell_rect(self, position):
        x = self.grid_start_x + position * self.cell_width
        y = self.grid_start_y
        return pygame.Rect(x, y, self.cell_width, self.cell_height)
    
    def get_cell_center(self, position):
        rect = self.get_cell_rect(position)
        return rect.centerx, rect.centery
    
    def get_enemy_at(self, pos):
        return next((enemy for enemy in self.enemies if enemy.position == pos), None)

    
    def handle_move(self,player, new_pos):
        enemy = self.get_enemy_at(new_pos)
        if enemy:# 与敌人交换位置       
            enemy.position, player.position = player.position, enemy.position
            return player.position  # 玩家保持原位置（朝向不变）
        elif player.can_move_to(new_pos):
            return new_pos
        else:
            return None
    
    def handle_event(self,event):
        if self.game_state != "player_turn":
            return
        
        if event.type == pygame.KEYDOWN:
            # === 移动：A / ←（左），D / →（右） ===
            if event.key in [pygame.K_a, pygame.K_LEFT]:
                if self.player.move(-1):
                    self.end_player_turn()
            elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                if self.player.move(1):
                    self.end_player_turn()
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                index = event.key - pygame.K_1
                success, msg = self.player.try_add_weapon_to_sequence(index,self)
                self.show_message(msg) #666
            elif event.key == pygame.K_SPACE:
                if self.player.action_sequence:
                    self.execute_player_actions()
                    self.end_player_turn()
                else:
                    self.show_message("序列为空!")

    
    def execute_player_actions(self):
        executed_actions = self.player.execute_sequence()

        if self.player.battle_style == "stack":# stack风格反转序列
            executed_actions.reverse()
        print(f"执行的动作序列: {executed_actions}")

        for action_type, weapon_index, weapon in executed_actions:
            # if action_type != 'weapon':
            multiplier = self.player.damage_multiplier
            actual_damage = int(weapon.damage * multiplier)
            print(f"actual_damage:{actual_damage}")

            # --- 类型1: melee / ranged（固定 pattern 攻击） ---
            if weapon.weapon_type in ["melee", "meleeMove","ranged"]:
                if weapon.weapon_type == "meleeMove":
                    self.player.move(1)
                attack_positions = self.get_adjusted_attack_positions(weapon)
                
                hit = False
                for enemy in self.enemies[:]:
                    if enemy.position in attack_positions:
                        enemy.take_damage(actual_damage)
                        hit = True
                        self.show_message(f"{weapon.name} Hit! (-{actual_damage})")
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            self.show_message("Ememy Is Defeated!")

            # --- 类型2: targeted（攻击最近敌人） ---
            elif weapon.weapon_type == "targeted":
                closest_enemy = min(self.enemies, key=lambda e: abs(e.position - self.player.position), default=None)
                if closest_enemy and abs(closest_enemy.position - self.player.position) in weapon.range_pattern:
                    closest_enemy.take_damage(actual_damage)
                    self.show_message(f"{weapon.name} 命中最近敌人! (-{actual_damage})")
                    if closest_enemy.health <= 0:
                        self.enemies.remove(closest_enemy)
                        self.show_message("敌人被击败!")
                else:
                    self.show_message(f"{weapon.name} 没有敌人射程内")

            # --- 类型3: fireball（攻击最近敌人±1格） ---
            elif weapon.weapon_type == "fireball":
                closest_enemy = min(self.enemies, key=lambda e: abs(e.position - self.player.position), default=None)
                if closest_enemy and abs(closest_enemy.position - self.player.position) in weapon.range_pattern:
                    aoe_positions = [closest_enemy.position - 1, closest_enemy.position, closest_enemy.position + 1]
                    aoe_positions = [pos for pos in aoe_positions if 0 <= pos < self.grid_size]

                    hit = False
                    for enemy in self.enemies[:]:
                        if enemy.position in aoe_positions:
                            enemy.take_damage(weapon.damage)
                            hit = True
                            self.show_message(f"{weapon.name} AOE命中敌人! (-{weapon.damage})")
                            if enemy.health <= 0:
                                self.enemies.remove(enemy)
                                self.show_message("敌人被击败!")
                    if not hit:
                        self.show_message(f"{weapon.name} 没有命中任何敌人")
                else:
                    self.show_message(f"{weapon.name} 射程内没有敌人")

    def get_adjusted_attack_positions(self, weapon):
        adjusted_positions = []
        for offset in weapon.range_pattern:
            actual_offset = offset * self.player.direction  # 左右翻转
            target_pos = self.player.position + actual_offset
            if 0 <= target_pos < self.grid_size:
                adjusted_positions.append(target_pos)
        print(f"方向: {self.player.direction}, 攻击格子: {adjusted_positions}")
        return adjusted_positions
    
    def get_occupied_positions(self):
        return {enemy.position for enemy in self.enemies}

    def spawn_enemy(self):
        # 获取所有未被占据的位置
        occupied_positions = {enemy.position for enemy in self.enemies}
        occupied_positions.add(self.player.position)

        possible_positions = [i for i in range(self.grid_size) if i not in occupied_positions]
        if not possible_positions:
            return  # 没有空位就不刷怪

        new_pos = random.choice(possible_positions)
        new_enemy = Enemy(new_pos)
        self.enemies.append(new_enemy)
        new_enemy.show_attack_intent([random.randint(0, BOARDSIZE)])
        self.show_message("Enemy Arrived!")

    
    def end_player_turn(self):
        if not self.enemies:
            self.game_state = "game_over"
            self.show_message("胜利!", 300)
            return
        
        self.player.update_cooldowns()
        self.game_state = "enemy_turn"
        self.turn_count += 1
        
        # 每10回合刷1个敌人
        if self.turn_count % 10 == 0:
            self.spawn_enemy()
        
        # 执行敌人回合
        pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # 1秒后执行敌人回合
    
    def execute_enemy_turn(self):
        for enemy in self.enemies:
            attack_pos = enemy.execute_attack()
            print(attack_pos)
            if attack_pos and self.player.position in attack_pos:
                self.player.take_damage(6)
                # 添加一个永久脑损伤（疾病类状态）
                self.player.add_status(Status("Simplified", "brain", is_illness=True))
                self.player.add_status(Status("PC addict", "brain", is_illness=True))
                self.player.add_status(Status("Diabetes", "wholebody", is_illness=True))
                self.player.add_status(Status("Sad", "brain", is_illness=False))
                self.show_message("You Are Under Atack! (-6)")
                if self.player.health <= 0:
                    self.game_state = "game_over"
                    self.show_message("游戏结束!", 300)
                    return
        
        # 设置新的攻击意图
        self.setup_enemy_intents()
        self.game_state = "player_turn"
    
    def draw_grid(self,screen):
        for i in range(self.grid_size):
            rect = self.get_cell_rect(i)
            
            # 绘制网格背景
            color = BLACK
            # if i == self.player.position:
            #     color = GRAY  # 玩家位置
            
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRAY, rect, 2)
            
            # 绘制位置编号
            pos_text = self.small_font.render(str(i), True, GRAY)
            text_rect = pos_text.get_rect(topleft=(rect.x + 5, rect.y + 5))
            screen.blit(pos_text, text_rect)
    
    def draw_attack_intents(self,screen):
        for enemy in self.enemies:
            if enemy.attack_intent and enemy.intent_timer > 0:
                for pos in enemy.attack_intent:
                    if 0 <= pos < self.grid_size:
                        rect = self.get_cell_rect(pos)
                        # 绘制攻击意图（红色警告）
                        overlay = pygame.Surface((rect.width, rect.height))
                        overlay.set_alpha(100)
                        overlay.fill(RED)
                        screen.blit(overlay, rect)
                        
                        # 绘制警告文字
                        warning_text = self.small_font.render("!", True, RED)
                        text_rect = warning_text.get_rect(center=rect.center)
                        screen.blit(warning_text, text_rect)
    
    def draw_entities(self,screen):
        self.draw_character_with_arrow(screen, "Hero",self.player.position, self.player.direction)
        
        # 绘制敌人
        for enemy in self.enemies:
            enemy_center = self.get_cell_center(enemy.position)
            self.draw_character_with_arrow(screen, "Enemy1",enemy.position, enemy.direction)
            
            # 绘制敌人血量
            health_ratio = enemy.health / enemy.max_health
            health_width = 40
            health_x = enemy_center[0] - health_width // 2
            health_y = enemy_center[1] - 35
            
            pygame.draw.rect(screen, RED, (health_x, health_y, health_width, 6))
            pygame.draw.rect(screen, GREEN, (health_x, health_y, int(health_width * health_ratio), 6))

    def draw_character_with_arrow(self, screen, name , position, direction):
        arrow_font = get_font("ch","Lolita")
        # 加载图片
        if name=="Hero":
            character = load_image('assets/hero.png')
        elif name == "Enemy1":
            character = load_image('assets/Enemy1.png')
            
        # 根据方向翻转
        if direction == 1:  # 朝右
            draw_img = character
            arrow_surface = arrow_font.render("→", True, GRAY)
        else:  # 朝左
            draw_img = pygame.transform.flip(character, True, False)
            arrow_surface = arrow_font.render("←", True, GRAY)

        # 获取格子矩形 & 中心
        rect = self.get_cell_rect(position)
        center_x, center_y = rect.center

        # 角色图片居中
        draw_x = center_x - draw_img.get_width() // 2
        draw_y = center_y - draw_img.get_height() // 2
        screen.blit(draw_img, (draw_x, draw_y))

        # 箭头居中（覆盖在图片正上方）
        arrow_x = center_x - arrow_surface.get_width() // 2
        arrow_y = draw_y - arrow_surface.get_height() + 5  
        screen.blit(arrow_surface, (arrow_x, arrow_y))

    def draw_ui(self,screen):
        # 绘制玩家血量,假设最大血量是 10 格
        max_bar_length = 10  
        filled = int(self.player.health / self.player.max_health * max_bar_length)
        bar_str = "#" * filled + "." * (max_bar_length - filled)
        health_text = self.small_font.render(f"HP: {bar_str}({self.player.health}/{self.player.max_health})", True, WHITE)
        screen.blit(health_text, (30, SCREEN_HEIGHT-80))
        
        # 绘制回合数
        turn_text = self.font.render(f"Turn: {self.turn_count}", True, WHITE)
        screen.blit(turn_text, (SCREEN_WIDTH- 100, 20))
        
        # 绘制武器状态
        weapon_y = 10
        for i, weapon in enumerate(self.player.weapons):
            color = GREEN if weapon.is_ready() else RED
            cooldown_text = f"Cooldown: {weapon.current_cooldown}" if not weapon.is_ready() else "Ready"
            
            weapon_text = self.small_font.render(f"{i+1}. {weapon.name} ({cooldown_text})", True, color)
            screen.blit(weapon_text, (20, weapon_y + i * 30))
        
        # 绘制动作序列
        if self.player.action_sequence:
            seq_text = self.font.render("Sequence:", True, WHITE)
            screen.blit(seq_text, (20, 400))
            
            for i, (action_type, data) in enumerate(self.player.action_sequence):
                if action_type == 'weapon':
                    weapon_name = self.player.weapons[data].name
                    action_text = self.small_font.render(f"- {weapon_name}", True, GREEN)
                    screen.blit(action_text, (30, 430 + i * 25))
        
    def draw_message(self,screen):
        if self.message:
            text = self.font.render(self.message, True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            # 绘制背景框
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, WHITE, bg_rect)
            pygame.draw.rect(screen, BLACK, bg_rect, 2)
            
            screen.blit(text, text_rect)
    
    def update(self):
        # 状态管理 & 消息清除
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""
    
    def draw(self, screen, font):
        # 绘制网格
        self.draw_grid(screen)
        
        # 绘制攻击意图
        self.draw_attack_intents(screen)
        
        # 绘制实体
        self.draw_entities(screen)
        
        # 绘制UI
        self.draw_ui(screen)
        
        # 绘制消息
        self.draw_message(screen)
        
        # 游戏结束屏幕
        if self.game_state == "game_over":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(WHITE)
            screen.blit(overlay, (0, 0))
            
            if not self.enemies:
                end_text = self.large_font.render("胜利!", True, GREEN)
            else:
                end_text = self.large_font.render("失败!", True, RED)
            
            end_rect = end_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(end_text, end_rect)
            
            restart_text = self.font.render("按R键重新开始", True, BLACK)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            screen.blit(restart_text, restart_rect)
        
    
    def restart_game(self):
        self.player = Player(2)
        self.enemies = [Enemy(4)]
        self.game_state = "player_turn"
        self.turn_count = 0
        self.message = ""
        self.message_timer = 0
        self.setup_enemy_intents()


weapon = {
    "Pointer Sword": {
        "damage": 5,
        "pattern": [1],
        "cooldown": 1,
        "color": RED,
        "weapon_type": "meleeMove",
        "unique_in_sequence": False
    },
    "Template Greatsword":{
        "damage": 10,
        "pattern": [-1, 1],
        "cooldown": 4,
        "color": GREEN,
        "weapon_type": "melee",
        "unique_in_sequence": True
    },
    "Snake Staff":{
        "damage": 15,
        "pattern": [2,4,6,8],
        "cooldown": 8,
        "color": GREEN,
        "weapon_type": "melee",
        "unique_in_sequence": True
    },
    "Text Rain":{
        "damage": 5,
        "pattern": [-5,-4,-3,-2,-1,1,2,3,4,5],
        "cooldown": 8,
        "color": GREEN,
        "weapon_type": "melee",
        "unique_in_sequence": True
    },
    "Formula Barrage":{
        "damage": 10,
        "pattern": [1,2,3,4,5],
        "cooldown": 6,
        "color": GREEN,
        "weapon_type": "targeted",
        "unique_in_sequence": True
    }
}
