import pygame
import random
from util import *
from charactor import Player,Enemy,EnemyFactory,MONSTER_LIBRARY
from entity import Projectile
from events import *
from animation import *
from vfxsystem import VFXSystem
from grid import *
from camera import Camera
from map import *
from Action import GravityAction
from commands import *
from ui_input import *
from gameplay_input import *


class FightScene:
    def __init__(self):
        # 游戏状态
        # self.grid_size = BOARDSIZE + 1
        self.grid_start_x = 100
        self.grid_start_y = 100


        # 游戏状态
        self.game_state = "player_turn"  # player_turn, enemy_turn, game_over
        self.turn_count = 0
        self.messages = []  # 队列，最新的消息插入末尾

        self.events = EventQueue()
        self.current_action=None
        self.camera = Camera()
        self.vfx = VFXSystem(self.camera)

        self.icons = [
            load_image("arts/sprite/sand.png",(32,32)),
            load_image("arts/sprite/Level.png",(32,32)),
        ]
        
        # 生成一个随机关卡
        self.player = Player(self, Vec2(8, 1))
        self.enemies = []
        self.prepare_level()
        # print(self.player.position)

        self.level = 1 
        self.win=False   

        # 字体
        self.font = get_font("Cogmind",10)
        self.small_font = get_font("DOS",16)
        self.large_font = get_font("Cogmind",16)

        #sequence拖动处理
        self.dragging_index = None
        self.dragging_weapon = None
        
        self.player.on_move_check = self.handle_move    #回调函数绑定
        for enemy in self.enemies:
            enemy.on_move_check = self.handle_move
        self.map_width = 16
        self.map_height = 16

        # self.hotbar = WeaponHotbar()

        self.timeline = []
        self.ui_input = UIInputSystem(self)
        self.gameplay_input = GameplayInputSystem(self)
        self.projectiles = []

        self.input_locked = False
        self.spritemanager = SpriteManager()

        self.mouse_pos = (0, 0)

        
    def prepare_level(self):
        self.mymap = Map(GRID_WIDTH, GRID_HEIGHT, self.camera)
        self.mymap.generate_map()

        self.player.position = Vec2(8, 1)
        self.player.render_pos = Vec2(8.0, 1.0)
        # self.mymap.occupy(Vec2(0, 8), self.player)   # ← player 也登记

        self.spawn_enemy()

        self.actions = deque()

    def get_player_data(self):
        return {
            "health": self.player.health,
            "max_health": self.player.max_health,
            "sequence_limit":self.player.sequence_limit,
            "damage_multiplier":self.player.damage_multiplier,
            "status":self.player.status,
            "point":self.player.skill_points,
            "available_skills":self.player.available_skills,
            "learned_skills":self.player.learned_skills,
            "base_stats":self.player.base_stats
        }

    def add_message(self, text, color=WHITE, duration=2000):
        self.messages.append({
            "text": text,
            "color": color,
            "time": pygame.time.get_ticks(),
            "duration": duration,
            "alpha": 255
        })

    
    def get_cell_rect(self,pos):

        x = self.grid_start_x + pos.x * CELL_WIDTH
        y = self.grid_start_y + pos.y * CELL_HEIGHT

        return pygame.Rect(x,y,CELL_WIDTH,CELL_HEIGHT)
    
    def get_cell_center(self, position):
        rect = self.get_cell_rect(position)
        return Vec2(rect.centerx, rect.centery)

    def get_pawn_at(self, pos, pawn_type="all"):

        # 检查玩家
        if pawn_type in ("all", "player"):
            if self.player and self.player.position.x == pos.x and self.player.position.y == pos.y:
                return self.player

        # 检查敌人
        if pawn_type in ("all", "enemy"):
            for enemy in self.enemies:
                if enemy.position.x == pos.x and enemy.position.y == pos.y:
                    return enemy
                
                # 检查敌人
        if pawn_type in ("all","projectile"):
            for p in self.projectiles:
                if p.position.x == pos.x and p.position.y == pos.y:
                    return p

        return None
    
    def get_enemy_positions(self):
        """返回已排序的敌人位置"""
        return sorted(enemy.position for enemy in self.enemies if enemy.alive)
    
    def can_see_line(self,pawn1,pawn2):#666
        # 视线判定：两者之间没有其他单位阻挡
        if pawn1.position == pawn2.position:
            return True
        if pawn2 == self.get_closestL_pawn(pawn1.position, pawn1.direction):
            return True
        return False
    
    def is_facing_player(self,pawn):
        if pawn.direction * (self.player.position.x-pawn.position.x) > 0:
            return True
        return False
    
    # def can_spawn(self,pos):
    #     return self.is_standable(pos) and pos not in self.get_occupied_pos()

    def can_spawn(self, pos, flying=False):
        if flying:
            return self.mymap.is_flyable(pos)
        return self.mymap.is_walkable(pos)
    
    def get_occupied_pos(self):

        result = []

        for enemy in self.enemies:
            result.append(enemy.position)

        result.append(self.player.position)

        return result

    def mdis(self,p1,p2):#曼哈顿距离
        return abs(p1.x-p2.x)+abs(p1.x-p2.x)

    def handle_move(self, actor, new_pos):


        if self.mymap.is_wall(new_pos):
            return None

        if self.player.position.x == new_pos.x and self.player.position.y == new_pos.y: #怪物不能走到玩家位置
            return None

        enemy = self.get_pawn_at(new_pos,"enemy")

        if enemy:

            if isinstance(actor, Player) and actor.swap_cooldown == 0:#玩家的换位技能

                old_actor = actor.position
                old_enemy = enemy.position

                enemy.position = old_actor
                enemy.anim.play(
                    MoveAnimation(enemy.idle_frames, enemy, old_enemy, old_actor)
                )

                actor.swap_cooldown = 4

                return old_enemy

            return None

        # if actor.move_ability.can_move_to(new_pos,self.mymap):
        return new_pos
    
    def resolve_actions(self):

        return any(
            action.turn_consumed
            for action in self.actions
        )
    
    def execute_ui_command(self, command):
        if isinstance(command, SelectWeaponCommand):
            if command.index < len(self.player.weapons):

                self.player.current_weapon_index = (
                    command.index
                )

    def handle_event(self, event):

        # if self.game_state != "player_turn": #已包含在gameplay中
        #     return

        # UI优先
        if self.ui_input.handle_event(event):
            return

        # gameplay
        self.gameplay_input.handle_event(event)

    def process_reactions(self):

        pawn = self.player

        if not self.mymap.is_walkable(pawn.position):

            self.actions.appendleft(
                GravityAction(pawn)
            )


    # def execute_actions(self,actor):
    #     executed_actions = actor.execute_sequence()

    #     if self.player.battle_style == "stack":# stack风格反转序列
    #         executed_actions.reverse()
    #     self.print_executed_actions(executed_actions)
        
    #     for weapon_index, weapon in executed_actions:
    #         # print("atk triggered")
    #         # === 1. 加算 / 基础阶段 ===
    #         base = int(weapon.damage * actor.damage_multiplier)
    #         damage = Damage(base)

    #         # === 2. Decorator 阶段（按规则包） ===
    #         if isinstance(actor, Player):
    #             # print(f"Player enabled decorators: {actor.enabled_damage_decorators}")
    #             if "DDL_fever" in actor.enabled_damage_decorators:
    #                 damage = DDLFeverDecorator(damage, actor)

    #         # 以后可以继续包：
    #         # damage = CriticalDecorator(damage)

    #         damage = damage.value()
    #         # 让武器自己决定产生哪些 Action
    #         actions = weapon.build_actions(self, actor, damage)
    #         self.actions.extend(actions)

    def shoot(self, weapon,actual_damage,actor):
        # 获取当前方向最近的敌人
        closest_enemy = self.get_closest_pawn(actor.position, direction=actor.direction,pawn_type="all")
        
        if not closest_enemy:
            self.add_message(f"{weapon.name} No enemy")
            return False

        distance = abs(closest_enemy.position - actor.position)

        closest_enemy.take_damage(actual_damage,scene=self)
        actor.apply_weapon_effects(closest_enemy, weapon)

        # 超出最大射程
        if distance > weapon.range:
            self.add_message(f"{weapon.name} Too far(Max {weapon.range} tile)")
            return False
        
    def get_closestL_pawn(self,pos,direction):#看一行的最近敌人,用于dash

        i = pos.x + direction
        while 0 < i < GRID_WIDTH - 1:
            if self.mymap.is_wall(Vec2(i,pos.y)): #遇到墙停止
               return None
            pawn = self.get_pawn_at(Vec2(i,pos.y))
            if pawn:
                return pawn
            i+=direction
        return None

    def get_legal_position(self, postion):
        return max(0, min(self.grid_size - 1, postion))

    # def get_adjusted_attack_positions(self, weapon, actor):
    #     adjusted_positions = []
    #     for offset in weapon.pattern:
    #         actual_offset = offset * actor.direction  # 左右翻转
    #         target_pos = actor.position + actual_offset
    #         # if 0 <= target_pos.x < GRID_WIDTH & 0 <= target_pos.y < GRID_HEIGHT:
    #         adjusted_positions.append(target_pos)
    #     print(f"{actor.name}攻击方向: {actor.direction}, 攻击格子: {adjusted_positions}")
    #     return adjusted_positions
    
    def get_occupied_positions(self):
        return {enemy.position for enemy in self.enemies}
    

    
    # def spawn_enemy(self):

    #     pos = self.get_random_spawn_pos()

    #     if pos is None:
    #         return

    #     enemy = self.create_random_enemy(pos)

    #     enemy.on_move_check = self.handle_move

    #     self.enemies.append(enemy)

    def spawn_enemy(self):
        flying_ids = [k for k, v in MONSTER_LIBRARY.items() if v.get("flying")]
        ground_ids  = [k for k, v in MONSTER_LIBRARY.items() if not v.get("flying")]

        # 分别用对应的 spawn 点生成
        for _ in range(12):
            pos = self.get_random_spawn_pos(flying=False)
            if pos:
                enemy = self.create_random_enemy(pos, monster_id=random.choice(ground_ids))
                self.enemies.append(enemy)
                self.mymap.occupy(pos, enemy)

        for _ in range(10):
            pos = self.get_random_spawn_pos(flying=True)
            if pos:
                enemy = self.create_random_enemy(pos, monster_id=random.choice(flying_ids))
                self.enemies.append(enemy)
                self.mymap.occupy(pos, enemy)

    def get_random_spawn_pos(self, flying=False):
        for _ in range(50):
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            pos = Vec2(x, y)
            if self.can_spawn(pos, flying=flying):
                return pos
        return None

    def create_random_enemy(self , position, monster_id=None):
        """从图纸库中生成敌人。"""
        enemy = EnemyFactory.create(self,position)
        return enemy
    
    def save_timeline(self):
            data = [step.to_dict() for step in self.timeline]
            with open("timeline.json", "w") as f:
                json.dump(data, f, indent=4)
    
    def end_player_turn(self):
        self.game_state = "enemy_turn"

        if self.mymap.get_terrain(self.player.position) == 3:
            self.level += 1
            self.prepare_level()
            return  

        if  self.level > 2:
            self.game_state = "game_over"
            self.win=True
            return        
        

        self.player.update_cooldowns()
        if self.player.swap_cooldown > 0:
            self.player.swap_cooldown -= 1
        if self.game_state != "game_over":
            self.game_state = "enemy_turn"
        self.turn_count += 1

        self.player.update_statuses()#更新状态

        self.save_timeline()

        if not self.mymap.is_walkable(self.player.position) and not self.get_pawn_at(self.player.position+Vec2(0,1),"enemy"):
            self.actions.append(GravityAction(self.player))

    def end_enemy_turn(self):
        for enemy in self.enemies:
            enemy.update_cooldowns()

        for enemy in self.enemies:
            if not enemy.flying and enemy.alive:
                if not self.mymap.is_walkable(enemy.position) and not self.get_pawn_at(enemy.position+Vec2(0,1),"all"):
                    self.actions.append(GravityAction(enemy))

        if self.game_state != "game_over":
            self.game_state = "player_turn"
                    
        # # 执行敌人回合
        # pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # 0.1秒后执行玩家回合

        for p in self.projectiles:
            p.update()


    
    def execute_enemy_turn(self,scene):
        for enemy in self.enemies:
            enemy.ai_take_turn(scene)

        self.end_enemy_turn()
        
        # 设置新的攻击意图
        if self.game_state != "game_over":
            self.game_state = "player_turn"
    
    def draw_entities(self,screen):
        self.draw_pawns(screen, self.player)
        
        # 绘制敌人
        for enemy in self.enemies:            
            self.draw_pawns(screen, enemy)

            # 绘制敌人血量
            screen_pos = self.camera.apply(enemy.render_pos)
            hp_text = self.font.render(str(enemy.health), True, GREEN)

            screen.blit(hp_text,(screen_pos[0],screen_pos[1]))

        for projectile in self.projectiles:

            projectile.draw(screen)
            screen_pos=self.camera.apply(projectile.position)
            start = (screen_pos[0]+16,screen_pos[1]+16)
            end = (start[0] + projectile.direction.x * 20,start[1] + projectile.direction.y * 20)
            # end = start + Vec2(10,10)
            pygame.draw.line(screen, GRAY, start, end, 2)
            pygame.draw.circle(screen, GRAY, end, 3)
            

            

    def draw_pawns(self, screen , pawn):
        character = pawn.anim.get_frame()
            
        # 根据方向翻转
        if pawn.direction == 1:  # 朝右
            draw_img = character
        else:  # 朝左
            draw_img = pygame.transform.flip(character, True, False)

        for g in pawn.turn_ghosts:
            draw_img.set_alpha(g["alpha"])
            screen.blit(draw_img,self.camera.apply(g["pos"]))
            

        screen_pos=self.camera.apply(pawn.render_pos)

        draw_img.set_alpha(255)#本体
        screen.blit(draw_img,screen_pos)

        if isinstance(pawn, Player):
            self.draw_hero_overlay(screen, pawn,screen_pos)
        elif isinstance(pawn, Enemy):
            self.draw_enemy_overlay(screen, pawn,screen_pos)

    def draw_hero_overlay(self, screen, pawn: Player,pos):
        line = "*" * pawn.swap_cooldown
        cooldown_surface = self.font.render(line, True, GREEN)
        screen.blit(cooldown_surface, pos)

    def draw_enemy_overlay(self, screen, pawn: Enemy,pos):
        self.draw_intents(screen, pawn, pos)

    def draw_intents(self, screen, pawn, pos):
        intent_x = pos[0] + 10
        intent_y = pos[1] - 20

        hovered_weapon = None  # 当前悬停的武器
        weapon_color = pawn.state.get_weapon_color(pawn)

        for index in pawn.action_sequence:
            weapon = pawn.weapons[index]
            weapon_image = load_image(f"arts/sprite/weapons/{weapon.name}.png",(16,16))

            # 绘制图标
            rect = weapon_image.get_rect(topleft=(intent_x, intent_y))
            render_1bit_sprite(screen, weapon_image, rect.topleft, weapon_color)
            screen.blit(self.font.render(f"{weapon.damage}", True, WHITE), (intent_x - 10 , intent_y))#左下角为伤害

            # 如果鼠标悬停在这个图标上
            if rect.collidepoint(self.mouse_pos):
                hovered_weapon = weapon

            intent_y -= 16  # 间距调整

        for symbol in pawn.state.get_intent_symbols(pawn):
            if symbol == "!":
                name = "Warning"
            elif symbol == "+":
                name = "Adding"
            symbol_image = load_image(f"arts/sprite/weapons/{name}.png", (16, 16))
            render_1bit_sprite(screen, symbol_image, (intent_x, intent_y), weapon_color)
            intent_y -= 48


        # ==============================
        # 悬停时绘制武器详细信息 Tooltip
        # ==============================
        if hovered_weapon:
            self.draw_weapon_tooltip(screen, hovered_weapon, self.mouse_pos)

    def draw_weapon_tooltip(self, screen, weapon, pos):
        
        """在鼠标位置显示武器信息"""
        lines = [f"{weapon.name}",f"Damage: {weapon.damage}"]

        padding = 5
        width = 200
        height = len(lines) * 18 + padding * 2

        x, y = pos
        rect = pygame.Rect(x + 15, y + 15, width, height)

        # 黑底
        pygame.draw.rect(screen, (0, 0, 0), rect)

        # 多层发光描边（外圈先画深色，内圈画亮色）
        pygame.draw.rect(screen,GRAY, rect, 1)


        # 文本
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, WHITE)
            screen.blit(text_surface, (rect.x + padding, rect.y + padding + i * 18))

    def draw_ui(self,screen):
        # 绘制玩家血量,假设最大血量是 10 格
        max_bar_length = 5  
        filled = int(self.player.health / self.player.max_health * max_bar_length)
        bar_str = "#" * filled + "." * (max_bar_length - filled)
        health_text = self.font.render(f"HP{bar_str}({self.player.health}/{self.player.max_health})", True, WHITE)
        screen.blit(health_text, (SCREEN_WIDTH- 120, 50))
        
        # 绘制回合数
        screen.blit(self.icons[0], (SCREEN_WIDTH- 50, 10))
        turn_text = self.font.render(f"{self.turn_count}", True, GREEN)
        screen.blit(turn_text, (SCREEN_WIDTH- 30, 30))
        screen.blit(self.icons[1], (SCREEN_WIDTH- 82, 10))
        level_text = self.font.render(f"{self.level}", True, GREEN)
        screen.blit(level_text, (SCREEN_WIDTH- 30 - 32, 30))
        
        # 绘制武器状态
        self.ui_input.hotbar.draw(screen, self.font)
        self.ui_input.hotbar.set_weapons(self.player.weapons)

        # 绘制动作序列
        if self.player.action_sequence:
            seq_text = self.font.render("Sequence:", True, WHITE)
            screen.blit(seq_text, (10, 200))
            
            for i, index in enumerate(self.player.action_sequence):
                if i == self.dragging_index:#不画选中的
                    continue
                weapon_name = self.player.weapons[index].name
                # action_text = self.small_font.render(f"- {weapon_name}", True, GREEN)
                # screen.blit(action_text, (30, 430 + i * 25))
                weapon_image = load_image(f"arts/sprite/weapons/{weapon_name}.png",(32,32))
                rect = self.get_sequence_rect(i)
                render_1bit_sprite(screen, weapon_image, rect.topleft, GREEN)
                # print(f"INDEX:{self.dragging_weapon}")

                if self.dragging_weapon is not None:

                    weapon_name = self.player.weapons[self.dragging_weapon].name

                    weapon_image = load_image(
                        f"arts/sprite/weapons/{weapon_name}.png",
                        (32,32)
                    )

                    render_1bit_sprite(screen, weapon_image, (pygame.mouse.get_pos()), GREEN)

    def get_sequence_rect(self, i):
        return pygame.Rect(5 + i * 32, 215, 24, 24)
    
    def get_weapon_rect(self, i):
        return pygame.Rect(20, i * 20 - 5 , 24, 24)
        
    def draw_messages(self, screen, font, pos=(SCREEN_WIDTH-500, 500)):
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

    def update_actionqueue(self, dt):

        # print("CURRENT", self.current_action)
        # if self.current_action is not None:
        #     print(self.current_action.actor,self.actions)

        if self.current_action is None and self.actions:
            self.current_action = self.actions.popleft()
            self.current_action.start(self)

        if self.current_action:
            self.current_action.update(self, dt)

            if self.current_action.is_finished():
                self.current_action = None

    def update(self):
        # print(self.actions)

        # 1. 如果是敌人回合且没有正在执行的动作和动画，才执行敌人逻辑
        if self.game_state == "enemy_turn":
            if not self.current_action and not self.actions:
                self._enemy_turn_ready()        # tmp
                self.execute_enemy_turn(self)

        # 统一 dt
        dt = 1/60

        self.update_actionqueue(dt)

        self.process_events()
        self.vfx.update(dt)
        self.camera.update(self.player)

        self.player.update(dt) #包括状态机和动画+死亡管理
        for enemy in self.enemies:
            enemy.update(dt)

        self.cleanup_entities()

        self.ui_input.update()

    def cleanup_entities(self):

        self.enemies = [
            e
            for e in self.enemies
            if e.alive
        ]

        self.projectiles = [
            p
            for p in self.projectiles
            if p.alive
        ]

    def _enemy_turn_ready(self):
        """所有敌人的动画都播完了才返回 True"""
        for enemy in self.enemies:
            #print(enemy.anim.current.index)
            if enemy.anim.current is not None:
                return False
        return True

    def draw(self, screen):
        # print(self.player.position,self.player.render_pos)
        
        self.mymap.draw_map(screen)
        
        # 绘制实体
        self.draw_entities(screen)

        self.vfx.draw(screen)
        
        # 绘制UI
        self.draw_ui(screen)
        
        # 绘制消息
        self.draw_messages(screen,self.small_font)

        # 游戏结束屏幕
        if self.game_state == "game_over":
            self.game_over(screen)


    def game_over(self,screen):
        
        screen.fill(BLACK)
        
        if self.win:
            end_text = self.font.render("Congratulations!", True, GREEN)
        else:
            end_text = self.font.render("You Failed!", True, RED)
            render_ascii_art(screen, label="grave",x=10, y=20, font_size=12, color=WHITE)
            character = load_image('arts/grave.png',(121,294))
            screen.blit(character, (400, 25))

        screen.blit(end_text, (250,100))
        
        restart_text = self.font.render("Q to return Menu,R to restart", True, WHITE)
        screen.blit(restart_text, (250,200))    
    
    def restart_game(self):
        self.player = Player(self)
        self.enemies = [Enemy(self,4)]
        self.game_state = "player_turn"
        self.turn_count = 0
        self.message = []

    def process_events(self):
        while not self.events.empty():
            event = self.events.pop()
            self.handle_scene_event(event)

    def handle_scene_event(self, event):

        if isinstance(event, DamageEvent):
            if(event.target == None or event.target.health<=0):
                return
            event.target.health -= event.amount

            print(f"{event.target.name} took {event.amount} damage, health now {event.target.health}")

            if event.target.health <= 0 :
                self.events.push(DeathEvent(event.target))

        elif isinstance(event, DeathEvent):
            event.pawn.die()

        elif isinstance(event, MessageEvent):
            self.add_message(event.text, event.color)





