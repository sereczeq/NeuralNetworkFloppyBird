import pygame
from sys import exit
import random
import ctypes
import time
import numpy


# 4 inputs - current height, speed, distance to next wall, height of next wall


def sigmoid(x):
    x /=1000
    return 1 / (1 + numpy.exp(-x))


class Neuron:
    def __init__(self, bird):
        self.weights = numpy.zeros(4)
        self.bird = bird
        for i in range(4):
            self.weights[i] = random.random()
            if random.random() > 0.5:
                self.weights[i] *= -1
        self.learning_rate = 0.2
        self.random = 0.9

    def calculate(self, inputs):
        x = numpy.dot(self.weights, inputs)
        return sigmoid(x)

    def correct(self, bird):
        if random.random() > self.random or bird is None:
            for i in range(4):
                self.weights[i] = random.random()
                if random.random() > 0.5:
                    self.weights[i] *= -1
        else:
            for i in range(len(self.weights)):
                self.weights[i] += (bird.neuron.weights[i] - self.weights[i]) * self.learning_rate#((bird.score - self.bird.score)/bird.score) * self.learning_rate


class Bird:
    def __init__(self, position, size, screen, screen_height, color=(100, 0, 100)):
        self.speed = 0
        self.rect = pygame.Rect(position, size)
        self.initial_position = self.rect.y
        self.screen = screen
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.score = time.time()
        self.alive = True
        self.neuron = Neuron(self)
        self.screen_height = screen_height

    def jump(self):
        self.speed = -15

    def update(self, walls, wall):
        if self.alive:
            if self.should_kill(walls):
                self.die()
                return
            self.decide(wall)
            self.speed += 1
            self.speed = min(self.speed, 15)
            pygame.draw.rect(self.screen, self.color, self.rect)
            self.rect.y += self.speed

    def die(self):
        self.alive = False
        self.rect.y = self.initial_position
        self.score = time.time() - self.score

    def resurrect(self):
        self.score = time.time()
        self.alive = True

    def should_kill(self, walls):
        if self.rect.top < 0 or self.rect.bottom > self.screen_height:
            return True
        if walls is not None:
            for wall in walls:
                if pygame.Rect.colliderect(self.rect, wall):
                    return True
        return False

    def decide(self, wall):
        inputs = (self.rect.bottom,
                  self.speed,
                  600 if wall is None else wall.top,
                  1920 if wall is None else wall.right)
        value = self.neuron.calculate(inputs)
        if value < 0.4:
            self.jump()


class Walls:
    def __init__(self, screen_width, screen_height, screen, color=(0, 255, 100)):
        self.walls = []
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = screen
        self.color = color

    def update(self):

        for wall in self.walls:
            if wall.right < 0:
                self.walls.remove(wall)

        for wall in self.walls:
            wall.x -= 5
            pygame.draw.rect(self.screen, self.color, wall)

    def create(self):
        gap = 300
        height = random.randint(100, self.screen_height - 100 - gap)
        wall1 = pygame.Rect(self.screen_width + 5, 0, 70, height)
        self.walls.append(wall1)
        wall2 = pygame.Rect(self.screen_width + 5, height + gap, 70, self.screen_height)
        self.walls.append(wall2)


class Game:

    def __init__(self, number_of_players=1):
        self.clock = pygame.time.Clock()
        self.size = 60
        self.birds = []
        self.number_of_players = number_of_players
        self.FPS = 60

        # Initialize game
        pygame.init()
        pygame.display.set_caption("Floppy Bird")
        # setting display correctly from
        # https://gamedev.stackexchange.com/questions/105750/pygame-fullsreen-display-issue
        ctypes.windll.user32.SetProcessDPIAware()
        true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
        self.screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN)
        self.screen_width, self.screen_height = pygame.display.get_surface().get_size()
        self.initialize_birds()
        self.walls = Walls(self.screen_width, self.screen_height, self.screen)
        self.CREATEWALL = pygame.USEREVENT + 1
        pygame.time.set_timer(self.CREATEWALL, 100)

        self.play()

    def initialize_birds(self):
        position = (int(self.screen_width / 5 - self.size / 2), int(self.screen_height / 2 - self.size / 2))
        for _ in range(self.number_of_players):
            bird = Bird(position, (self.size, self.size), self.screen, self.screen_height)
            self.birds.append(bird)

    def play(self):
        while True:
            self.screen.fill((0, 0, 0))
            self.walls.update()

            self.check_for_alive_birds()

            wall = self.closest_wall()
            for bird in self.birds:
                bird.update(self.walls.walls, wall)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    for bird in self.birds:
                        print(bird.neuron.weights)
                    pygame.quit()
                    exit()
                if event.type == self.CREATEWALL:
                    self.walls.create()
                    pygame.time.set_timer(self.CREATEWALL,  int(60.0 / self.FPS * 1000) * random.randint(2, 5))
                # just testing
                if event.type == pygame.KEYDOWN:
                    for bird in self.birds:
                        bird.jump()

            pygame.display.update()
            self.clock.tick(self.FPS)

    def check_for_alive_birds(self):
        end_game = True
        for bird in self.birds:
            if end_game:
                if bird.alive:
                    end_game = False
        if end_game:
            self.finish()

    # choose the best and follow him
    def finish(self):
        pygame.time.set_timer(self.CREATEWALL, 0)
        self.walls.walls = []
        max_score = 0
        min_score = 100
        max_bird = None
        for bird in self.birds:
            if bird.score > max_score:
                max_bird = bird
                max_score = bird.score
            if bird.score < min_score:
                min_score = bird.score
        if max_score - min_score < 0.5:
            max_bird = None
        for bird in self.birds:
            bird.neuron.correct(max_bird)
            bird.resurrect()
        pygame.time.set_timer(self.CREATEWALL, 100)

    def closest_wall(self):
        bird = self.birds[0]
        closest_distance = 1920
        closest_wall = None
        for wall in self.walls.walls:
            distance = wall.right - bird.rect.left
            if 0 < distance <= closest_distance and wall.y > 20:
                closest_distance = distance
                print(closest_distance)
                closest_wall = wall
        if closest_wall is not None:
            pygame.draw.rect(self.screen, (100, 100, 100), closest_wall)
        return closest_wall

game = Game(100)
