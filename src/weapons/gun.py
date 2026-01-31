from src.player.settings import *
from random import randint

class Gun(arcade.Sprite):
    def __init__(self, game, headshot_damage, bodyshot_damage, path_to_default_texture, path_to_shoot_texture, path_to_sound_of_shoot, scale, changer, shoot_delay, volume, patrons, magazines):
        super().__init__(path_to_default_texture, scale)
        self.default_texture = arcade.load_texture(path_to_default_texture)

        self.game = game
        self.default_texture.width *= changer
        self.texture = self.default_texture
        self.volume = volume

        self.shoot_texture = arcade.load_texture(path_to_shoot_texture)
        self.shoot_texture.width *= changer

        self.bottom = 0
        self.center_x = SCREEN_WIDTH - self.texture.width // 2
        self.shoot_timer = 0
        self.shoot_delay = shoot_delay
        self.active = []
        self.shoot_sound = arcade.load_sound(path_to_sound_of_shoot)
        self.empty_magazine = arcade.load_sound('../../assets/sounds/guns/empty_magazine.mp3')
        self.reload_sound = arcade.load_sound('../../assets/sounds/guns/quick-click-reload.mp3')
        self.bodyshot_sound = arcade.load_sound('../../assets/sounds/guns/bodyshot_sound.mp3')
        self.headshot_sound = arcade.load_sound('../../assets/sounds/guns/headshot_sound.mp3')
        self.borrel_shot_sound = arcade.load_sound('../../assets/sounds/guns/borrel_onshot.mp3')
        self.shooting = False
        self.speed = 100

        self.timer = 0
        self.can_breath = True

        self.headshot_damage, self.bodyshot_damage = headshot_damage, bodyshot_damage

        self.patrons, self.magazines = patrons, magazines

        self.patrons_in_magazine = patrons

        self.reload_anim = False

    def check_hit(self, enemies_list):
        player = self.game.player
        ray_angle = player.angle


        closest_hit = None
        closest_distance = float('inf')
        hit_type = None

        for enemy in enemies_list:
            if enemy.is_dead:
                continue
            dx = enemy.x - player.x
            dy = enemy.y - player.y

            angle_to_enemy = atan2(dy, dx)
            angle_diff = abs(angle_to_enemy - ray_angle)

            if angle_diff > pi:
                angle_diff = 2 * pi - angle_diff

            if angle_diff < 0.05:
                distance = sqrt(dx * dx + dy * dy)

                if distance < closest_distance:
                    screen_hit = self.check_screen_hit(enemy, player.aim_x, player.aim_y)
                    if screen_hit:
                        closest_distance = distance
                        closest_hit = enemy
                        hit_type = screen_hit

        return closest_hit, hit_type

    def check_screen_hit(self, enemy, aim_x, aim_y):
        if (enemy.screen_x < aim_x < enemy.screen_x + enemy.proj_width and
                enemy.screen_y < aim_y < enemy.screen_y + enemy.proj_height * 0.8):
            return 'bodyshot'

        if (
                enemy.screen_x + enemy.proj_width * 0.3 < aim_x < enemy.screen_x + enemy.proj_width * 0.3 + enemy.proj_width * 0.4 and
                enemy.screen_y + enemy.proj_height * 0.8 < aim_y < enemy.screen_y + enemy.proj_height * 0.8 + enemy.proj_height // 5):
            return 'headshot'

        return None

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        self.timer += delta_time
        if self.reload_anim:
            if self.reload_anim == 1:
                if self.bottom > -200:
                    self.bottom -= delta_time * 200
                else:
                    self.reload_anim = 2
                    a = (self.patrons_in_magazine - self.patrons)
                    if self.magazines >= a:
                        self.magazines -= a
                        self.patrons += a
                    else:
                        self.patrons += self.magazines
                        self.magazines = 0
                    self.reload_sound.play(volume=0.5)
            else:
                self.bottom += delta_time * 100
                if self.bottom >= 0:
                    self.bottom = 0
                    self.center_x = SCREEN_WIDTH - self.texture.width // 2
                    self.can_breath = True
                    self.timer = 0
                    self.reload_anim = False
        elif self.shooting:
            if self.shoot_timer >= self.shoot_delay or self.shoot_timer == 0:
                if self.patrons > 0:
                    self.patrons -= 1
                    self.game.shoot += 1
                    self.shoot_sound.play(volume=self.volume)
                    hit_enemy, hit_type = self.check_hit(self.game.enemies)
                    if hit_enemy and hit_type:
                        if hit_type == 'headshot':
                            self.game.headshot += 1
                            self.headshot_sound.play(0.05) if hit_enemy.enemy_type != 'b' else self.borrel_shot_sound.play()
                        else:
                            self.game.bodyshot += 1
                            self.bodyshot_sound.play(0.05) if hit_enemy.enemy_type != 'b' else self.borrel_shot_sound.play()
                        hit_enemy.get_damage(randint(self.headshot_damage[0], self.headshot_damage[1]) if hit_type == 'headshot' else randint(self.bodyshot_damage[0], self.bodyshot_damage[1]), hit_type)
                        self.game.draw_hit_ind = True

                    self.texture = self.shoot_texture
                    self.center_x += self.speed * delta_time
                    self.bottom -= self.speed * delta_time

                else:
                    self.texture = self.default_texture
                    self.empty_magazine.play(volume=0.5)
                self.shoot_timer = 0
            else:
                self.texture = self.default_texture
            self.shoot_timer += delta_time
            self.can_breath = False

        elif self.bottom < 0 and self.center_x > SCREEN_WIDTH - self.texture.width // 2 and not self.can_breath:
            self.center_x -= self.speed * delta_time * 2
            self.bottom += self.speed * delta_time * 2

        elif not self.can_breath:
            self.bottom = 0
            self.center_x = SCREEN_WIDTH - self.texture.width // 2
            self.can_breath = True
            self.timer = 0

        else:
            self.center_x += sin(self.timer) * delta_time * 20
            self.center_y -= sin(self.timer) * delta_time * 25



        if self.texture == self.shoot_texture and not self.shooting:
            self.texture = self.default_texture

    def reload(self):
        if self.magazines > 0 and self.patrons != self.patrons_in_magazine:
            self.reload_anim = 1


