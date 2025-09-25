from colors import *
class Weapon:
    def __init__(self, name, damage, pattern, cooldown, color,weapon_type="melee",unique_in_sequence=True,range=None,status_effects=None):
        self.name = name
        self.damage = damage
        self.pattern = pattern  # 相对于玩家位置的攻击范围
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.color = color
        self.weapon_type = weapon_type  # 新增字段：melee / ranged / targeted
        self.unique_in_sequence = unique_in_sequence
        self.range=range
        self.status_effects = status_effects or []  # 支持多个状态效果
    
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

weapon_info = {
    "Hello World": {
        "damage": 5,
        "pattern": [1],
        "range": 9,
        "cooldown": 0,
        "color": RED,
        "weapon_type": "roll",
        "unique_in_sequence": False
    },
    "Pointer Sword": {
        "damage": 5,
        "pattern": [1],
        "range": 9,
        "cooldown": 4,
        "color": RED,
        "weapon_type": "dash_to_enemy",
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
        "range": 5,
        "cooldown": 6,
        "color": GREEN,
        "weapon_type": "ranged",
        "unique_in_sequence": True
    },
    "Random Generator":{
        "damage": 6,
        "pattern": [-5,-4,-3,-2,-1,1,2,3,4,5],
        "cooldown": 4,
        "color": GREEN,
        "weapon_type": "random",
        "unique_in_sequence": True
    },
    "JVM Inferno Staff": {
        "damage": 15,
        "pattern": [-2,-1,0,1,2],
        "range": 9,
        "cooldown": 7,
        "color": RED,
        "weapon_type": "fireball",
        "unique_in_sequence": True
    },
}