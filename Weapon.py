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