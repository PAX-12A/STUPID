from grid import Vec2
from statemachine import *
from Damage import *
from entity import EntityFactory


class Action:

    def __init__(self, actor ,turn_consumed = False):
        self.actor = actor
        self.turn_consumed = turn_consumed #是否花费玩家回合

    def start(self, scene):
        pass

    def update(self, scene, dt):
        pass

    def is_finished(self):
        raise NotImplementedError

class WaitAction(Action):
    def __init__(self, actor):
        super().__init__(actor,turn_consumed=True)
    def start(self, scene):
        print("waiting")
        return
    def is_finished(self):
        return True

class MoveAction(Action):

    def __init__(self, actor, offset):

        super().__init__(actor,turn_consumed=True)

        self.offset = offset
        self.finished = False

    def start(self, scene):

        old_pos = self.actor.position
        new_pos = old_pos + self.offset

        result = self.actor.move(self.offset) # 逻辑移动

        if result is None:

            self.turn_consumed = False
            self.finished = True

            return

        # Timeline
        step = TimelineStep(
            actor_id=self.actor.actor_id,
            step_type="move",

            start=old_pos,
            end=new_pos,

            duration=0.1
        )

        scene.timeline.append(step)

        # 视觉动画
        self.state = MoveVisualState(self.actor,step)
        self.actor.state_machine.change(self.state)

        # Trap
        trap = scene.mymap.get_trap(new_pos)

        if trap:
            trap.on_enter(self.actor)

    def update(self, scene, dt):

        if hasattr(self,"state") and self.state.finished:
            self.finished = True

    def is_finished(self):
        return self.finished
    
class GravityAction(Action):

    def __init__(self, actor):

        super().__init__(actor)

        self.finished = False

    def start(self, scene):

        old_pos = self.actor.position
        new_pos = old_pos

        new_pos = old_pos + Vec2(0,1)
        self.actor.position = new_pos
        if scene.mymap.is_walkable(new_pos):
            scene.events.push(DamageEvent(None,self.actor,1)) #test,临时模拟摔落伤害

        step = TimelineStep(
            actor_id=self.actor.actor_id,
            step_type="fall",
            start=old_pos,
            end=new_pos,
            duration=0.05
        )

        scene.timeline.append(step)

        # 视觉动画
        self.state = MoveVisualState(self.actor,step)
        self.actor.state_machine.change(self.state)

    def update(self, scene, dt):

        if not self.actor.alive:#临时，保证不卡死
            self.finished = True
            return

        if self.state.finished:
            self.finished = True

    def is_finished(self):
        return self.finished

class AttackAction(Action):

    def __init__(self, actor, weapon, attack_positions ,damage):
        super().__init__(actor)

        self.weapon = weapon
        self.damage = damage
        self.attack_positions = attack_positions
        self.finished = False
        self.hit_done = False

    def start(self, scene):

        print(f"{self.actor} triggers AttackAction,pos:{self.actor.position.x},{self.actor.position.y}")

        self.state = AttackVisualState(self.actor)

        self.actor.state_machine.change(self.state)

    def update(self, scene, dt):

        if self.state.hit_triggered and not self.hit_done:

            self.hit_done = True

            for pos in self.attack_positions:

                target = scene.get_pawn_at(pos)

                if target:

                    self.actor.events.push(
                        DamageEvent(
                            self.actor,
                            target,
                            self.damage
                        )
                    )

                    self.actor.vfx.add(
                        SlashVFX(
                            self.actor.slash_frames,
                            target.position,
                            self.actor.direction
                        )
                    )

        if self.state.finished:
            self.finished = True

    def is_finished(self):     
        return self.finished
    
class MineAction(Action):
    def __init__(self, actor , weapon):
        super().__init__(actor)
        self.finished = False
        self.weapon= weapon

    def start(self, scene):
        for pt in self.weapon.pattern :
            scene.mymap.destroy_tile(self.actor.position + pt)
        self.finished = True

    def is_finished(self):
        return self.finished


    
