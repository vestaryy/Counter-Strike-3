from pyglet.graphics import Batch
from random import choice
from src.entities.enemy import *
from src.entities.pathfinding import *
from src.weapons.USP import *
from src.weapons.AKR import *
import time
from src.views.main_menu import *
from src.player.player import Player


class Training(arcade.View):
    def __init__(self):
        super().__init__()
        self.kalash = None
        self.usp = None
        self.player = None
        self.enemies = []
        self.wall_batch = None
        self.texture_slices = {}
        self.manager = None
        self.player_moved = False
        self.draw_key = False
        self.draw_hit_ind = False
        self.sky_offset = 0
        self.timer_steps = 0
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        self.times_of_day = 17
        self.light_coeff = 0.000001

    def on_show_view(self):
        self.shoot = 0
        self.headshot = 0
        self.bodyshot = 0
        self.kalash = AK_47(self, [100, 120], [28, 30], '../../assets/textures/guns/AK-47/ak-47.png',
                            '../../assets/textures/guns/AK-47/ak-47_shoot.png',
                            '../../assets/sounds/guns/AK-47/ak47_shoot.wav', 1.3, 1.5, 0.15, 0.15, 30, float('inf'))

        self.usp = USP(self, [90, 110], [15, 25], '../../assets/textures/guns/USP/usp.png',
                       '../../assets/textures/guns/USP/usp_shoot.png',
                       '../../assets/sounds/guns/USP/usp_shoot.wav',
                       2, 1.5, 0.3, 0.1, 12, float('inf'))

        self.window.set_mouse_position(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.batch = Batch()

        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        self.manager = UIManager(self.window)
        self.manager.enable()

        self.fps = UILabel(text="0",
                           font_size=20,
                           text_color=arcade.color.GREEN,
                           width=300,
                           align="right")

        self.patrons = UILabel(text="0/0",
                               font_size=20,
                               text_color=arcade.color.GREEN,
                               width=300,
                               align="right")

        self.health = UILabel(text="100",
                              font_size=20,
                              text_color=arcade.color.RED,
                              width=300,
                              align="left")

        self.fps_anchor = UIAnchorLayout()

        self.fps_anchor.add(
            child=self.health,
            anchor_x="left",
            anchor_y="bottom",
            align_x=20,
            align_y=20
        )

        self.fps_anchor.add(
            child=self.fps,
            anchor_x="right",
            anchor_y="top",
            align_x=-20,
            align_y=-20
        )

        self.fps_anchor.add(
            child=self.patrons,
            anchor_x="right",
            anchor_y="bottom",
            align_x=-20,
        )

        self.manager.add(self.fps_anchor)
        self.player_moved = False
        self.window.set_mouse_visible(False)

        self.draw_key = False
        self.draw_hit_ind = False

        self.usp_list = arcade.SpriteList()
        self.usp_list.append(self.usp)
        self.kalash_list = arcade.SpriteList()
        self.kalash_list.append(self.kalash)

        self.wall_textures = {
            'W': arcade.load_texture('../../assets/textures/sky&walls/old_soviet.png'),
            'B': arcade.load_texture('../../assets/textures/sky&walls/old_soviet2.png')
        }

        self.enemies_textures = {
            '1': {'default': arcade.load_texture('../../assets/textures/mannequin/default.png'),
                  'walk1': arcade.load_texture('../../assets/textures/mannequin/default.png'),
                  'walk2': arcade.load_texture('../../assets/textures/mannequin/default.png'),
                  'headshot': arcade.load_texture('../../assets/textures/mannequin/default.png'),
                  'bodyshot': arcade.load_texture('../../assets/textures/mannequin/default.png'),
                  'death': arcade.load_texture('../../assets/textures/enemy1pack/death.png'),
                  'shoot': arcade.load_texture('../../assets/textures/mannequin/default.png')
                  }
        }

        self.enemies_settings = {
            '1': {'can_attack': False, 'can_move': False},
        }

        Enemies.precompute_texture_slices_for_all_enemies(self.enemies_textures)

        self.enemies = []

        self.times_of_day = 17
        self.wall_batch = arcade.SpriteList()
        self.texture_slices = {}

        for let, texture in self.wall_textures.items():
            self.texture_slices[let] = []
            for x in range(block_size):
                self.texture_slices[let].append(texture.crop(x * (texture.width / block_size), 0, 1, texture.height))

        self.block_size = 100
        self.text_map = [
            'WWWWWWWWWWWWWWWWWWW',
            'W..1............1.W',
            'W........1........W',
            'W....1............W',
            'W.............1...W',
            'W..1.......1......W',
            'W.................W',
            'WWWWWW.......WWWWWW',
            'W.................W',
            'W.................W',
            'W........P........W',
            'WWWWWWWWWBWWWWWWWWW',
        ]

        self.map_width, self.map_height = len(self.text_map[0]), len(self.text_map)
        self.map_textures = {}
        self.block_map = set()

        self.radar = set()
        self.radar_scale = 10

        self.pathfinding = PathFinding(self)

        f = False
        ybp = 0
        for row in self.text_map:
            if f:
                break
            xbp = 0
            for col in list(row):
                if col == 'P':
                    self.player = Player(xbp, ybp)
                    f = True
                    break
                xbp += self.block_size
            ybp += self.block_size

        ybp = 0
        for row in self.text_map:
            xbp = 0
            for col in list(row):
                if col in self.wall_textures.keys():
                    self.block_map.add((xbp, ybp))
                    self.map_textures[(xbp, ybp)] = col
                    self.radar.add((xbp // self.radar_scale, ybp // self.radar_scale))
                elif col in self.enemies_textures.keys():
                    spr = Enemies(
                        self,
                        col,
                        self.enemies_textures[col],
                        (xbp // self.block_size, ybp // self.block_size),
                        0.5,
                        0.8,
                        1,
                        self.enemies_settings[col]['can_move'],
                        self.enemies_settings[col]['can_attack'],
                        True,
                        True,
                        death_duration=5
                    )
                    spr.set_pathfinding(self.pathfinding)
                    self.enemies.append(spr)
                xbp += self.block_size
            ybp += self.block_size

        self.sky_texture = arcade.load_texture('../../assets/textures/sky&walls/sky_ala.jpg')
        self.sky_offset = 0
        self.flashlight = arcade.load_texture('../../assets/textures/sky&walls/light.png')
        self.floor_color = arcade.color.JET
        self.light_coeff = 0.000001

        self.hud_batch = Batch()
        self.button_to_press = arcade.Text(
            '''Нажмите "Е", чтобы обыскать.''',
            self.player.aim_x - 10,
            self.player.aim_y,
            arcade.color.WHITE,
            anchor_x='right',
            anchor_y='center',
            batch=self.hud_batch,
            font_name='SimSun',
            font_size=16
        )

        self.health_text = arcade.Sprite(
            arcade.make_soft_circle_texture(20, (255, 0, 0), 128),
            center_x=35,
            center_y=40
        )
        self.health_list = arcade.SpriteList()
        self.health_list.append(self.health_text)

        self.patrons_sound = arcade.load_sound(
            '../../assets/sounds/background/bullet-casing-7mm-bullets-drop-pile-cement_my8iaf4o.mp3')
        self.zip_bag = arcade.load_sound('../../assets/sounds/background/bbe1c9e31bbaee7.mp3')
        self.steps_sound = arcade.load_sound('../../assets/sounds/background/zvuk-shagov_UwwnLDOO.mp3')
        self.timer_steps = 0

        self.icons_list = arcade.SpriteList()
        self.ak_icon = arcade.Sprite('../../assets/textures/guns/AK-47/icon.png', scale=0.1)
        self.ak_icon.right = SCREEN_WIDTH - 5
        self.ak_icon.bottom = half_height + 5
        self.usp_icon = arcade.Sprite('../../assets/textures/guns/USP/icon.png', scale=0.1)
        self.usp_icon.right = SCREEN_WIDTH - 5
        self.usp_icon.top = half_height - 5
        self.icons_list.append(self.ak_icon)
        self.icons_list.append(self.usp_icon)
        self.background_music = arcade.load_sound(
            '../../assets/sounds/background/summer-summer-atmosphere.mp3').play(loop=True)

    def on_draw(self):
        self.clear()
        self.wall_batch.clear()

        def draw_sky():
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset, -self.player.ver_a, SCREEN_WIDTH, SCREEN_HEIGHT))
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset + SCREEN_WIDTH, -self.player.ver_a, SCREEN_WIDTH, SCREEN_HEIGHT)
            )
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset, -self.player.ver_a + SCREEN_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT))
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset + SCREEN_WIDTH, -self.player.ver_a + SCREEN_HEIGHT, SCREEN_WIDTH,
                                 SCREEN_HEIGHT)
            )

        def draw_radar():
            arcade.draw_rect_filled(arcade.rect.XYWH(
                self.map_width * self.block_size // self.radar_scale // 2 + 10,
                SCREEN_HEIGHT - self.map_height * self.block_size // self.radar_scale // 2 - 10,
                self.map_width * self.block_size // self.radar_scale,
                self.map_height * self.block_size // self.radar_scale),
                arcade.color.GRAY)

            map_x, map_y = (self.player.x // self.radar_scale + 10,
                            SCREEN_HEIGHT - self.player.y // self.radar_scale - 10)
            arcade.draw_circle_filled(map_x, map_y, 4, (0, 0, 255))
            arcade.draw_line(map_x, map_y, map_x + 5 * cos(-self.player.angle), map_y + 5 * sin(-self.player.angle),
                             (0, 0, 0))

            for enemy in self.enemies:
                if enemy.current_texture_name != 'death':
                    arcade.draw_circle_filled(enemy.x // self.radar_scale + 10,
                                              SCREEN_HEIGHT - enemy.y // self.radar_scale - 10, 4, (255, 0, 0))
            for x, y in self.radar:
                arcade.draw_rect_filled(
                    arcade.rect.LBWH(x + 10, SCREEN_HEIGHT - y - self.block_size // self.radar_scale - 10,
                                     self.block_size // self.radar_scale,
                                     self.block_size // self.radar_scale), (0, 0, 0))

        def draw_floor():
            arcade.draw_rect_filled(
                arcade.rect.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT // 2 - self.player.ver_a),
                arcade.color.JET
            )

        blckposd = {
            'l': self.player.x - self.player.x // self.block_size * self.block_size,
            't': self.player.y - self.player.y // self.block_size * self.block_size,
            'r': self.block_size - (self.player.x - self.player.x // self.block_size * self.block_size),
            'b': self.block_size - (self.player.y - self.player.y // self.block_size * self.block_size)
        }

        for ray in range(num_rays):
            cos_a, sin_a = cos(self.player.angle - half_FOV + delta_ray * ray), sin(
                self.player.angle - half_FOV + delta_ray * ray)
            vertical_d, horiz_d = 0, 0
            texture_v, texture_h = 0, 0

            for dep in range(self.map_width):
                if cos_a > 0:
                    vertical_d = blckposd['r'] / cos_a + block_size / cos_a * dep + 1
                elif cos_a < 0:
                    vertical_d = blckposd['l'] / -cos_a + block_size / -cos_a * dep + 1

                xv, yv = vertical_d * cos_a + self.player.x, vertical_d * sin_a + self.player.y
                index = xv // self.block_size * self.block_size, yv // self.block_size * self.block_size
                if index in self.block_map:
                    texture_v = self.map_textures[index]
                    break

            for dep in range(self.map_height):
                if sin_a > 0:
                    horiz_d = blckposd['b'] / sin_a + block_size / sin_a * dep + 1
                elif sin_a < 0:
                    horiz_d = blckposd['t'] / -sin_a + block_size / -sin_a * dep + 1

                xh, yh = horiz_d * cos_a + self.player.x, horiz_d * sin_a + self.player.y
                index = xh // self.block_size * self.block_size, yh // self.block_size * self.block_size
                if index in self.block_map:
                    texture_h = self.map_textures[index]
                    break

            if horiz_d > vertical_d:
                ray_len = vertical_d
                offset = int(yv) % self.block_size
                text_let = texture_v
            else:
                ray_len = horiz_d
                offset = int(xh) % self.block_size
                text_let = texture_h

            if text_let in self.texture_slices:
                if offset >= len(self.texture_slices[text_let]):
                    offset = len(self.texture_slices[text_let]) - 1

                ray_len = ray_len * cos(
                    self.player.angle - (self.player.angle - half_FOV + delta_ray * ray)) * dep_coeff / 1.5
                h_c = coefficent / (ray_len + 0.0000000001)


                wall = arcade.Sprite(
                    self.texture_slices[text_let][offset],
                    1,
                    ray * scale,
                    half_height - self.player.ver_a
                )
                wall.height = h_c
                wall.width = scale

                self.wall_batch.append(wall)

        draw_sky()
        draw_floor()

        visible_sprites = []
        for sprite in self.enemies:
            if sprite.visible:
                visible_sprites.append(sprite)

        visible_sprites.sort(key=lambda s: s.distance_to_player, reverse=True)

        self.wall_batch.draw()
        self.wall_batch.clear()

        for sprite in visible_sprites:
            sprite.draw()

        def hud():
            arcade.draw_rect_filled(
                arcade.rect.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
                (0, 0, 0, 255 - max(0, min(255, round(127.5 * (cos(2 * pi * (self.times_of_day % 24 - 12) / 24) + 1)))))
            )
            arcade.draw_circle_filled(self.player.aim_x, self.player.aim_y, 3, (255, 255, 255))

            if self.draw_hit_ind and self.player.current_gun_list:
                if self.player.current_gun_list[0].patrons != 0:
                    arcade.draw_line(self.player.aim_x - 10, self.player.aim_y - 10, self.player.aim_x - 5,
                                     self.player.aim_y - 5, (255, 255, 255))
                    arcade.draw_line(self.player.aim_x - 10, self.player.aim_y + 10, self.player.aim_x - 5,
                                     self.player.aim_y + 5, (255, 255, 255))
                    arcade.draw_line(self.player.aim_x + 10, self.player.aim_y - 10, self.player.aim_x + 5,
                                     self.player.aim_y - 5, (255, 255, 255))
                    arcade.draw_line(self.player.aim_x + 10, self.player.aim_y + 10, self.player.aim_x + 5,
                                     self.player.aim_y + 5, (255, 255, 255))

                    self.draw_hit_ind = False

            if self.draw_key:
                self.hud_batch.draw()

            if self.player.damage_indicator_angle is not None and self.player.damage_indicator_timer > 0:
                indicator_radius = 50
                angle_to_player = self.player.angle - self.player.damage_indicator_angle

                arcade.draw_arc_outline(
                    self.player.aim_x, self.player.aim_y,
                    indicator_radius, indicator_radius,
                    arcade.color.RED,
                    degrees(angle_to_player - 0.2),
                    degrees(angle_to_player + 0.2),
                    5, 255
                )

            if self.player.current_gun_list:
                self.player.current_gun_list.draw()

            self.health_list.draw()
            draw_radar()
            self.icons_list.draw()
            self.manager.draw()

        hud()

    def can_move_to(self, x, y):
        for i in range(8):
            a = 2 * pi * i / 8
            check_x = x + 10 * cos(a)
            check_y = y + 10 * sin(a)

            if (check_x // self.block_size * self.block_size,
                check_y // self.block_size * self.block_size) in self.block_map:
                return False
        return True

    def on_update(self, delta_time):
        if self.player is None:
            return
        self.timer_steps += delta_time
        dx, dy = 0, 0

        if self.player.current_gun_list:
            if arcade.MOUSE_BUTTON_LEFT in self.player.keys_pressed:
                self.player.current_gun_list[0].shooting = True
                self.player.speed = 100
            elif self.player.current_gun_list[0].shooting:
                self.player.current_gun_list[0].shooting = False
                self.player.speed = 150

        if arcade.key.W in self.player.keys_pressed:
            dx += cos(self.player.angle) * delta_time * self.player.speed
            dy += sin(self.player.angle) * delta_time * self.player.speed

        if arcade.key.S in self.player.keys_pressed:
            dx -= cos(self.player.angle) * delta_time * self.player.speed
            dy -= sin(self.player.angle) * delta_time * self.player.speed

        if arcade.key.A in self.player.keys_pressed:
            dx += sin(self.player.angle) * delta_time * self.player.speed
            dy -= cos(self.player.angle) * delta_time * self.player.speed

        if arcade.key.D in self.player.keys_pressed:
            dx -= sin(self.player.angle) * delta_time * self.player.speed
            dy += cos(self.player.angle) * delta_time * self.player.speed

        if dx != 0:
            if self.can_move_to(self.player.x + dx, self.player.y):
                self.player.x = self.player.x + dx
            elif self.can_move_to(self.player.x + dx * 0.3, self.player.y):
                self.player.x = self.player.x + dx * 0.3

        if dy != 0:
            if self.can_move_to(self.player.x, self.player.y + dy):
                self.player.y = self.player.y + dy
            else:
                if self.can_move_to(self.player.x, self.player.y + dy * 0.3):
                    self.player.y = self.player.y + dy * 0.3

        if (dx or dy) and self.timer_steps > 0.5:
            self.steps_player = self.steps_sound.play(volume=1.0)
            self.timer_steps = 0

        self.fps_counter += 1
        self.fps_timer += delta_time

        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
            self.fps.text = str(self.current_fps)

        if not self.window._mouse_visible:
            self.custom_mouse_motion(self.window._mouse_x, self.window._mouse_y, delta_time)

        if self.player.current_gun_list:
            self.player.current_gun_list.update(delta_time)
            self.patrons.text = f'{self.player.current_gun_list[0].patrons}/{self.player.current_gun_list[0].magazines}'

        for enemy in self.enemies:
            enemy.update(delta_time)

        self.health.text = str(self.player.health)
        self.health_list[-1].scale = max((100 - self.player.health) // 10, 1)

    def custom_mouse_motion(self, x, y, delta):
        dx = x - SCREEN_WIDTH // 2
        self.sky_offset = (self.sky_offset + dx * delta * 90) % SCREEN_WIDTH
        self.player.angle += dx * delta * 0.1

        if self.player.ver_a < -SCREEN_HEIGHT:
            self.player.ver_a = -70

        dy = y - SCREEN_HEIGHT // 2
        if dy > 0:
            if SCREEN_HEIGHT > self.player.ver_a + dy * delta * 50:
                self.player.ver_a += dy * delta * 50
        if dy < 0:
            if self.player.ver_a + dy * delta * 50 > -SCREEN_HEIGHT:
                self.player.ver_a += dy * delta * 50

        self.window.set_mouse_position(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """ Обработка нажатий кнопок мыши """
        self.player.keys_pressed.add(button)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """ Обработка отпускания кнопок мыши """
        if button in self.player.keys_pressed:
            self.player.keys_pressed.remove(button)
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.player.current_gun_list:
                self.player.current_gun_list[0].shoot_timer = 0

    def on_key_press(self, key, modifiers):
        """ Обработка нажатий клавиш """
        if not self.player_moved:
            self.player_moved = True

        if arcade.key.ESCAPE == key:
            arcade.stop_sound(self.background_music)
            from src.views.main_menu import MainMenu
            menu = MainMenu()
            self.window.set_mouse_visible(True)
            self.window.show_view(menu)

        if key == arcade.key.ENTER:
            self.add_random_enemy()

        if key == arcade.key.KEY_2:
            self.player.current_gun_list = self.usp_list

        if key == arcade.key.KEY_1:
            self.player.current_gun_list = self.kalash_list

        if key == arcade.key.R:
            if self.player.current_gun_list:
                self.player.current_gun_list[0].reload()

        if arcade.key.F1 == key:
            self.window.set_mouse_visible(not self.window._mouse_visible)

        self.player.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        """ Обработка отпускания клавиш """
        if key in self.player.keys_pressed:
            self.player.keys_pressed.remove(key)

    def add_random_enemy(self):
        row, col = randint(1, self.map_height - 6), randint(1, self.map_width - 1)
        while self.text_map[row][col] != '.':
            row, col = randint(1, self.map_height - 6), randint(1, self.map_width - 1)
        type = choice(list(self.enemies_textures.keys()))
        spr = Enemies(
            self,
            type,
            self.enemies_textures[type],
            (col, row),
            0.5,
            0.8,
            1,
            self.enemies_settings[type]['can_move'],
            self.enemies_settings[type]['can_attack'],
            True,
            True,
            death_duration=5
        )
        spr.set_pathfinding(self.pathfinding)
        self.enemies.append(spr)


if __name__ == '__main__':
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "CS 3")
    start_view = Training()
    window.show_view(start_view)
    window.set_fullscreen(True)
    window.run()