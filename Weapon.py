from util import *
from grid import Vec2
from Action import *
from entity import Arrow



class Weapon:
    def __init__(self, name, data):
        self.name = name
        self.damage = data.get("damage",0)
        self.cooldown = data.get("cooldown",0)
        self.current_cooldown = 0
        self.unique_in_sequence = data.get("unique_in_sequence",True)
        # self.status_effects = data.get("status_effects",None)
        self.behavior = data.get("behavior",None)
        self.config = data
    
    def is_ready(self):
        return self.current_cooldown <= 0
    
    def use(self):
        if self.is_ready():
            self.current_cooldown = self.cooldown
            return True
        return False
    
    def update_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def get_attack_positions(self, actor):

        adjusted_positions = []

        for offset in self.config["pattern"]:

            actual_offset = offset * actor.direction

            target_pos = actor.position + actual_offset

            adjusted_positions.append(target_pos)

            print(f"{actor.name}攻击方向: {actor.direction}, 攻击格子: {adjusted_positions}")

        return adjusted_positions
    

    # def build_actions(self, scene, actor):

    #     return behavior_registry[self.behavior](self,scene,actor)

    def build_actions(self, scene, actor):

        actions = []

        behaviors = self.behavior

        if isinstance(behaviors, str):
            behaviors = [behaviors]

        for behavior in behaviors:

            actions.extend(
                behavior_registry[behavior](
                    self,
                    scene,
                    actor
                )
            )

        return actions
    
def mirror(vec,direction):
    return Vec2(
        vec.x * direction,
        vec.y
    )
    
def build_pattern_attack(weapon,scene,actor):

    pattern = []

    for offset in weapon.config["pattern"]:

        pattern.append(actor.position +offset * actor.direction)

    return [AttackAction(actor,weapon,pattern,weapon.damage)]

def build_dash_attack(weapon, scene, actor):

    def sequence():

        closest_enemy = scene.get_closestL_pawn(actor.position,actor.direction)

        if not closest_enemy:
            yield MoveAction(actor,Vec2(actor.direction, 0))
            return

        target_x = (closest_enemy.position.x - actor.direction)

        offset = Vec2(target_x - actor.position.x,0)

        yield MoveAction(actor, offset)

        # Move 执行后：actor.position 已经是最新的

        attack_positions = weapon.get_attack_positions(actor)

        yield AttackAction(actor,weapon,attack_positions,weapon.damage)

    return [SequenceAction(actor, sequence())]

# def build_roll_attack(weapon, scene, actor):

#     def sequence():

#         closest_enemy = scene.get_roll_pawn(actor.position,actor.direction)

#         if not closest_enemy:
#             yield MoveAction(actor,Vec2(actor.direction, 0))
#             return

#         target_x = (closest_enemy.position.x + actor.direction)

#         offset = Vec2(target_x - actor.position.x ,0)

#         yield MoveAction(actor, offset)

#         attack_positions = weapon.get_attack_positions(actor)

#         yield AttackAction(actor,weapon,attack_positions,weapon.damage)

#     return [SequenceAction(actor, sequence())]

def build_roll_attack(weapon, scene, actor):

    def sequence():

        targets = scene.get_roll_pawns(actor.position,actor.direction)

        if not targets:
            yield MoveAction(actor,Vec2(actor.direction,0))
            return

        last_target = targets[-1]

        target_x = (last_target.position.x+ actor.direction)

        offset = Vec2(target_x - actor.position.x,0)

        yield MoveAction(actor, offset)

        attack_positions = [pawn.position for pawn in targets]

        yield AttackAction(actor,weapon,attack_positions,weapon.damage)

    return [SequenceAction(actor, sequence())]

def build_move(weapon, scene, actor):
    act = []
    for op in weapon.config["move"]:
        if op !=Vec2(0,-1): #向上不镜像
            op = op * actor.direction
        act.append(MoveAction(actor,op))
    return act


def build_mine(weapon, scene, actor):
    return [
        MineAction(actor,weapon),
        AttackAction(actor, weapon,attack_positions = weapon.get_attack_positions(actor), damage = weapon.damage),  # execute() 只做攻击
    ]
    
