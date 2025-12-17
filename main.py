import arcade
from math import *

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "CS 3"

block_size = 100
FOV = pi / 2
half_FOV = FOV / 2
max_depth = SCREEN_WIDTH // 100
num_rays = 300
delta_ray = FOV / (num_rays - 1)
ray_size = SCREEN_WIDTH
dist = num_rays / (2 * tan(half_FOV))
scale = SCREEN_WIDTH // num_rays
coefficent = dist * 100 * scale
half_height = SCREEN_HEIGHT / 2
dep_coeff = 2


class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0

        # Скрываем курсор мыши
        # self.set_mouse_visible(False)

        # Чувствительность мыши
        self.mouse_sensitivity = 0.003  # Чувствительность мыши

    def setup(self):
        self.keys_pressed = set()
        self.ver_a = 0
        self.angle = 0
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.block_size = 100
        self.text_map = [
            'WWWWWWWWWWWW',
            'W..........W',
            'W..........W',
            'W.........WW',
            'W..........W',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ]
        self.block_map = set()
        y_block_pos = 0
        for row in self.text_map:
            x_block_pos = 0
            for column in list(row):
                if column == 'W':
                    self.block_map.add((x_block_pos, y_block_pos))
                x_block_pos += self.block_size
            y_block_pos += self.block_size

    def on_draw(self):
        """ Очистка окна """
        self.clear()
        arcade.draw_rect_filled(arcade.rect.LBWH(0, half_height - self.ver_a, SCREEN_WIDTH, half_height + self.ver_a),
                                arcade.color.SKY_BLUE)
        arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, SCREEN_WIDTH, half_height - self.ver_a), arcade.color.JET)
        # for x, y in self.block_map:
        #     arcade.draw_rect_outline(arcade.rect.LBWH(x, y, self.block_size, self.block_size), arcade.color.GRAY)

        in_block_pos = {'left': self.x - self.x // self.block_size * self.block_size,
                        'top': self.y - self.y // self.block_size * self.block_size,
                        'right': self.block_size - (self.x - self.x // self.block_size * self.block_size),
                        'bottom': self.block_size - (self.y - self.y // self.block_size * self.block_size)
                        }
        for ray in range(num_rays):
            cur_angle = self.angle - half_FOV + delta_ray * ray
            cos_a, sin_a = cos(cur_angle), sin(cur_angle)
            vd, hd = 0, 0
            founded = False
            for dep in range(max_depth):
                if cos_a > 0:
                    vd = in_block_pos['right'] / cos_a + self.block_size / cos_a * dep + 1
                elif cos_a < 0:
                    vd = in_block_pos['left'] / -cos_a + self.block_size / -cos_a * dep + 1
                x, y = vd * cos_a + self.x, vd * sin_a + self.y
                fix_x, fix_y = x // self.block_size * self.block_size, y // self.block_size * self.block_size
                if (fix_x, fix_y) in self.block_map:
                    founded = True
                    break

            for dep in range(max_depth):
                if sin_a > 0:
                    hd = in_block_pos['bottom'] / sin_a + self.block_size / sin_a * dep + 1
                elif sin_a < 0:
                    hd = in_block_pos['top'] / -sin_a + self.block_size / -sin_a * dep + 1
                x, y = hd * cos_a + self.x, hd * sin_a + self.y
                fix_x, fix_y = x // self.block_size * self.block_size, y // self.block_size * self.block_size
                if (fix_x, fix_y) in self.block_map:
                    founded = True
                    break

            if founded:
                ray_size = min(vd, hd) * dep_coeff
                ray_size *= cos(self.angle - cur_angle)
                h_c = coefficent / (ray_size + 0.0001)
                c = 255 / (ray_size ** 2 * 0.000001 + 1)
                color = (c, c, c)
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(ray * scale + scale / 2, (half_height) - self.ver_a, scale, h_c), color)

        # Точка с лучом
        # arcade.draw_circle_filled(self.x, self.y, 10, (0, 255, 255))
        # arcade.draw_line(self.x, self.y, SCREEN_WIDTH * cos(self.angle) + self.x,
        #                  SCREEN_WIDTH * sin(self.angle) + self.y,
        #                  (0, 255, 255))

    def on_update(self, delta_time):
        if arcade.key.LSHIFT in self.keys_pressed:
            self.ver_a -= 150 * delta_time * 10
        if arcade.key.LCTRL in self.keys_pressed:
            self.ver_a += 150 * delta_time * 10

        if arcade.MOUSE_BUTTON_LEFT in self.keys_pressed:
            self.angle -= delta_time * 1.5
        if arcade.MOUSE_BUTTON_RIGHT in self.keys_pressed:
            self.angle += delta_time * 1.5

        if arcade.key.W in self.keys_pressed:
            self.x += cos(self.angle) * delta_time * 500
            self.y += sin(self.angle) * delta_time * 500
        if arcade.key.S in self.keys_pressed:
            self.x -= cos(self.angle) * delta_time * 500
            self.y -= sin(self.angle) * delta_time * 500
        if arcade.key.A in self.keys_pressed:
            self.x += sin(self.angle) * delta_time * 500
            self.y -= cos(self.angle) * delta_time * 500
        if arcade.key.D in self.keys_pressed:
            self.x -= sin(self.angle) * delta_time * 500
            self.y += cos(self.angle) * delta_time * 500

        self.fps_counter += 1
        self.fps_timer += delta_time

        # Обновляем FPS каждую секунду
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
            self.set_caption(f"{SCREEN_TITLE} - FPS: {self.current_fps}")

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """
        Обработка движения мыши.
        dx, dy - ИЗМЕНЕНИЕ позиции мыши с последнего вызова (относительное движение)
        НЕ нужно возвращать мышь в центр!
        """
        # Изменяем угол в зависимости от горизонтального движения мыши
        # dx - изменение по горизонтали с последнего кадра

        self.angle += dx * self.mouse_sensitivity
        self.set_mouse_position(800, 500)

        # d = x - SCREEN_WIDTH // 2
        # self.set_mouse_position(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        # self.angle += x + dx * self.mouse_sensitivity

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """ Обработка нажатий кнопок мыши """
        self.keys_pressed.add(button)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """ Обработка отпускания кнопок мыши """
        if button in self.keys_pressed:
            self.keys_pressed.remove(button)

    def on_key_press(self, key, modifiers):
        """ Обработка нажатий клавиш """
        self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        """ Обработка отпускания клавиш """
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)


def main():
    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