class ParallelAction(Action):

    def __init__(self, actor, actions):

        super().__init__(actor)

        self.actions = actions

    def start(self, scene):

        for action in self.actions:
            action.start(scene)

    def update(self, scene, dt):

        for action in self.actions:
            action.update(scene, dt)

    def is_finished(self):

        return all(
            action.is_finished()
            for action in self.actions
        )
    
class SequenceAction(Action):

    def __init__(self, actor, generator):

        super().__init__(actor)

        self.generator = generator
        self.current_action = None
        self.finished = False

    def start(self, scene):
        self.advance(scene)

    def advance(self, scene):

        try:
            self.current_action = next(self.generator)

            self.current_action.start(scene)

        except StopIteration:
            self.finished = True

    def update(self, scene, dt):

        if self.finished:
            return
        
        self.current_action.update(scene, dt)

        if self.current_action.is_finished():

            self.advance(scene)

    def is_finished(self):

        return self.finished
    
class WeaponSequenceAction(Action):

    def __init__(self, actor, weapon_generator):

        super().__init__(actor)

        self.weapon_generator = weapon_generator
        self.current_action = None
        self.finished = False
    
    def start(self, scene):

        self.advance(scene)

    def advance(self, scene):

        try:

            weapon = next(self.weapon_generator)
            
            base = int(weapon.damage*self.actor.damage_multiplier)
            damage = Damage(base)

            if self.actor.actor_id == 0 :# 玩家

                if "DDL_fever" in self.actor.enabled_damage_decorators:

                    damage = DDLFeverDecorator(
                        damage,
                        self.actor
                    )
            # 这里weapon 自己生成 sequence
            weapon_actions = weapon.build_actions(scene,self.actor)

            self.current_action = SequenceAction(
                self.actor,
                iter(weapon_actions)
            )

            self.current_action.start(scene)

        except StopIteration:

            self.finished = True

    def update(self, scene, dt):

        if self.finished:
            return

        self.current_action.update(scene, dt)

        if self.current_action.is_finished():

            self.advance(scene)

    def is_finished(self):

        # scene.process_reactions()

        return self.finished



import json   
class TimelineStep:

    def __init__(self,actor_id,step_type,start,end,duration=0.15,):

        self.actor_id = actor_id
        self.step_type = step_type

        self.start = start
        self.end = end

        self.duration = duration

    
    def to_dict(self):

        return {
            "actor_id": self.actor_id,
            "step_type": self.step_type,

            "start": [
                self.start.x,
                self.start.y
            ],

            "end": [
                self.end.x,
                self.end.y
            ],

            "duration": self.duration
        }
    
# class SpawnEntityAction(Action):

#     def __init__(self, actor, projectile_type , damage ,direction:Vec2 ,lifetime = 5 , offset = None , speed = 1):
#         super().__init__(actor)

#         self.projectile_type = projectile_type
#         self.damage = damage
#         self.direction = direction
#         self.lifetime = lifetime
#         self.offset = offset if offset is not None else actor.position
#         self.speed = speed

#     def start(self,scene):
#         projectile_cls = projectile_registry[self.projectile_type]

#         projectile = projectile_cls(
#             scene = scene,
#             projectile_type = self.projectile_type,
#             position = self.actor.position + self.offset,
#             direction= self.direction,
#             lifetime = self.lifetime,
#             damage = self.damage,
#             speed = self.speed
#         )

#         scene.projectiles.append(projectile)

#         self.finished = True
    
#     def is_finished(self):
#         return True

class SpawnEntityAction(Action):

    def __init__(self,actor,entity_type,direction,offset=None,config=None):
        super().__init__(actor)

        self.entity_type = entity_type
        self.direction = direction
        self.offset = offset if offset else Vec2(0,0)
        self.config = config

    def start(self,scene):

        entity = EntityFactory.create(
            scene=scene,
            entity_type=self.entity_type,
            position=self.actor.position+self.offset,
            direction=self.direction,
            config=self.config
        )

        scene.projectiles.append(entity)

        self.finished = True

    def is_finished(self):
        return True

class PlayerEndTurnAction(Action):

    def start(self, scene):

        scene.end_player_turn()

        scene.input_locked = False

        self.finished = True
    
    def is_finished(self):
        return self.finished

