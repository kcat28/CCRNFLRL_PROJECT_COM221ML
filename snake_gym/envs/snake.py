import pygame
import sys
import time
import random
from snake_gym.envs.modules import *
from pygame.locals import *
import numpy as np


class SnakeGame(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        self.surface = pygame.Surface(self.screen.get_size())
        self.surface = self.surface.convert()
        self.surface.fill((255, 255, 255))
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.done = False

        pygame.key.set_repeat(1, 40)

        self.screen.blit(self.surface, (0, 0))
        self.fpsClock = pygame.time.Clock()

        self.snake = Snake()
        self.apple = Apple()
        
        # Add these for proper reward tracking
        self.prev_length = 1

    def reset(self):
        """Reset the game to initial state"""
        self.done = False
        self.snake.lose()  # Reset snake
        self.apple.randomize()  # New apple
        self.prev_length = 1
        
        # Redraw the initial state
        self.surface.fill((255, 255, 255))
        self.snake.draw(self.surface)
        self.apple.draw(self.surface)
        self.screen.blit(self.surface, (0, 0))
        pygame.display.flip()
        
        return SnakeGame._get_image(self.surface)

    def step(self, key):
        """Take an action and return (state, reward, done, info)"""
        if self.done:
            return self.reset(), 0, True, {}

        # Store old head position and length for reward calculation
        old_head_x, old_head_y = self.snake.get_head_position()
        old_length = self.snake.length

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        # Map action to direction
        act = [UP, DOWN, LEFT, RIGHT]
        self.snake.point(act[key])

        # Clear screen
        self.surface.fill((255, 255, 255))

        # Try to move
        try:
            self.snake.move()
        except SnakeException:
            # Snake hit itself
            self.done = True
            state = SnakeGame._get_image(self.surface)
            return state, -10, True, {"reason": "self_collision"}

        # Check wall collision
        head_x, head_y = self.snake.get_head_position()
        if head_x < 0 or head_x >= SCREEN_WIDTH or head_y < 0 or head_y >= SCREEN_HEIGHT:
            self.done = True
            state = SnakeGame._get_image(self.surface)
            return state, -10, True, {"reason": "wall_collision"}

        # Check if apple eaten
        ate_apple = False
        if self.snake.get_head_position() == self.apple.position:
            self.snake.length += 1
            self.apple.randomize()
            ate_apple = True

        # Calculate reward
        reward = -0.01  # small step penalty for efficiency
        if ate_apple:
            reward += 10
        else:
            # Distance-based shaping: reward for moving closer, penalty for moving away
            old_distance = abs(old_head_x - self.apple.position[0]) + abs(old_head_y - self.apple.position[1])
            new_distance = abs(head_x - self.apple.position[0]) + abs(head_y - self.apple.position[1])
            if new_distance < old_distance:
                reward += 0.1  # positive reward for moving closer
            elif new_distance > old_distance:
                reward -= 0.05  # small penalty for moving away

        # Draw everything
        self.snake.draw(self.surface)
        self.apple.draw(self.surface)

        # Draw score
        font = pygame.font.Font(None, 36)
        text = font.render(str(self.snake.length), 1, (10, 10, 10))
        text_pos = text.get_rect()
        text_pos.centerx = 20
        self.surface.blit(text, text_pos)

        self.screen.blit(self.surface, (0, 0))
        state = SnakeGame._get_image(self.surface)
        pygame.display.flip()
        pygame.display.update()

        self.fpsClock.tick(self.fps + self.snake.length / 3)

        return state, reward, self.done, {}


    @staticmethod
    def _get_image(surface):
        ret = list(map(lambda x: list(x), np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH))))
        for j in range(SCREEN_HEIGHT):
            for k in range(SCREEN_WIDTH):
                ret[j][k] = surface.get_at((k, j))
        return np.array(ret)