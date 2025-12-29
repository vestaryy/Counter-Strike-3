from gun import *


class USP(Gun):
    def __init__(self, path_to_default_texture, path_to_shoot_texture, path_to_sound_of_shoot, scale, changer, shoot_delay, volume):
        super().__init__(path_to_default_texture, path_to_shoot_texture, path_to_sound_of_shoot, scale, changer, shoot_delay, volume)
