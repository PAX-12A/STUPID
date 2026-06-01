from animation import *
class VFXSystem:

    def __init__(self,camera):
        self.effects = []
        self.camera = camera

    def add(self, effect):
        self.effects.append(effect)

    def update(self, dt):

        for effect in self.effects[:]:

            finished = effect.update(dt)

            if finished:
                self.effects.remove(effect)

    def draw(self, screen):

        for effect in self.effects:
            effect.draw(screen, self.camera) 

class VFX:

    def update(self, dt):
        return False

    def draw(self, screen):
        pass

class SlashVFX(VFX):

    def __init__(self, frames, center_pos, direction):

        self.anim = FrameAnimation(frames,speed=0.06,loop=False)
        self.center_pos = center_pos
        self.direction = direction

    def update(self, dt):
        return self.anim.update(dt)

    def draw(self, screen , camera):

        img = self.anim.get_frame()

        if self.direction == -1:
            img = pygame.transform.flip(img, True, False)

        render_1bit_sprite(screen, img, camera.apply(self.center_pos), RED)