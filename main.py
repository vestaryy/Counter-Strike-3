import arcade
from math import *

SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 800
SCREEN_TITLE = "CS 3"

block_size = 100
FOV = pi / 2
half_FOV = FOV / 2
max_depth = SCREEN_WIDTH // 100
num_rays = 650
delta_ray = FOV / (num_rays - 1)
ray_size = SCREEN_WIDTH
dist = num_rays / (2 * tan(half_FOV))
scale = SCREEN_WIDTH // num_rays
coefficent = dist * 150 * scale
half_height = SCREEN_HEIGHT / 2
dep_coeff = 2


class AK_47(arcade.BasicSprite):
    def __init__(self, path=arcade.load_texture('textures/ak-47.png'), scale=1.3):
        path.width *= 1.5
        super().__init__(path, scale)
        self.defoult_texture = path
        self.shoot_texture = arcade.load_texture('textures/ak-47_shoot.png')
        self.shoot_texture.width *= 1.5
        self.bottom = 0
        self.right = SCREEN_WIDTH
        self.shoot_timer = 0
        self.shoot_delay = 0.2
        self.active = []
        self.shoot_sound = arcade.load_sound('sounds/ak47_shoot.mp3')
        self.shooting = False
        self.speed = 100

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        if self.shooting:
            if self.shoot_timer >= self.shoot_delay or self.shoot_timer == 0:
                self.shoot_sound.play(volume=0.05)
                self.texture = self.shoot_texture
                self.right += self.speed * delta_time
                self.bottom -= self.speed * delta_time
                self.shoot_timer = 0
            else:
                self.texture = self.defoult_texture
            self.shoot_timer += delta_time

        elif self.bottom < 0 and self.right > SCREEN_WIDTH:
            self.right -= self.speed * delta_time * 2
            self.bottom += self.speed * delta_time * 2
        else:
            self.bottom = 0
            self.right = SCREEN_WIDTH

        if self.texture == self.shoot_texture and not self.shooting:
            self.texture = self.defoult_texture


class StartWindow(arcade.Window):
    def __init__(self, w, h, t):
        super().__init__(w, h, t)
        s, w = arcade.load_texture('textures/wall_squares.jpg'), arcade.load_texture('textures/soviet_wall.jpg')


    def on_key_press(self, key, modifiers):
        self.close()
        game = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, {'W': arcade.load_texture('textures/wall_squares.jpg'),
                                                                'L': arcade.load_texture('textures/soviet_wall.jpg')})
        game.setup()
        game.run()


