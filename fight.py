import pygame
import random

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (220, 20, 60)
GREEN = (34, 139, 34)

BOARDSIZE=8

class Weapon:
    def __init__(self, name, damage, range_pattern, cooldown, color,weapon_type="melee",unique_in_sequence=True):
        self.name = name
        self.damage = damage
        self.range_pattern = range_pattern  # 相对于玩家位置的攻击范围
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.color = color
        self.weapon_type = weapon_type  # 新增字段：melee / ranged / targeted
        self.unique_in_sequence = unique_in_sequence
    
    def is_ready(self):
        return self.current_cooldown == 0
    
    def use(self):
        if self.is_ready():
            self.current_cooldown = self.cooldown
            return True
        return False
    
    def update_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

class Player:
    def __init__(self, position=2):
        self.position = position  # 0-4的网格位置
        self.health = 100
        self.max_health = 100
        self.action_sequence = []  # 存储将要执行的动作序列
        self.direction = 1
        self.unlocked_skills = set()  # 存储已解锁技能的字符串名
        self.damage_multiplier = 1.0  # 默认伤害倍数
        self.sequence_limit = 4 
        self.sequence_length = 0
        self.battle_style = "queue"  # 默认风格（正序）
        self.weapons = set()
        
  
        
        # 武器
        self.weapons = [
            Weapon("fireball", 15, [1,2,3,4,5], 8, GREEN, weapon_type="fireball", unique_in_sequence=True),
            Weapon("弓箭", 10, [1,2,3,4,5], 5, GREEN, weapon_type="targeted", unique_in_sequence=True)
        ]

        
    def can_move_to(self, new_pos):
        return 0 <= new_pos <= BOARDSIZE
    
    def move(self, offset):
        # print("f Move offset:{offset},direction:{self.direction},position:{self.position}")
        if offset > 0 and self.direction == 1 or offset < 0 and self.direction == -1:
            new_pos = self.position + offset
            if self.can_move_to(new_pos):
                self.position = new_pos
                return True
        elif offset < 0 and self.direction == 1 or offset > 0 and self.direction == -1:
            self.direction *= -1
            return True
        else :
            print("不能移动到该位置")

        return False
    
    def try_add_weapon_to_sequence(self, index):
        if index < len(self.weapons):
            weapon = self.weapons[index]
            if weapon.unique_in_sequence and any(action[1] == index for action in self.action_sequence):
                return False, f"{weapon.name} 已在序列中!"
            if self.sequence_length >= self.sequence_limit:
                return False, "序列已满!"
            elif self.weapons[index].is_ready():
                self.action_sequence.append(('weapon', index))
                self.sequence_length += 1
                return True, f"添加 {weapon.name} 到序列"
            else:
                return False, f"{weapon.name} 冷却中!"
        return False, "无效的武器编号"

    
    def execute_sequence(self):
        executed_actions = []
        for action_type, data in self.action_sequence:
            if action_type == 'weapon':
                weapon = self.weapons[data]
                if weapon.use():
                    executed_actions.append((action_type, data, weapon))
        self.action_sequence.clear()
        self.sequence_length = 0
        return executed_actions
    
    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
    
    def update_cooldowns(self):
        for weapon in self.weapons:
            weapon.update_cooldown()

    def apply_skill_effect(self, player, skill_name):
        if skill_name == "Hello world":
            player.damage_multiplier = 1.2
            player.unlocked_skills.add(skill_name)

        elif skill_name == "C++":
            fireball = Weapon("C++", 5, [1, 2, 3, 4, 5, 6,7, 8], 8, RED, weapon_type="melee", unique_in_sequence=True)
            player.unlock_weapon(fireball)
            player.unlocked_skills.add(skill_name)

        elif skill_name == "stack":
            player.unlocked_skills.add("stack")
            player.battle_style = "stack"  # 改变执行顺序
            player.damage_multiplier = 1.2  # 可选：stack流派加伤

        elif skill_name == "queue":
            player.unlocked_skills.add("queue")
            player.sequence_limit += 2

        else:
            print(f"技能 {skill_name} 尚未实现效果")

    def unlock_weapon(self, weapon_name):
        if weapon_name not in self.weapons:
            if weapon_name in weapon:
                w = weapon[weapon_name]
                new_weapon = Weapon(
                    weapon_name,
                    w["damage"],
                    w["pattern"],
                    w["cooldown"],
                    w["color"],
                    weapon_type=w["weapon_type"],
                    unique_in_sequence=w["unique_in_sequence"]
                )
                self.weapons.append(new_weapon)
                print(f"已解锁武器：{weapon_name}")
            else:
                print(f"武器名 {weapon_name} 不存在于weapon字典中。")




