import arcade
from math import *
from settings import *


class Gun(arcade.Sprite):
    def __init__(self, path_to_default_texture, path_to_shoot_texture, path_to_sound_of_shoot, scale, changer, shoot_delay, volume):
        super().__init__(path_to_default_texture, scale)
        self.default_texture = arcade.load_texture(path_to_default_texture)
        self.default_texture.width *= changer
        self.texture = self.default_texture
        self.volume = volume

        self.shoot_texture = arcade.load_texture(path_to_shoot_texture)
        self.shoot_texture.width *= changer

        self.bottom = 0
        self.right = SCREEN_WIDTH
        self.shoot_timer = 0
        self.shoot_delay = shoot_delay
        self.active = []
        self.shoot_sound = arcade.load_sound(path_to_sound_of_shoot)
        self.shooting = False
        self.speed = 100

        self.timer = 0
        self.can_breath = True


    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        self.timer += delta_time
        if self.shooting:
            if self.shoot_timer >= self.shoot_delay or self.shoot_timer == 0:
                self.shoot_sound.play(volume=self.volume)
                self.texture = self.shoot_texture
                self.right += self.speed * delta_time
                self.bottom -= self.speed * delta_time
                self.shoot_timer = 0
            else:
                self.texture = self.default_texture
            self.shoot_timer += delta_time
            self.can_breath = False

        elif self.bottom < 0 and self.right > SCREEN_WIDTH and not self.can_breath:
            self.right -= self.speed * delta_time * 2
            self.bottom += self.speed * delta_time * 2

        elif not self.can_breath:
            self.bottom = 0
            self.right = SCREEN_WIDTH
            self.can_breath = True
            self.timer = 0
        else:
            self.center_x += sin(self.timer) * delta_time * 10
            self.center_y -= sin(self.timer) * delta_time * 15

        if self.texture == self.shoot_texture and not self.shooting:
            self.texture = self.default_texture

