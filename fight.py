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
        self.player = Player()  # 开始在中间位置
        self.enemies = []
        self.spawn_enemy()
        
        # 游戏状态
        self.game_state = "player_turn"  # player_turn, enemy_turn, game_over
        self.turn_count = 0
        self.messages = []  # 队列，最新的消息插入末尾
        
        # 字体
        self.font = get_font("en","Cogmind",20)
        self.small_font = get_font("en","DOS",20)
        self.large_font = get_font("ch","Lolita",16)
        
        self.player.on_move_check = self.handle_move#回调函数绑定
        for enemy in self.enemies:
            enemy.on_move_check = self.handle_move


    def get_player_data(self):
        return {
            "health": self.player.health,
            "max_health": self.player.max_health,
            "sequence_limit":self.player.sequence_limit,
            "damage_multiplier":self.player.damage_multiplier,
            "status":self.player.status,
            "point":self.player.skill_points
        }

    def add_message(self, text, color=WHITE, duration=2000):
        self.messages.append({
            "text": text,
            "color": color,
            "time": pygame.time.get_ticks(),
            "duration": duration,
            "alpha": 255
        })

    
    def get_cell_rect(self, position):
        x = self.grid_start_x + position * self.cell_width
        y = self.grid_start_y
        return pygame.Rect(x, y, self.cell_width, self.cell_height)
    
    def get_cell_center(self, position):
        rect = self.get_cell_rect(position)
        return rect.centerx, rect.centery
    
    def get_pawn_at(self, pos, pawn_type="enemy"):
        """
        在指定位置获取单位
        :param pos: 位置 (int)
        :param pawn_type: "enemy" | "ally" | "player" | "all"
        :return: Pawn 对象或 None
        """
        if pawn_type == "enemy":
            pawns = self.enemies
        elif pawn_type == "player":
            pawns = [self.player]
        elif pawn_type == "all":
            pawns = []
            if self.player:   # 玩家存在才加
                pawns.append(self.player)
            pawns.extend(self.enemies)
        else:
            pawns = []
        # 🔑 过滤掉 None
        pawns = [p for p in pawns if p is not None]

        return next((pawn for pawn in pawns if pawn.position == pos), None)
    
    def get_closest_pawn(self, source_position , max_range=None, direction=None, pawn_type="enemy"):
        """
        从整个 scene 中找最近的单位
        :return: 最近的 pawn 或 None
        """
        # 根据 pawn_type 确定候选列表
        if pawn_type == "enemy":
            candidates = self.enemies
        elif pawn_type == "player":
            candidates = [self.player]
        elif pawn_type == "all":
            candidates = [self.player] + self.enemies
        else:
            candidates = []

        if not candidates:
            return None

        # 按方向过滤
        if direction == 1:  # 右边
            candidates = [p for p in candidates if p.position > source_position]
        elif direction == -1:  # 左边
            candidates = [p for p in candidates if p.position < source_position]

        if not candidates:
            return None

        # 找最近
        closest = min(candidates, key=lambda p: abs(p.position - source_position))

        # 射程判定
        if max_range is not None and abs(closest.position - source_position) > max_range:
            return None

        return closest


 
    def handle_move(self, actor, new_pos):
        enemy = self.get_pawn_at(new_pos,"enemy")

        if enemy:#面前为敌人
            # 只有玩家可以换位，且要检查冷却
            if isinstance(actor, Player) and actor.swap_cooldown == 0:
                # 执行换位
                enemy.position, actor.position = actor.position, enemy.position
                actor.swap_cooldown = 4  # 重置换位冷却
                return actor.position  # 玩家位置更新后返回新位置
            else:
                # 敌人不能换位，玩家换位冷却中也不能换位
                return None
        else:
            if actor.can_move_to(new_pos) and self.player.position!=new_pos:#防止怪物跑到玩家脸上
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
            elif event.key in [pygame.K_w, pygame.K_UP]:
                self.player.turn_around()
                self.end_player_turn()
            elif event.key in [pygame.K_s, pygame.K_DOWN]:
                self.end_player_turn()
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                index = event.key - pygame.K_1
                success, msg = self.player.try_add_weapon_to_sequence(index,self)
                self.add_message(msg) #666
            elif event.key == pygame.K_SPACE:
                if self.player.action_sequence:
                    self.execute_actions(self.player)
                    self.end_player_turn()
                else:
                    self.add_message("序列为空!")
    def print_executed_actions(self,executed_actions):
        """
        打印 executed_actions 列表内容，不换行，用 -> 分隔
        executed_actions: [(index, weapon), ...]
        """
        if not executed_actions:
            print("No actions executed.")
            return

        for i, (index, weapon) in enumerate(executed_actions):
            end_char = "->" if i < len(executed_actions) - 1 else "\n"
            print(f"{weapon.name}({index})", end=end_char)


    def execute_actions(self,actor):
        executed_actions = actor.execute_sequence()

        if self.player.battle_style == "stack":# stack风格反转序列
            executed_actions.reverse()
        self.print_executed_actions(executed_actions)

        for weapon_index, weapon in executed_actions:
            multiplier = actor.damage_multiplier
            actual_damage = int(weapon.damage * multiplier)
            # print(f"actual_damage:{actual_damage}")
            # --- 类型1: melee / ranged（固定 pattern 攻击） ---
            if weapon.weapon_type in ["melee", "meleeMove"]:
                if weapon.weapon_type == "meleeMove":
                    actor.move(1)
                self.attack_by_pattern(weapon,actual_damage,actor)

            # --- 类型2: dash_to_enemy ---
            elif weapon.weapon_type == "dash_to_enemy":
                self.use_dash_to_enemy(weapon,actual_damage,actor)

            # --- 类型3: shoot（攻击最近敌人） ---
            elif weapon.weapon_type == "ranged":
                self.shoot(weapon,actual_damage,actor)


            # --- 类型4: fireball（攻击最近敌人±1格） ---
            elif weapon.weapon_type == "fireball":
                closest_pawn = self.get_closest_pawn(actor.position, direction=actor.direction,pawn_type="all")
                if closest_pawn:
                    print(f"explosion_center:{closest_pawn.position}")
                for offset in weapon.pattern:
                    position = closest_pawn.position + offset
                    pawn = self.get_pawn_at(position,pawn_type="all")
                    if pawn:
                        pawn.take_damage(actual_damage,scene=self)

    def attack_by_pattern(self,weapon,actual_damage,actor):

        attack_positions = self.get_adjusted_attack_positions(weapon,actor)
        for enemy in self.enemies[:]:
            if enemy.position in attack_positions:
                enemy.take_damage(actual_damage,scene=self)
        if self.player.position in attack_positions:
            self.player.take_damage(actual_damage,scene=self)


    def shoot(self, weapon,actual_damage,actor):
        # 获取当前方向最近的敌人
        closest_enemy = self.get_closest_pawn(actor.position, direction=actor.direction,pawn_type="all")
        
        if not closest_enemy:
            self.add_message(f"{weapon.name} No enemy")
            return False

        distance = abs(closest_enemy.position - actor.position)

        closest_enemy.take_damage(actual_damage,scene=self)

        # 超出最大射程
        if distance > weapon.range:
            self.add_message(f"{weapon.name} Too far(Max {weapon.range} tile)")
            return False
        

    def use_dash_to_enemy(self, weapon,actual_damage,actor):
        # 获取当前方向最近的敌人
        closest_enemy = self.get_closest_pawn(actor.position, direction=actor.direction,pawn_type="all")
        
        if not closest_enemy:
            self.add_message(f"{weapon.name} No enemy")
            return False

        distance = abs(closest_enemy.position - self.player.position)

        # 超出冲锋最大距离
        if distance > weapon.range:
            self.add_message(f"{weapon.name} Too far(Max {weapon.range} tile)")
            return False
        
        # 停在敌人前一格
        if actor.direction == 1:
            actor.position = closest_enemy.position - 1
        else:
            actor.position = closest_enemy.position + 1

        self.attack_by_pattern(weapon,actual_damage,actor)

        # 判断是否斩杀
        if closest_enemy.health <= 0:
            self.add_message("Kill!")
            # 冲到敌人所在格
            actor.position = closest_enemy.position

        return True


    def get_adjusted_attack_positions(self, weapon, actor):
        adjusted_positions = []
        for offset in weapon.pattern:
            actual_offset = offset * actor.direction  # 左右翻转
            target_pos = actor.position + actual_offset
            if 0 <= target_pos < self.grid_size:
                adjusted_positions.append(target_pos)
        print(f"方向: {actor.direction}, 攻击格子: {adjusted_positions}")
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
        new_enemy.on_move_check = self.handle_move
        self.enemies.append(new_enemy)
        # self.add_message("Enemy Arrived!")

    
    def end_player_turn(self):
        if not self.enemies and self.turn_count>=50:
            self.game_state = "game_over"
            self.add_message("胜利!", 300)
            return        
        
        self.player.update_cooldowns()
        if self.player.swap_cooldown > 0:
            self.player.swap_cooldown -= 1
        if self.game_state != "game_over":
            self.game_state = "enemy_turn"
        self.turn_count += 1
        
        # 每10回合刷2个敌人
        if self.turn_count % 10 == 0:
            self.spawn_enemy()
            self.spawn_enemy()
        
        # 执行敌人回合
        pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # 1秒后执行敌人回合

    def end_enemy_turn(self):
        for enemy in self.enemies :      
            enemy.update_cooldowns()
        if self.game_state != "game_over":
            self.game_state = "player_turn"
                
        # 执行敌人回合
        pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # 0.1秒后执行玩家回合
    
    def execute_enemy_turn(self,scene):
        for enemy in self.enemies:
            # attack_pos = enemy.execute_attack()
            # if attack_pos and self.player.position in attack_pos:
            #     self.player.take_damage(6)
            #     # 添加一个永久脑损伤（疾病类状态）
            #     self.player.add_status(Status("Simplified", "brain", is_illness=True))
            #     self.player.add_status(Status("PC addict", "brain", is_illness=True))
            #     self.player.add_status(Status("Diabetes", "wholebody", is_illness=True))
            #     self.player.add_status(Status("Sad", "brain", is_illness=False))
            #     self.add_message("You Are Under Atack! (-6)")
            #     if self.player.health <= 0:
            #         self.game_state = "game_over"
            #         self.add_message("游戏结束!", 300)
            #         return
            enemy.ai_take_turn(scene)
            self.end_enemy_turn()
        
        # 设置新的攻击意图
        if self.game_state != "game_over":
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
    
    def draw_entities(self,screen):
        self.draw_character_with_arrow(screen, self.player,"Hero")
        
        # 绘制敌人
        for enemy in self.enemies:
            enemy_center = self.get_cell_center(enemy.position)
            
            # 绘制敌人血量
            health_ratio = enemy.health / enemy.max_health
            health_width = 40
            health_x = enemy_center[0] - health_width // 2
            health_y = enemy_center[1] - 35
            
            pygame.draw.rect(screen,SHADOW, (health_x, health_y, health_width, 6))
            pygame.draw.rect(screen, WHITE, (health_x, health_y, int(health_width * health_ratio), 6))

            self.draw_character_with_arrow(screen, enemy ,"Enemy1")

    def draw_character_with_arrow(self, screen , pawn, type):
        arrow_font = get_font("ch","Lolita")
        # 加载图片
        if type =="Hero":
            character = load_image('assets/hero.png')
        elif type == "Enemy1":
            character = load_image('assets/Enemy1.png')
            
        # 根据方向翻转
        if pawn.direction == 1:  # 朝右
            draw_img = character
            arrow_surface = arrow_font.render("→", True, GRAY)
        else:  # 朝左
            draw_img = pygame.transform.flip(character, True, False)
            arrow_surface = arrow_font.render("←", True, GRAY)

        # 获取格子矩形 & 中心
        rect = self.get_cell_rect(pawn.position)
        center_x, center_y = rect.center

        # 角色图片居中
        draw_x = center_x - draw_img.get_width() // 2
        draw_y = center_y - draw_img.get_height() // 2
        screen.blit(draw_img, (draw_x, draw_y))

        # 箭头居中
        arrow_x = center_x - arrow_surface.get_width() // 2
        arrow_y = center_y + 15  
        screen.blit(arrow_surface, (arrow_x, arrow_y))

        if type =="Hero":
            line= "#" * pawn.swap_cooldown
            cooldown_surface = arrow_font.render(line, True, GRAY)
            screen.blit(cooldown_surface, (arrow_x, arrow_y + 10))
        if type =="Enemy1":
            intents = self.draw_enemy_intent(pawn)
            for intent in intents:
                intent_surface = arrow_font.render(intent, True, RED)
                screen.blit(intent_surface, (arrow_x, arrow_y + 10))
                arrow_y += 15
        

    def draw_enemy_intent(self, pawn):
        line=[]
        for index in pawn.action_sequence:
            weapon = pawn.weapons[index]
            line.append(f"{weapon.name}({weapon.damage})")

        return line

    def draw_ui(self,screen):
        # 绘制玩家血量,假设最大血量是 10 格
        max_bar_length = 10  
        filled = int(self.player.health / self.player.max_health * max_bar_length)
        bar_str = "#" * filled + "." * (max_bar_length - filled)
        health_text = self.small_font.render(f"HP: {bar_str}({self.player.health}/{self.player.max_health})", True, WHITE)
        screen.blit(health_text, (30, SCREEN_HEIGHT-80))
        
        # 绘制回合数
        turn_text = self.font.render(f"Turn: {self.turn_count}", True, WHITE)
        screen.blit(turn_text, (SCREEN_WIDTH- 200, 20))
        
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
            
            for i, index in enumerate(self.player.action_sequence):
                weapon_name = self.player.weapons[index].name
                action_text = self.small_font.render(f"- {weapon_name}", True, GREEN)
                screen.blit(action_text, (30, 430 + i * 25))
        
    def draw_messages(self, screen, font, pos=(SCREEN_WIDTH-500, 400)):
        now = pygame.time.get_ticks()
        y_offset = 0
        to_remove = []

        for msg in self.messages:
            elapsed = now - msg["time"]

            # 进入淡出阶段
            if elapsed > msg["duration"]:
                fade_progress = min((elapsed - msg["duration"]) / 500, 1)
                msg["alpha"] = 255 * (1 - fade_progress)

            # 完全透明就删除
            if msg["alpha"] <= 0:
                to_remove.append(msg)
                continue

            # 渲染文字
            text_surface = font.render(msg["text"], True, msg["color"])
            text_surface.set_alpha(int(msg["alpha"]))
            screen.blit(text_surface, (pos[0], pos[1] + y_offset))

            y_offset += font.get_height() + 5  # 每条消息向下偏移

        # 清理过期消息
        for msg in to_remove:
            self.messages.remove(msg)

    def draw_intents(self, screen):
        for enemy in self.enemies:
            line = "" 
            # print(f"{enemy.position}:{enemy.waiting}")
            if enemy.waiting:
                line = "!"
            if enemy.ready_to_attack:
                line = "!!!"
            
            text_surface = self.small_font.render(line, True, RED)
            position= self.get_cell_center(enemy.position)
            new_pos = (position[0], position[1]-50)
            screen.blit(text_surface, new_pos)
    
    def draw(self, screen):
        # 绘制网格
        self.draw_grid(screen)

        self.draw_intents(screen)
        
        # 绘制实体
        self.draw_entities(screen)
        
        # 绘制UI
        self.draw_ui(screen)
        
        # 绘制消息
        self.draw_messages(screen,self.small_font)

        # 游戏结束屏幕
        if self.game_state == "game_over":
            self.game_over(screen)

    def game_over(self,screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(WHITE)
        screen.blit(overlay, (0, 0))
        
        if not self.enemies:
            end_text = self.large_font.render("Congratulations!", True, GREEN)
        else:
            end_text = self.font.render("You Failed!", True, RED)
        
        end_rect = end_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2+100))
        screen.blit(end_text, end_rect)
        
        restart_text = self.font.render("Press q to return Menu,r to restart", True, BLACK)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(restart_text, restart_rect)    
    
    def restart_game(self):
        self.player = Player(2)
        self.enemies = [Enemy(4)]
        self.game_state = "player_turn"
        self.turn_count = 0
        self.message = []