class Enemy:
    def __init__(self, position, attack_intent=None):
        self.position = position
        self.health = 50
        self.max_health = 50
        self.attack_intent = attack_intent  # 显示即将攻击的位置
        self.intent_timer = 0
        
    def show_attack_intent(self, target_positions):
        self.attack_intent = target_positions
        self.intent_timer = 2  # 提前2回合显示攻击意图
    
    def execute_attack(self):
        if self.intent_timer > 0:
            self.intent_timer -= 1
            return None
        elif self.attack_intent:
            attack_pos = self.attack_intent
            self.attack_intent = None
            return attack_pos
        return None
    
    def take_damage(self, damage):
        self.health = max(0, self.health - damage)

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
        self.font = pygame.font.SysFont("萝莉体", 24)
        self.small_font =pygame.font.SysFont("萝莉体", 24)
        self.large_font = pygame.font.SysFont("萝莉体", 24)
        
        # 初始化敌人攻击意图
        self.setup_enemy_intents()
    
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
                success, msg = self.player.try_add_weapon_to_sequence(index)
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
            print(actual_damage)

            # --- 类型1: melee / ranged（固定 pattern 攻击） ---
            if weapon.weapon_type in ["melee", "ranged"]:
                attack_positions = self.get_adjusted_attack_positions(weapon)
                
                hit = False
                for enemy in self.enemies[:]:
                    if enemy.position in attack_positions:
                        enemy.take_damage(actual_damage)
                        hit = True
                        self.show_message(f"{weapon.name} 命中敌人! (-{actual_damage})")
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            self.show_message("敌人被击败!")
                if not hit:
                    self.show_message(f"{weapon.name} 没有命中任何敌人")


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
        self.show_message("新的敌人出现了！")

    
    def end_player_turn(self):
        if not self.enemies:
            self.game_state = "game_over"
            self.show_message("胜利!", 300)
            return
        
        self.player.update_cooldowns()
        self.game_state = "enemy_turn"
        self.turn_count += 1
        
        # === 新增部分：每10回合刷1个敌人 ===
        if self.turn_count % 10 == 0:
            self.spawn_enemy()
        
        # 执行敌人回合
        pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # 1秒后执行敌人回合
    
    def execute_enemy_turn(self):
        for enemy in self.enemies:
            attack_pos = enemy.execute_attack()
            if attack_pos and self.player.position in attack_pos:
                self.player.take_damage(20)
                self.show_message("你被敌人攻击了! (-20)")
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
            if i == self.player.position:
                color = GRAY  # 玩家位置
            
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, WHITE, rect, 2)
            
            # 绘制位置编号
            pos_text = self.small_font.render(str(i), True, WHITE)
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
        small_font = pygame.font.SysFont("萝莉体", 36)
        # 绘制玩家
        player_center = self.get_cell_center(self.player.position)
        # pygame.draw.circle(self.screen, GREEN, player_center, 20)
        # pygame.draw.circle(self.screen, BLACK, player_center, 15)
        arrow_left = small_font.render("←", True, GREEN)  
        arrow_right = small_font.render("→", True, GREEN)  

        if (self.player.direction == 1):
            screen.blit(arrow_right,player_center)
        else:
            screen.blit(arrow_left,player_center)
        
        # 绘制敌人
        for enemy in self.enemies:
            enemy_center = self.get_cell_center(enemy.position)
            pygame.draw.circle(screen, RED, enemy_center, 20)
            pygame.draw.circle(screen, BLACK, enemy_center, 15)
            
            # 绘制敌人血量
            health_ratio = enemy.health / enemy.max_health
            health_width = 40
            health_x = enemy_center[0] - health_width // 2
            health_y = enemy_center[1] - 35
            
            pygame.draw.rect(screen, RED, (health_x, health_y, health_width, 6))
            pygame.draw.rect(screen, GREEN, (health_x, health_y, int(health_width * health_ratio), 6))
    
    def draw_ui(self,screen):
        # 绘制玩家血量
        health_text = self.font.render(f"血量: {self.player.health}/{self.player.max_health}", True, WHITE)
        screen.blit(health_text, (20, 20))
        
        # 绘制回合数
        turn_text = self.font.render(f"回合: {self.turn_count}", True, WHITE)
        screen.blit(turn_text, (20, 60))
        
        # 绘制武器状态
        weapon_y = 100
        for i, weapon in enumerate(self.player.weapons):
            color = GREEN if weapon.is_ready() else RED
            cooldown_text = f"冷却: {weapon.current_cooldown}" if not weapon.is_ready() else "就绪"
            
            weapon_text = self.small_font.render(f"{i+1}. {weapon.name} ({cooldown_text})", True, color)
            screen.blit(weapon_text, (20, weapon_y + i * 30))
        
        # 绘制动作序列
        if self.player.action_sequence:
            seq_text = self.font.render("动作序列:", True, WHITE)
            screen.blit(seq_text, (20, 400))
            
            for i, (action_type, data) in enumerate(self.player.action_sequence):
                if action_type == 'weapon':
                    weapon_name = self.player.weapons[data].name
                    action_text = self.small_font.render(f"- {weapon_name}", True, GREEN)
                    screen.blit(action_text, (30, 430 + i * 25))
        
        # 绘制控制说明
        if self.game_state == "player_turn":
            controls = [
                "A/D 或 ←/→ - 移动",
                "1/2 - 添加武器到序列",
                "空格 - 执行序列"
            ]
            for i, control in enumerate(controls):
                text = self.small_font.render(control, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH - 250, 20 + i * 25))

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
        "weapon_type": "melee",
        "unique_in_sequence": False
    },
    "Template Greatsword":{
        "damage": 20,
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
    }
}
