from .gun import Gun

class AK_47(Gun):
    def __init__(self, game,headshot_damage, bodyshot_damage, path_to_default_texture, path_to_shoot_texture, path_to_sound_of_shoot, scale, changer, shoot_delay, volume,patrons, magazines):
        super().__init__(game, headshot_damage, bodyshot_damage,path_to_default_texture, path_to_shoot_texture, path_to_sound_of_shoot, scale, changer, shoot_delay, volume,patrons, magazines)
