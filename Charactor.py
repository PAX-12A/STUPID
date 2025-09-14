import pygame
import random
from font_manager import get_font
from colors import *
from Weapon import Weapon,weapon_info

class Status:
    def __init__(self, name, body_part, is_temp=False, is_illness=False, duration=None):
        self.name = name                  # 状态名称，例如 "中毒"、"骨折"
        self.body_part = body_part        # 作用部位，例如 "brain"、"wholebody"、"left_arm"
        self.is_temp = is_temp            # 是否临时（True = 怪物施加/短期状态）
        self.is_illness = is_illness      # 是否疾病
        self.duration = duration          # 持续回合数（None 代表永久）
    
    def update(self):
        """每回合减少持续时间，临时状态到0就消失"""
        if self.duration is not None:
            self.duration -= 1
            if self.duration <= 0:
                return True  # 返回 True 表示需要移除
        return False

    def __repr__(self):
        return f"<Status {self.name} on {self.body_part}>"
    
class Actor:
    def __init__(self, position=0, health=100, sequence_limit=4):
        self.position = position
        self.direction = 1
        self.health = health
        self.max_health = health
        self.action_sequence = []
        self.sequence_limit = sequence_limit
        self.sequence_length = 0
        self.damage_multiplier = 1.0
        self.status = []
        self.weapons = []
        self.battle_style = "queue"  # 或 stack
        self.on_move_check = None  # 回调（检测位置交换等）
        self.alive = True   # 是否存活

    def add_status(self, status):
        """添加状态，如果已有同名状态，可以覆盖或叠加"""
        self.status.append(status)

    def remove_status(self, status_name):
        self.status = [s for s in self.status if s.name != status_name]

    def update_statuses(self):
        """每回合更新所有状态"""
        self.status = [s for s in self.status if not s.update()]

    def get_status_by_part(self, part):
        """获取某个部位的所有状态"""
        return [s for s in self.status if s.body_part == part]
    
    def take_damage(self, damage, scene):
        """接受伤害并检查是否死亡"""
        self.health -= damage
        if self.health <= 0:
            self.die(scene)  # 传入场景来移除角色
        self.add_status(Status("Simplified", "brain", is_illness=True))#666

    def die(self, scene):
        """角色死亡的基础逻辑"""
        print(f"Pawn has died.")
        self.health = 0  # 确保血量为 0
        self.alive = False
        self.remove_from_scene(scene)  # 从场景中移除角色

    def remove_from_scene(self, scene):
        """从场景中移除角色"""
        if isinstance(self, Player):
            print(f"Removing player from the scene...")
        elif isinstance(self, Enemy):
            print(f"Removing enemy from the scene...")
            scene.enemies.remove(self)  # 移除敌人
        else:
            print(f"Unknown actor type: {self.name}")
    
    def update_cooldowns(self):
        for weapon in self.weapons:
            weapon.update_cooldown()

    def try_add_weapon_to_sequence(self, index, scene):
        if index < len(self.weapons):
            weapon = self.weapons[index]
            if weapon.unique_in_sequence and any(action == index for action in self.action_sequence):
                return False, f"{weapon.name} Already in Sequence!"
            if self.sequence_length >= self.sequence_limit:
                return False, "Reached Max Sequence Length!"
            elif self.weapons[index].is_ready():
                self.action_sequence.append(index)
                self.sequence_length += 1
                scene.end_player_turn()
                return True, f"{weapon.name} Added"
            else:
                return False, f"{weapon.name} Cooling!"
        return False, "无效的武器编号"
    
    def execute_sequence(self):
        executed_actions = []
        for index in self.action_sequence:
            weapon = self.weapons[index]
            if weapon.use():
                executed_actions.append((index, weapon))
        self.action_sequence.clear()
        self.sequence_length = 0
        return executed_actions
    
    def can_move_to(self, new_pos):
        return 0 <= new_pos <= BOARDSIZE
    
    def turn_around(self):
        self.direction *= -1
    
    def move(self, offset):
        new_pos = self.position + offset

        # === 让外部来决定能否移动（以及是否交换位置） ===
        if self.on_move_check:
            new_pos = self.on_move_check(self, new_pos)

        if new_pos is not None:
            self.position = new_pos
            return True
        # else:
        #     print("不能移动到该位置")
        return False

class Player(Actor):
    def __init__(self, position=2):
        super().__init__(position, health=100, sequence_limit=4)
        self.unlocked_skills = set()
        self.weapons = [
            Weapon("fireball", 15, [-1,0,1], 8, GREEN, weapon_type="fireball"),
        ]
        self.skill_points = {
            "tech": 5,
            "lang": 5,
            "algo": 0,
        }
        self.swap_cooldown = 0  # 记录换位剩余冷却回合数

    def die(self,scene):
        """玩家死亡时的特殊逻辑"""
        super().die(scene)  # 调用父类的 die() 处理基本死亡逻辑
        print("Game Over. You have died.")  # 显示游戏结束提示
        scene.game_state = "game_over"   # ✅ 切换游戏状态，而不是删掉 player

    def game_over(self):
        """游戏结束的逻辑"""
        print("Ending the game...")

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
            if weapon_name in weapon_info:
                w = weapon_info[weapon_name]
                new_weapon = Weapon(
                    weapon_name,
                    w["damage"],
                    w["pattern"],
                    w["cooldown"],
                    w["color"],
                    weapon_type=w["weapon_type"],
                    unique_in_sequence=w["unique_in_sequence"],
                    range=w.get("range", None)
                )
                self.weapons.append(new_weapon)
                print(f"已解锁武器：{weapon_name}")
            else:
                print(f"武器名 {weapon_name} 不存在于weapon字典中。")