def build_pn(weapon,scene,actor):
    

    actions = []

    for spawn in weapon.config["spawns"]:

        actions.append(
            SpawnEntityAction(
                actor,
                entity_type=spawn["entity"],
                direction=mirror(spawn["direction"],actor.direction),
                offset=mirror(spawn["offset"],actor.direction),#与actor的direction有关
            )
        )
    return [ParallelAction(actor,actions)]
    

weapon_info = {
    "Hello World": {
        "damage": 1,
        "behavior": "pattern",
        "pattern": [Vec2(1,0)],
        "cooldown": 0,
        "unique_in_sequence": False
    },
    "Goto Jump": {
        "behavior": "move",
        "move": [Vec2(0,-1),Vec2(0,-1)],
        "pattern": [Vec2(0,-1),Vec2(0,-1)],
        "cooldown": 0,
    },
    "DEBUG": {
        "behavior": "move",
        "move": [Vec2(2,0)],
        "cooldown": 0,
        "unique_in_sequence": False
    },
    "DragAndDrop": {
        "behavior": "move",
        "move": [Vec2(0,-1),Vec2(0,-1),Vec2(0,-1),Vec2(0,-1),Vec2(0,-1),Vec2(0,-1)],
        "cooldown": 4,
    },
    "Pointer Sword": {
        "behavior": "dash",
        "damage": 2,
        "pattern": [Vec2(1,0)],
        "cooldown": 4,
    },
    "Template Greatsword":{
        "damage": 3,
        "behavior": "pattern",
        "pattern": [Vec2(-1,0), Vec2(1,0),Vec2(0,-1), Vec2(0,1)],
        "cooldown": 4,
    },
    "Data Mining": {
        "damage": 2,
        "behavior": "mine",
        "pattern": [Vec2(0,1),Vec2(-1,0),Vec2(1,0)],
        "cooldown": 4,
    },
    "Snake Roll":{
        "damage": 1,
        "behavior": "roll",
        "pattern": [Vec2(-1,0)],
        "cooldown": 5,
    },
    "Shotgun":{
        "behavior": ["pn","move"],
        "move":[Vec2(-1,0),Vec2(-1,0)],
        "cooldown": 6,
        "spawns": [
            {"entity":"Bullet","direction": Vec2(1,1),"offset": Vec2(1,0)},
            {"entity":"Bullet","direction": Vec2(1,0),"offset": Vec2(1,0)},
            {"entity":"Bullet","direction": Vec2(1,-1),"offset": Vec2(1,0)},
        ]
    },
    # "JVM Inferno Staff": {
    # },
    # "Text Rain":{
    # },
    # "Formula Barrage":{
    # },
    # "Random Generator":{
    # },
    "DashToDeadline":{
        "behavior": "dash",
        "damage": 6,
        "pattern": [Vec2(1,0)],
    },
    "Exam":{
        "damage": 10,
        "behavior": "pattern",
        "pattern": [Vec2(1,0)],
    },
    "Nullptr":{
        "damage": 6,
        "behavior": "pattern",
        "pattern": [Vec2(1,0),Vec2(2,0)],
    },
    "Fireball":{
        "damage":5,#远程武器的此字段只用于展示给玩家，实际造成弹射物的伤害
        "behavior": "pn",
        "spawns":[
            {"entity":"Arrow","direction":Vec2(1,0),"offset":Vec2(1,0)},
        ]
    },
    "MultiShoot":{
        "damage":2,
        "behavior": "pn",
        "spawns": [
            {"entity":"Mana","direction": Vec2(1,1),"offset": Vec2(1,1)},
            {"entity":"Mana","direction": Vec2(-1,1),"offset": Vec2(-1,1)},
            {"entity":"Mana","direction": Vec2(1,-1),"offset": Vec2(1,-1)},
            {"entity":"Mana","direction": Vec2(-1,-1),"offset": Vec2(-1,-1)}
        ]
    },
}

behavior_registry = {
    "pattern": build_pattern_attack,
    "dash": build_dash_attack,
    "roll": build_roll_attack,
    "move": build_move,
    "mine":build_mine,
    "pn" : build_pn,
}

