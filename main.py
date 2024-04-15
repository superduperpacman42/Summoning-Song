import pygame
import os
import asyncio
import random

from loader import Loader
import birdcall
from bird import Bird


class Game:

    def __init__(self, name="Summoning Song", size=(1000, 700), pos=(0, 30), fps=60, ticks_per_frame=1):
        self.name = name
        self.size = size
        self.pos = pos
        self.goal = self.pos
        self.fps = fps
        self.ticks_per_frame = ticks_per_frame
        self.quit = False
        self.t = 0
        self.level = 0
        self.score = 0
        self.threshold = 0
        self.attempts = 0
        try:
            with open("device_list.txt", 'w') as file:
                file.writelines(str(birdcall.get_devices()))
            with open("config.txt") as file:
                line = file.readline()
                if line:
                    birdcall.device = int(line)
        except ValueError:
            print("Invalid device ID")
        except FileNotFoundError:
            print("Config file not found")
        except PermissionError:
            print("Could not write device_list to file")

        self.sequence = list(Bird.thresholds.keys())
        random.shuffle(self.sequence)

        self.state = "Splash"

        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = str(self.pos[0]) + ", " + str(self.pos[1])
        pygame.display.set_caption(self.name)
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_icon(Loader.image("IconSmall.png", alpha=True))

        self.bird = Bird(self.sequence[self.level])
        self.font = pygame.font.Font("fonts/Cooper Black Regular.ttf", 40)

        self.reference_transform = None
        self.song_duration = 0
        self.recording = None

        if not birdcall.init_stream():
            self.state = "Error"
        birdcall.stop()
        Loader.music("Birdsong.wav").play(loops=-1)
        pygame.mixer.music.set_volume(1)


    def run(self):
        """ Run the game asynchronously """
        asyncio.run(self._run())

    async def _run(self):
        """ Iteratively check for input, update game state, and redraw screen """
        clock = pygame.time.Clock()
        while not self.quit:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    self.key_pressed(event.key)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse_pressed(event.pos, event.button)
                if event.type == pygame.QUIT:
                    pygame.display.quit()
                    return
            dt = clock.tick(self.fps)
            for _ in range(self.ticks_per_frame):
                self.update(dt, pygame.key.get_pressed())
            self.draw(self.screen)
            pygame.display.update()
            await asyncio.sleep(0)

    def update(self, dt, keys):
        self.t += dt/1000
        self.bird.update(dt)
        if self.state == "Error":
            if int(self.t) > int(self.t - dt):
                if birdcall.init_stream():
                    self.state = "Splash"
                birdcall.stop()
        if self.state == "Loading" and self.t > 1:
            try:
                self.reference_transform, self.song_duration = birdcall.load_transform(self.bird.song())
            except:
                print("Could not load song:", self.bird.song())
                self.reference_transform, self.song_duration = birdcall.load_transform("audio/Crow1.wav")
            self.state = "Listen"
            self.t = 0
        if self.state == "Listen" and self.t > self.song_duration + 0.5:
            self.state = "Waiting"
            self.t = 0
            birdcall.init_stream()
            birdcall.start()
        if self.state == "Waiting" or self.state == "Recording":
            state, sound = birdcall.record(self.song_duration + 0.5)
            if state != self.state:
                self.t = 0
            self.state = state
            self.recording = sound
            if self.state == "Finished":
                self.t = 0
                birdcall.stop()
                transform = birdcall.get_transform(self.recording)
                self.score = birdcall.compare_transforms(transform, self.reference_transform)
                self.threshold = self.bird.threshold()
                self.attempts += 1
                print(f"{self.bird.name}-{self.bird.progress} ({self.attempts}): {round(self.score * 100)}% (goal = {round(self.threshold * 100)}%)")
                self.state = "Loading"
                handicap = (self.attempts - 3) * 0.05
                if self.score > self.threshold or (self.attempts >= 5 and self.score + handicap > self.threshold):
                    self.attempts = 0
                    if self.bird.advance():
                        self.state = "Complete"
                        Loader.sound("Complete").play()
                    else:
                        Loader.sound("Success").play()
                else:
                    Loader.sound("Fail").play()
        if self.state == "Complete" and self.t > 2.5:
            self.level += 1
            self.score = 0
            self.state = "Loading"
            if len(self.sequence) <= self.level:
                self.state = "Victory"
                self.level = 0
                Loader.music("Birdsong.wav").play(loops=-1)
            self.bird = Bird(self.sequence[self.level])
        if self.state == "Victory":
            if int(self.t * 100) != int(self.t * 100 - dt / 10):
                if random.randint(1, 20) == 1:
                    bird = random.choice(list(Bird.thresholds.keys()))
                    n = random.randint(1, 3)
                    Loader.sound(f"{bird}{n}").play()

    def draw(self, surface):
        surface.blit(Loader.image("Background", colorkey=None), (0, 0))

        if self.state == "Splash" or self.state == "Error":
            surface.blit(Loader.image("Splash", alpha=True), (0, 0))
            if self.t % 1 > 0.5:
                if self.state == "Splash":
                    start = self.font.render("Press any key to begin", True, (255, 255, 255))
                else:
                    start = self.font.render("Microphone not detected", True, (255, 255, 255))
                surface.blit(start, (self.size[0]/2 - start.get_width()/2, self.size[1] - start.get_height() - 30))
            return
        if self.state == "Victory":
            surface.blit(Loader.image("Victory", alpha=True), (0, 0))
            thanks = self.font.render("Thanks for playing!", True, (255, 255, 255))
            surface.blit(thanks, (self.size[0]/2 - thanks.get_width()/2, self.size[1] - thanks.get_height()*2 - 60))
            if self.t % 1 > 0.5:
                start = self.font.render("Press any key to play again", True, (255, 255, 255))
                surface.blit(start, (self.size[0]/2 - start.get_width()/2, self.size[1] - start.get_height() - 30))
            return

        self.bird.draw(surface)
        
        if self.state == "Listen" or self.state == "Loading" or self.state == "Complete":
            ear = Loader.image("Ear", alpha=True, scale=0.5)
            ear.set_alpha(abs((self.t+.75)%1.5 - .75) * 200 + 55 if self.state == "Listen" else 55)
            if self.score == 0 or self.state == "Listen":
                surface.blit(ear, (500 - ear.get_width() / 2, 570))
                feedback = "Listen"
            elif self.score - 0.05 > self.threshold:
                feedback = "Perfect!"
            elif self.score > self.threshold:
                feedback = "Success"
            elif self.attempts == 0 and self.score < self.threshold:
                feedback = "Good enough"
            elif self.score + 0.05 > self.threshold:
                feedback = "Almost there!"
            elif self.score + 0.1 > self.threshold:
                feedback = "Not quite"
            elif self.score + 0.15 > self.threshold:
                feedback = "Listen carefully"
            else:
                feedback = "Try again"
            text = self.font.render(feedback, True, (255, 255, 255))
            surface.blit(text, (self.size[0]/2 - text.get_width()/2, self.size[1] - ear.get_height() - text.get_height() - 30))

        if self.state == "Waiting" or self.state == "Recording":
            mic = Loader.image("Microphone", alpha=True, scale=0.5)
            mic.set_alpha(abs((self.t+.75)%1.5 - .75) * 200 + 55 if self.state == "Recording" else 55)
            if self.state == "Recording" or self.t > 0.2:
                surface.blit(mic, (500 - mic.get_width()/2, 570))
                text = self.font.render("Respond", True, (255, 255, 255))
                surface.blit(text, (self.size[0]/2 - text.get_width()/2, self.size[1] - mic.get_height() - text.get_height() - 30))

        watcher = Loader.image("Watcher", alpha=True)
        surface.blit(watcher, (0, self.size[1] - watcher.get_height()))

    def key_pressed(self, key):
        if key <= 255 and (self.state == "Splash" or self.state == "Victory"):
            self.state = "Loading"
            self.t = -1
            pygame.mixer.music.fadeout(1000)
        # else:
        #     if self.bird.advance():
        #         self.state = "Complete"
        #         birdcall.stop()
        #         self.t = 0

    def mouse_pressed(self, pos, button):
        pass


if __name__ == "__main__":
    g = Game()
    g.run()