class Enemy(Actor):
    def __init__(self, position=5):
        super().__init__(position, health=30, sequence_limit=4)
        self.weapons = [
            #Weapon("claw", 10, [1], 0, RED, weapon_type="melee"),
            Weapon("Fireball", 15, [-1,0,1], 1, GREEN, weapon_type="fireball"),
            #Weapon("Spear", 5, [1,2], 2, GREEN, weapon_type="melee"),
            Weapon("Dash",8,[1],1,RED,weapon_type="dash_to_enemy",range=3),
            Weapon("Arrow",13,[1],1,RED,weapon_type="ranged",range=9),
        ]
        self.waiting = False  
        self.ready_to_attack = False

    def die(self,scene):
        """敌人死亡时的特殊逻辑"""
        super().die(scene)  # 调用父类的 die() 处理基本死亡逻辑
        print(f"Enemy dropped loot!")  # 显示敌人掉落物品提示
        # 这里可以增加掉落物品的逻辑

    def ai_take_turn(self, scene):
        player = scene.player
    
        # 如果敌人攻击序列>2
        if self.sequence_length > 1:
            if self.waiting:  
                # --- 检查能否命中玩家 ---
                if self.can_hit_player(player, scene):
                    # 可以命中 → 保持等待状态，下一回合会攻击
                    scene.add_message(f"Enemy is ready to attack")
                    # 等待结束后下回合执行攻击
                    self.waiting = False  
                    self.ready_to_attack=True
                else:
                    # --- 不能命中，先调整方向 ---
                    if not self.is_facing_player(player):
                        self.turn_around()
                        scene.add_message(f"Enemy turn around")
                    else:
                        self.move(self.direction)
                
                return
            elif self.ready_to_attack == 1:
                # 施放攻击
                scene.execute_actions(self)
                self.ready_to_attack=False
        
        else:
            # --- 没有攻击序列：添加武器并进入 waiting ---
            weapon_index = random.randint(0,len(self.weapons))# random weapon
            if self.add_weapon_to_sequence(weapon_index, scene):
                self.waiting = True

    def add_weapon_to_sequence(self, index, scene):
        if index < len(self.weapons):
            weapon = self.weapons[index]
            if weapon.unique_in_sequence and any(weapon_index == index for weapon_index in self.action_sequence):
                return False
            if self.sequence_length >= self.sequence_limit:
                return False
            elif self.weapons[index].is_ready():
                self.action_sequence.append(index)
                self.sequence_length += 1
                return True
            else:
                return False
        return False, "无效的武器编号"
    
    def is_facing_player(self, player):
        return (self.direction == 1 and player.position > self.position) or \
            (self.direction == -1 and player.position < self.position)
    
    def can_hit_player(self, player, scene):#临时的方案，实际和怪物种类相关
        """检查当前方向 & 攻击模式能否命中玩家"""
        if player:
            distance = self.position - player.position
            if abs(distance)<=3 and distance * self.direction<0:
                return True
        return False
    
class Goblin(Enemy):
    def __init__(self, position):
        super().__init__(position, health=20, sequence_limit=3)
        self.weapons = [
            Weapon("Dagger", 6, [1], 0, RED, weapon_type="melee")
        ]
        self.set_ai(AggressiveAI())  # 永远近战

class Archer(Enemy):
    def __init__(self, position):
        super().__init__(position, health=15, sequence_limit=3)
        self.weapons = [
            Weapon("Bow", 10, [1], 1, GREEN, weapon_type="ranged", range=5)
        ]
        self.set_ai(RangedAI())  # 永远远程

class AggressiveAI:
    """近战AI：追击并攻击玩家"""
    def decide_action(self, enemy, scene):
        player = scene.player
        weapon = enemy.weapons[0]  # 假设永远第0个武器是近战

        # 距离判断
        if abs(player.position - enemy.position) <= max(weapon.range or 1, 1):
            enemy.add_weapon_to_sequence(0, scene)
            scene.add_message(f"{enemy} slashes with {weapon.name}!")
            scene.execute_actions(enemy)
        else:
            # 靠近玩家
            direction = 1 if player.position > enemy.position else -1
            enemy.move(direction)


class RangedAI:
    """远程AI：保持距离射击"""
    def decide_action(self, enemy, scene):
        player = scene.player
        weapon = enemy.weapons[0]  # 永远第0个武器是远程
        distance = abs(player.position - enemy.position)

        if distance <= weapon.range and weapon.is_ready():
            enemy.add_weapon_to_sequence(0, scene)
            scene.add_message(f"{enemy} shoots a {weapon.name}!")
            scene.execute_actions(enemy)
        else:
            # 保持拉扯
            if distance < weapon.range // 2:
                enemy.move(-enemy.direction)
            else:
                enemy.move(enemy.direction if player.position > enemy.position else -enemy.direction)

# def spawn_enemy(enemy_type, position):
#     if enemy_type == "goblin":
#         return Goblin(position)
#     elif enemy_type == "archer":
#         return Archer(position)
#     else:
#         raise ValueError(f"Unknown enemy type: {enemy_type}")
# enemy = spawn_enemy("archer", position=8)
# scene.enemies.append(enemy)


