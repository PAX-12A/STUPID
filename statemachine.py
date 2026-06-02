from animation import FrameAnimation,MoveAnimation
from events import DamageEvent
from vfxsystem import SlashVFX
from grid import Vec2

HIT_FRAME = 0  # 在第几帧触发伤害

class StateMachine:
    def __init__(self, owner):
        self.owner = owner
        self.state = None

    def change(self, new_state):
        
        if self.state:
            self.state.exit() #退出旧状态

        self.state = new_state
        self.state.enter() #进入新状态

    def update(self, dt):
        if self.state:
            self.state.update(dt)

class State:
    def __init__(self, pawn):
        self.pawn = pawn

    def enter(self):
        pass

    def update(self, dt):
        pass

    def exit(self):
        pass

class IdleState(State):

    def enter(self):
        self.anim = FrameAnimation(self.pawn.idle_frames, 0.2 ,loop=True)
        self.pawn.anim.play(self.anim)

    def update(self, dt):
        pass

class AttackVisualState(State):

    def __init__(self, pawn):
        super().__init__(pawn)

        self.hit_triggered = False
        self.finished = False

    def enter(self):
        print(f"{self.pawn.name} Enter AttackVisual State")
        self.anim = FrameAnimation(
            self.pawn.attack_frames,
            speed=0.08
        )
        self.pawn.anim.play(self.anim)

    def update(self, dt):

        if self.anim.index >= HIT_FRAME and not self.hit_triggered:
            self.hit_triggered = True

        if self.anim.finished:
            self.finished = True

            self.pawn.state_machine.change(
                IdleState(self.pawn)
            )


class MoveVisualState(State):

    def __init__(self, pawn, step):

        super().__init__(pawn)

        self.step = step
        self.finished= False

    def enter(self):

        self.anim = MoveAnimation(
            self.pawn.idle_frames,
            self.pawn,
            self.step.start,
            self.step.end,
            self.step.duration
        )

        self.pawn.anim.play(self.anim)

    def update(self, dt):

        if self.anim.finished:
            self.finished = True

            self.pawn.state_machine.change(
                IdleState(self.pawn)
            )

class HitState(State):

    def enter(self):

        self.anim = FrameAnimation(
            self.pawn.hit_frames
        )

        self.pawn.anim.play(self.anim)

    def update(self, dt):

        if self.anim.update(dt):
            self.pawn.state_machine.change(
                IdleState(self.pawn)
            )