class Game(arcade.Window):
    def __init__(self, width, height, title, textures):
        super().__init__(width, height, title)
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        self.textures = textures

        self.set_mouse_visible(False)

    def setup(self):
        self.times_of_day = 17
        self.wall_batch = arcade.SpriteList()
        self.texture_slices = {}
        for let, texture in self.textures.items():
            self.texture_slices[let] = []
            for x in range(block_size):
                self.texture_slices[let].append(texture.crop(x * (texture.width // block_size), 0, 1, texture.height))
        self.player = Player()
        self.block_size = 100
        self.text_map = [
            'WWWWWWWWWWWW',
            'W..........W',
            'W....W.....W',
            'W....LLWL.LL',
            'W....W.....L',
            'W....LLWL.LL',
            'W..WWL.....W',
            'W...L...W..W',
            'W..........W',
            'WWWWWWWWWWWW',
        ]
        self.map_width, self.map_height = len(self.text_map[0]), len(self.text_map)
        self.map_textures = {}
        self.block_map = set()

        self.radar = set()
        self.radar_scale = 5

        ybp = 0
        for row in self.text_map:
            xbp = 0
            for col in list(row):
                if col != '.':
                    self.block_map.add((xbp, ybp))
                    self.map_textures[(xbp, ybp)] = col
                    self.radar.add((xbp // self.radar_scale, ybp // self.radar_scale))
                xbp += self.block_size
            ybp += self.block_size


        self.kalash = AK_47()
        self.kalash_list = arcade.SpriteList()
        self.kalash_list.append(self.kalash)

        self.sky_texture = arcade.load_texture('textures/sky_ala.jpg')
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

        def draw_floor():
            arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, SCREEN_WIDTH, half_height - self.player.ver_a),
                                    arcade.color.JET)

        dict_block_pos = {'l': self.player.x - self.player.x // self.block_size * self.block_size,
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
                    vertical_d = self.block_size / cos_a * dep + dict_block_pos['r'] / cos_a + 1
                elif cos_a < 0:
                    vertical_d = self.block_size / -cos_a * dep + dict_block_pos['l'] / -cos_a + 1
                xv, yv = vertical_d * cos_a + self.player.x, vertical_d * sin_a + self.player.y
                index = xv // self.block_size * self.block_size, yv // self.block_size * self.block_size
                if index in self.block_map:
                    texture_v = self.map_textures[index]
                    break

            for dep in range(self.map_height):
                if sin_a > 0:
                    horiz_d = self.block_size / sin_a * dep + dict_block_pos['b'] / sin_a + 1
                elif sin_a < 0:
                    horiz_d = self.block_size / -sin_a * dep + dict_block_pos['t'] / -sin_a + 1
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
            ray_len = ray_len * cos(
                self.player.angle - (self.player.angle - half_FOV + delta_ray * ray)) * dep_coeff / 1.5
            h_c = coefficent / (ray_len + 0.0000000001)

            wall = arcade.Sprite(self.texture_slices[text_let][offset], 1, ray * scale, half_height - self.player.ver_a)
            wall.height = h_c
            wall.width = scale

            self.wall_batch.append(wall)

        draw_sky()
        draw_floor()
        self.wall_batch.draw()

        def draw_radar():
            arcade.draw_rect_filled(arcade.rect.XYWH(self.map_width * self.block_size // self.radar_scale // 2 + 10,
                                                     SCREEN_HEIGHT - self.map_height * self.block_size // self.radar_scale // 2 - 10,
                                                     self.map_width * self.block_size // self.radar_scale,
                                                     self.map_height * self.block_size // self.radar_scale),
                                                     arcade.color.GRAY)
            map_x, map_y = (self.player.x // self.radar_scale + 10,
                            SCREEN_HEIGHT - self.player.y // self.radar_scale - 10)
            arcade.draw_circle_filled(map_x, map_y, self.radar_scale // 1.5, (0, 0, 255))
            arcade.draw_line(map_x, map_y, map_x + 5 * cos(-self.player.angle), map_y + 5 * sin(-self.player.angle), (0, 0, 0))
            for x, y in self.radar:
                arcade.draw_rect_filled(
                    arcade.rect.LBWH(x + 10, SCREEN_HEIGHT - y - 30, self.block_size // self.radar_scale,
                                     self.block_size // self.radar_scale), (0, 0, 0))

        def hud():
            arcade.draw_rect_filled(arcade.rect.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT), (0, 0, 0, 255 - max(0, min(255, round(127.5 * (cos(2 * pi * (self.times_of_day % 24 - 12) / 24) + 1))))))
            arcade.draw_circle_filled(self.player.aim_x, self.player.aim_y, 3, (255, 0, 0))
            draw_radar()
            self.kalash_list.draw()

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

        if arcade.MOUSE_BUTTON_LEFT in self.player.keys_pressed:
            self.kalash.shooting = True
            self.player.speed = 100
        elif self.kalash.shooting:
            self.kalash.shooting = False
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
            self.set_caption(f"{SCREEN_TITLE}  FPS: {self.current_fps}")
        if not self._mouse_visible:
            self.custom_mouse_motion(self._mouse_x, self._mouse_y, delta_time)

        self.kalash.update(delta_time)

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
            self.kalash.shoot_timer = 0

    def on_key_press(self, key, modifiers):
        """ Обработка нажатий клавиш """
        if key == arcade.key.KEY_1:
            self.times_of_day += 1
        self.player.keys_pressed.add(key)
        if arcade.key.F1 == key:
            self.set_mouse_visible(not self._mouse_visible)

    def on_key_release(self, key, modifiers):
        """ Обработка отпускания клавиш """
        if key in self.player.keys_pressed:
            self.player.keys_pressed.remove(key)


class Player:
    def __init__(self):
        self.x = block_size + 50
        self.y = block_size + 50
        self.keys_pressed = set()
        self.ver_a = 0
        self.angle = 0.6
        self.aim_x = SCREEN_WIDTH // 2
        self.aim_y = SCREEN_HEIGHT // 2
        self.speed = 100


def main():
    StartWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()


if __name__ == "__main__":
    main()
