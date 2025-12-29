import arcade
from math import *
SCREEN_WIDTH = int(arcade.get_screens()[0].width // 1.25)
SCREEN_HEIGHT = int(arcade.get_screens()[0].height // 1.25)
SCREEN_TITLE = "CS 3"

block_size = 100
FOV = pi / 2
half_FOV = FOV / 2
max_depth = SCREEN_WIDTH // 100
num_rays = SCREEN_WIDTH // 3
delta_ray = FOV / (num_rays - 1)
ray_size = SCREEN_WIDTH
dist = num_rays / (2 * tan(half_FOV))
scale = SCREEN_WIDTH // num_rays
coefficent = dist * 150 * scale
half_height = SCREEN_HEIGHT / 2
dep_coeff = 2