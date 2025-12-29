import arcade
from math import *
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, \
    UIMessageBox
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from enemy import *
from pathfinding import *
from USP import *
from AKR import *
from settings import *


class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, fullscreen=True)
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        self.manager = UIManager()
        self.manager.enable()

        self.fps = UILabel(text="0",
                font_size=20,
                text_color=arcade.color.GREEN,
                width=300,
                align="right")

        self.fps_anchor = UIAnchorLayout()

        self.fps_anchor.add(
            child=self.fps,
            anchor_x="right",
            anchor_y="top",
            align_x=-20,
            align_y=-20
        )

        self.manager.add(self.fps_anchor)

        self.set_mouse_visible(False)

    def setup(self):

        self.kalash = AK_47('textures/guns/AK-47/ak-47.png', 'textures/guns/AK-47/ak-47_shoot.png',
                            'sounds/guns/AK-47/ak47_shoot.mp3', 1.3, 1.5, 0.15, 0.2)

        self.usp = USP('textures/guns/USP/usp.png', 'textures/guns/USP/usp_shoot.png', 'sounds/guns/USP/usp_shoot.wav',
                       2, 1.8, 0.3, 0.1)

        self.usp_list = arcade.SpriteList()
        self.usp_list.append(self.usp)
        self.kalash_list = arcade.SpriteList()
        self.kalash_list.append(self.kalash)

        self.current_gun_list = arcade.SpriteList()

        self.wall_textures = {
            'W': arcade.load_texture('textures/sky&walls/brks_2.png'),
            'L': arcade.load_texture('textures/sky&walls/img.png'),
            'B': arcade.load_texture('textures/sky&walls/wall_squares.jpg')

        }

        self.enemies_textures = {
            '1': {'defoult': arcade.load_texture('textures/enemy1pack/defoult.png'),
                  'walk1': arcade.load_texture('textures/enemy1pack/walk1.png'),
                  'walk2': arcade.load_texture('textures/enemy1pack/walk2.png')
                  },
            '2': {'defoult': arcade.load_texture('textures/enemy2pack/defoult.png'),
                  'walk1': arcade.load_texture('textures/enemy2pack/walk1.png'),
                  'walk2': arcade.load_texture('textures/enemy2pack/walk2.png')
                  }
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

            'WWWWLWWWWWWWWWWWWWW',
            'W....WW........1..W',
            'W..B...........B..W',
            'W..2..WW..........W',
            'W.................W',
            'W..BW.........W1..W',
            'W....W...2.....W..B',
            'W.. ..............B',
            'B.....WWWWWWW.....B',
            'B.................W',
            'B..B....B.B....W..W',
            'W.......BPB.......W',
            'WWWBBWWWWBWWWWWBBWW',
        ]

        self.map_width, self.map_height = len(self.text_map[0]), len(self.text_map)
        self.map_textures = {}
        self.block_map = set()

        self.radar = set()
        self.radar_scale = 10

        self.pathfinding = PathFinding(self)
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
                        enemy_type=col,
                        dict_textures=self.enemies_textures[col],
                        pos=(xbp // self.block_size, ybp // self.block_size),
                        scale=0.5,
                        floor_offset=0.8
                    )
                    spr.set_pathfinding(self.pathfinding)
                    self.enemies.append(spr)
                elif col == 'P':
                    self.player = Player(xbp, ybp)

                xbp += self.block_size
            ybp += self.block_size



        self.sky_texture = arcade.load_texture('textures/sky&walls/sky_ala.jpg')
        self.sky_offset = 0

    def on_draw(self):
        """ Очистка окна """
        self.clear()
        self.wall_batch.clear()

        def draw_sky():
            sky_h = SCREEN_HEIGHT
            sky_w = SCREEN_WIDTH
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset, -self.player.ver_a, sky_w, sky_h))
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset + SCREEN_WIDTH, -self.player.ver_a, sky_w, sky_h)
            )
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset, -self.player.ver_a + SCREEN_HEIGHT, sky_w, sky_h))
            arcade.draw_texture_rect(
                self.sky_texture,
                rect=arcade.LBWH(-self.sky_offset + SCREEN_WIDTH, -self.player.ver_a + SCREEN_HEIGHT, sky_w, sky_h)
            )

        def draw_radar():
            arcade.draw_rect_filled(arcade.rect.XYWH(self.map_width * self.block_size // self.radar_scale // 2 + 10,
                                                     SCREEN_HEIGHT - self.map_height * self.block_size // self.radar_scale // 2 - 10,
                                                     self.map_width * self.block_size // self.radar_scale,
                                                     self.map_height * self.block_size // self.radar_scale),
                                    arcade.color.GRAY)
            map_x, map_y = (self.player.x // self.radar_scale + 10,
                            SCREEN_HEIGHT - self.player.y // self.radar_scale - 10)
            arcade.draw_circle_filled(map_x, map_y, 4, (0, 0, 255))
            arcade.draw_line(map_x, map_y, map_x + 5 * cos(-self.player.angle), map_y + 5 * sin(-self.player.angle),
                             (0, 0, 0))
            for x, y in self.radar:
                arcade.draw_rect_filled(
                    arcade.rect.LBWH(x + 10, SCREEN_HEIGHT - y - self.block_size // self.radar_scale - 10,
                                     self.block_size // self.radar_scale,
                                     self.block_size // self.radar_scale), (0, 0, 0))

        def draw_floor():
            arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, SCREEN_WIDTH, half_height - self.player.ver_a),
                                    arcade.color.JET)

        blckposd = {'l': self.player.x - self.player.x // self.block_size * self.block_size,
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

            if offset >= len(self.texture_slices[text_let]):
                offset = len(self.texture_slices[text_let]) - 1
            ray_len = ray_len * cos(self.player.angle - (self.player.angle - half_FOV + delta_ray * ray)) * dep_coeff / 1.5
            h_c = coefficent / (ray_len + 0.0000000001)

            wall = arcade.Sprite(self.texture_slices[text_let][offset], 1, ray * scale, half_height - self.player.ver_a)
            wall.height = h_c
            wall.width = scale

            self.wall_batch.append(wall)

        draw_sky()
        draw_floor()
        visible_sprites = []
        for sprite in self.enemies:
            if sprite.visible:
                visible_sprites.append(sprite)

        visible_sprites.sort(key=lambda s: s.distance, reverse=True)

        self.wall_batch.draw()
        self.wall_batch.clear()

        for sprite in visible_sprites:
            sprite.draw()



        def hud():
            arcade.draw_rect_filled(arcade.rect.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT), (
                0, 0, 0, 255 - max(0, min(255, round(127.5 * (cos(2 * pi * (self.times_of_day % 24 - 12) / 24) + 1))))))
            arcade.draw_circle_filled(self.player.aim_x, self.player.aim_y, 3, (255, 0, 0))
            draw_radar()
            if self.current_gun_list:
                self.current_gun_list.draw()
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
        dx, dy = 0, 0

        if arcade.key.LSHIFT in self.player.keys_pressed:
            self.player.speed = 200
        else:
            self.player.speed = 150
        if self.current_gun_list:
            if arcade.MOUSE_BUTTON_LEFT in self.player.keys_pressed:
                self.current_gun_list[0].shooting = True
                self.player.speed = 100
            elif self.current_gun_list[0].shooting:
                self.current_gun_list[0].shooting = False
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

        if arcade.key.ESCAPE in self.player.keys_pressed:
            self.close()

        self.fps_counter += 1
        self.fps_timer += delta_time

        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
            #self.set_caption(f"{SCREEN_TITLE}  FPS: {self.current_fps}")
            self.fps.text = self.current_fps
        if not self._mouse_visible:
            self.custom_mouse_motion(self._mouse_x, self._mouse_y, delta_time)
        if self.current_gun_list:
            self.current_gun_list.update(delta_time)

        for enemy in self.enemies:
            enemy.update(delta_time)

    def custom_mouse_motion(self, x, y, delta):
        dx = x - SCREEN_WIDTH // 2

        self.sky_offset = (self.sky_offset + dx * delta * 100) % SCREEN_WIDTH

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
        self.set_mouse_position(self.player.aim_x, self.player.aim_y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """ Обработка нажатий кнопок мыши """
        self.player.keys_pressed.add(button)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """ Обработка отпускания кнопок мыши """
        if button in self.player.keys_pressed:
            self.player.keys_pressed.remove(button)
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.current_gun_list[0].shoot_timer = 0

    def on_key_press(self, key, modifiers):
        """ Обработка нажатий клавиш """
        if key == arcade.key.KEY_1:
            self.times_of_day += 1

        if key == arcade.key.KEY_3:
            self.current_gun_list = self.kalash_list


        if key == arcade.key.KEY_2:
            self.current_gun_list = self.usp_list


        if arcade.key.F1 == key:
            self.set_mouse_visible(not self._mouse_visible)
        self.player.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        """ Обработка отпускания клавиш """
        if key in self.player.keys_pressed:
            self.player.keys_pressed.remove(key)


class Player:
    def __init__(self, x, y):
        self.x = x + block_size // 2
        self.y = y + block_size // 2
        self.keys_pressed = set()
        self.ver_a = 0
        self.angle = 0.6
        self.aim_x = SCREEN_WIDTH // 2
        self.aim_y = SCREEN_HEIGHT // 2
        self.speed = 100


def main():
    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, )
    game.setup()
    game.run()


if __name__ == "__main__":
    main()
