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
    
    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
    
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
            Weapon("fireball", 15, [1, 2, 3, 4, 5], 8, GREEN, weapon_type="fireball", unique_in_sequence=True),
        ]
        self.skill_points = {
            "tech": 5,
            "lang": 5,
            "algo": 0,
        }
        self.swap_cooldown = 0  # 记录换位剩余冷却回合数

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
            Weapon("claw", 10, [-1,1], 0, RED, weapon_type="melee"),
        ]
        self.waiting = False  
        self.ready_to_attack = False

    def ai_take_turn(self, scene):
        player = scene.player
    
        # 如果敌人有攻击序列
        if self.sequence_length > 0:
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
            success, msg = self.add_weapon_to_sequence(0, scene)
            if success:
                self.waiting = True
            scene.add_message(msg)

    def add_weapon_to_sequence(self, index, scene):
        if index < len(self.weapons):
            weapon = self.weapons[index]
            if weapon.unique_in_sequence and any(weapon_index == index for weapon_index in self.action_sequence):
                return False, f"{weapon.name} Already in Sequence!"
            if self.sequence_length >= self.sequence_limit:
                return False, "Reached Max Sequence Length!"
            elif self.weapons[index].is_ready():
                self.action_sequence.append(index)
                self.sequence_length += 1
                return True, f"{weapon.name} Added"
            else:
                return False, f"{weapon.name} Cooling!"
        return False, "无效的武器编号"
    
    def is_facing_player(self, player):
        return (self.direction == 1 and player.position > self.position) or \
            (self.direction == -1 and player.position < self.position)
    
    def can_hit_player(self, player, scene):
        """检查当前方向 & 攻击模式能否命中玩家"""
        # #假设当前武器是序列第一个
        # weapon = self.weapons[self.action_sequence[0]] if self.action_sequence else None
        # if not weapon:
        #     return False
        # distance = player.position - self.position
        # return (self.direction == 1 and distance in weapon.pattern) or \
        #     (self.direction == -1 and -distance in weapon.pattern)
        return False
    
