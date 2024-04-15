from loader import Loader
import random, math


class Bird:

    spawn_locs = ((485, 28), (45, 95), (385, 180), (635, 157), (875, 70), (130, 180))
    thresholds = {"Crow": (0.65, 0.65, 0.65), "Owl": (0.5, 0.5, 0.4), "Parrot": (0.65, 0.65, 0.55),
                  "BlueJay": (0.5, 0.5, 0.5), "Robin": (0.4, 0.5, 0.65), "Woodpecker": (0.5, 0.5, 0.5),
                  "Eagle": (0.65, 0.65, 0.65), "Goose": (0.65, 0.65, 0.65), "Seagull": (0.65, 0.65, 0.65)}
    speed = 300

    def __init__(self, name, scale=0.2):
        self.name = name
        pos = self.spawn_locs[random.randint(0, len(self.spawn_locs)-1)]
        self.pos = [pos[0] + 22.5, pos[1] + 45]
        self.goal = self.pos
        self.set_scale(scale)
        self.t = 0
        self.progress = 1
        self.hop = 0

    def set_scale(self, scale):
        self.scale = scale
        self.image = Loader.image(self.name, alpha=True, scale=scale)
        self.size = self.image.get_size()

    def update(self, dt):
        self.t += dt
        if abs(self.pos[0] - self.goal[0]) > self.speed * dt/1000:
            self.hop += 5 * dt/1000
            slope = abs((self.pos[1] - self.goal[1]) / (self.pos[0] - self.goal[0]))
            self.pos[1] += math.copysign(self.speed * slope * dt/1000, self.goal[1] - self.pos[1])
            self.pos[0] += math.copysign(self.speed * dt/1000, self.goal[0] - self.pos[0])
            if self.hop >= 1:
                self.hop = 0
        else:
            self.hop = 0

    def advance(self):
        self.progress += 1
        self.set_scale(1)
        if self.progress == 2:
            self.pos = [1000+self.size[0], 650]
            self.goal = (900, 650)
        if self.progress == 3:
            self.goal = (700, 680)
        if self.progress == 4:
            self.goal = (350, 650)
        return self.progress > len(self.thresholds[self.name])

    def song(self):
        return f"audio/{self.name}{self.progress}.wav"

    def threshold(self):
        return self.thresholds[self.name][self.progress - 1] 

    def draw(self, surface):
        """
        Draw the sprite and its children on the given surface

        :param surface:
        :return:
        """
        h = 20
        dy = (1 - 4*(self.hop - 0.5)**2) * h
        surface.blit(self.image, (self.pos[0] - self.size[0]/2, self.pos[1] - self.size[1] - dy))
