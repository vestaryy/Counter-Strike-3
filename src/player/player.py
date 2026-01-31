from src.player.settings import *
from random import randint, choice
import time


class Player:
    def __init__(self, x, y):
        self.x = x + block_size // 2
        self.y = y + block_size // 2
        self.keys_pressed = set()
        self.ver_a = 0
        self.angle = 0
        self.aim_x = SCREEN_WIDTH // 2
        self.aim_y = SCREEN_HEIGHT // 2
        self.speed = 150
        self.current_gun_list = arcade.SpriteList()
        self.health = 100
        self.damage_indicator_angle = None
        self.damage_indicator_timer = 0
        self.damage_indicator_duration = 1.0
        self.last_damage_time = 0
        self.wound_sound1 = arcade.load_sound('../../assets/sounds/guns/wound1.mp3')
        self.wound_sound2 = arcade.load_sound('../../assets/sounds/guns/wound2.mp3')
        self.wound_sound3 = arcade.load_sound('../../assets/sounds/guns/wound3.mp3')
        self.get_damage_music = None

    def get_damage(self, enemy, damage):
        self.health -= (damage - randint(1, 5))
        self.get_damage_music = choice([self.wound_sound1, self.wound_sound2, self.wound_sound3]).play()
        dx = self.x - enemy.x
        dy = self.y - enemy.y
        self.damage_indicator_angle = atan2(dy, dx) + pi
        self.damage_indicator_timer = self.damage_indicator_duration
        self.last_damage_time = time.time()