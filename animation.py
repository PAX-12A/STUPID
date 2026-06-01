from util import *
from grid import Vec2
from statemachine import *

class AnimationController:
    def __init__(self, pawn):
        self.pawn = pawn
        self.current = None
        self.default = None

    def play(self, anim):
        self.current = anim
        anim.reset()

    def update(self, dt):
        if self.current:
            finished = self.current.update(dt)
            if finished:
                self.current = None

    def get_frame(self):
        if self.current:
            return self.current.get_frame()
        elif self.default:
            return self.default.get_frame()
        return self.pawn.get_sprite()
    
class FrameAnimation:
    def __init__(self, frames, speed=0.1, loop=False):
        self.frames = frames
        self.speed = speed
        self.loop = loop
        self.time = 0
        self.index = 0
        self.finished = False

    def reset(self):
        self.time = 0
        self.index = 0

    def update(self, dt):
        if self.finished:
            return True
        self.time += dt
        if self.time >= self.speed:
            self.time = 0
            self.index += 1

            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.finished = True

        return False

    def get_frame(self):
        if not self.frames : return None
        return self.frames[min(self.index, len(self.frames) - 1)]
    
class MoveAnimation:

    def __init__(self, frames , pawn, start_tile, end_tile, duration=0.1):

        self.pawn = pawn
        self.frames = frames

        self.start = Vec2(start_tile.x,start_tile.y)
        self.end = Vec2(end_tile.x,end_tile.y)

        self.duration = duration
        self.time = 0
        self.finished = False

    def reset(self):
        self.time = 0

    def update(self, dt):

        if self.finished:
            return True

        self.time += dt

        t = min(self.time / self.duration, 1)

        # 线性插值
        x = self.start.x + (self.end.x - self.start.x) * t
        y = self.start.y + (self.end.y - self.start.y) * t

        self.pawn.render_pos = Vec2(x, y)

        if t >= 1:
            self.finished = True

        return False

    def get_frame(self):
        return self.pawn.get_sprite()
    

class ScanDeathAnimation:

    def __init__(self, sprite, block_size=4, speed=0.02):

        self.sprite = sprite
        self.block_size = block_size
        self.speed = speed

        self.time = 0

        self.w = sprite.get_width()
        self.h = sprite.get_height()

        self.cols = self.w // block_size
        self.rows = self.h // block_size

        self.total_blocks = self.cols * self.rows

        self.current_block = 0

        self.finished = False

    def reset(self):
        self.time = 0

    def update(self, dt):

        if self.finished:
            return

        self.time += dt

        if self.time >= self.speed:

            self.time = 0

            self.current_block += 1

            if self.current_block >= self.total_blocks:

                self.finished = True

    def get_frame(self):

        frame = self.sprite.copy()

        for i in range(self.current_block):

            row = i // self.cols
            col = i % self.cols

            rect = pygame.Rect(
                col * self.block_size,
                row * self.block_size,
                self.block_size,
                self.block_size
            )

            frame.fill(
                (0, 0, 0, 0),
                rect
            )

        return frame
    

