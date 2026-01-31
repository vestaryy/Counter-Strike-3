from arcade.gui import UIManager, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout
from pyglet.graphics import Batch
from random import choice
from src.weapons.USP import *
from src.weapons.AKR import *
import time
from src.entities.enemy import *
from src.entities.pathfinding import PathFinding
from src.player.player import Player


FLOOR_FRAGMENT_SHADER = """
#version 330

uniform sampler2D u_tex_floor; 
uniform sampler2D u_tex_ceiling; 
uniform vec2 u_res;
uniform vec2 u_player_pos;
uniform float u_player_angle;
uniform float u_ver_a;
uniform float u_block_size;
uniform float u_fov;
uniform float u_coeff; 
uniform float u_player_height; 

in vec2 v_uv;
out vec4 f_color;

void main() {
    float horizon_y = 0.5 - (u_ver_a / u_res.y);
    bool is_floor = v_uv.y < horizon_y;
    float p = is_floor ? (horizon_y - v_uv.y) : (v_uv.y - horizon_y);
    p = max(p, 0.0001);

    float screen_x_norm = v_uv.x - 0.5;
    float ray_angle_offset = screen_x_norm * u_fov;
    float ray_angle = u_player_angle + ray_angle_offset;

    float height = is_floor ? u_player_height : (1.0 - u_player_height);
    float distance = (height * u_coeff) / (p * u_res.y) / cos(ray_angle_offset);

    float world_x = u_player_pos.x + cos(ray_angle) * distance;
    float world_y = u_player_pos.y + sin(ray_angle) * distance;

    vec2 uv_tex = vec2(world_x / u_block_size, world_y / u_block_size);
    uv_tex = fract(uv_tex);

    float fog = clamp(1.5 / (1.0 + distance * 0.002), 0.0, 1.0);

    vec4 tex_color;
    if (is_floor) {
        tex_color = texture(u_tex_floor, uv_tex);
    } else {
        tex_color = texture(u_tex_ceiling, uv_tex);
    }

    f_color = vec4(tex_color.rgb * fog, 1.0);
}
"""

class Stage3(arcade.View):
    def __init__(self):
        super().__init__()
        self.window.set_fullscreen(True)


    def on_show_view(self):
        self.flag2 = False
        self.current_stage = 3
        self.timer_for_slide = 0
        self.shoot = 0
        self.headshot = 0
        self.bodyshot = 0
        self.window.set_mouse_position(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.batch = Batch()
        self.draw_unlock = False
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
        self.goal = UILabel(text="Задача: исследовать лабораторию",
                            font_size=20,
                            font_name='SimSun',
                            text_color=arcade.color.WHITE,
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
            child=self.goal,
            anchor_x="left",
            anchor_y="top",
            align_x=20,
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

        self.usp = USP(self, [80, 90], [15, 25], '../../assets/textures/guns/USP/usp.png',
                       '../../assets/textures/guns/USP/usp_shoot.png',
                       '../../assets/sounds/guns/USP/usp_shoot.wav',
                       2, 1.5, 0.3, 0.1, 12, 30)
        self.kalash = AK_47(self, [90, 120], [28, 30], '../../assets/textures/guns/AK-47/ak-47.png',
                            '../../assets/textures/guns/AK-47/ak-47_shoot.png',
                            '../../assets/sounds/guns/AK-47/ak47_shoot.wav', 1.3, 1.5, 0.15, 0.15, 30, 120)

        self.icons_list = arcade.SpriteList()
        self.usp_icon = arcade.Sprite('../../assets/textures/guns/USP/icon2.png', scale=0.1)
        self.usp_icon.right = SCREEN_WIDTH - 5
        self.usp_icon.top = half_height - 5
        self.icons_list.append(self.usp_icon)

        self.medicals = arcade.Sprite('../../assets/textures/elements/med2.png', 0.05)
        self.medicals.center_x = SCREEN_WIDTH // 2
        self.medicals.bottom = 10

        self.medicals_list = arcade.SpriteList()
        self.medicals_list.append(self.medicals)




        self.background_sprite = arcade.Sprite('../../assets/textures/sky&walls/light.png', 2.1 - SCREEN_SCALE, SCREEN_WIDTH // 2,
                                               SCREEN_HEIGHT // 2)



        self.enemies_textures = {
            't': {'default': arcade.load_texture('../../assets/textures/enemy1pack/defoult.png'),
                  'walk1': arcade.load_texture('../../assets/textures/enemy1pack/walk1.png'),
                  'walk2': arcade.load_texture('../../assets/textures/enemy1pack/walk2.png'),
                  'headshot': arcade.load_texture('../../assets/textures/enemy1pack/headshot.png'),
                  'bodyshot': arcade.load_texture('../../assets/textures/enemy1pack/bodyshot.png'),
                  'death': arcade.load_texture('../../assets/textures/enemy1pack/death.png'),
                  'shoot': arcade.load_texture('../../assets/textures/enemy1pack/shoot.png')
                  },
            'w': {'default': arcade.load_texture('../../assets/textures/enemy2pack/defoult.png'),
                  'walk1': arcade.load_texture('../../assets/textures/enemy2pack/walk1.png'),
                  'walk2': arcade.load_texture('../../assets/textures/enemy2pack/walk2.png'),
                  'headshot': arcade.load_texture('../../assets/textures/enemy2pack/headshot.png'),
                  'bodyshot': arcade.load_texture('../../assets/textures/enemy2pack/bodyshot.png'),
                  'death': arcade.load_texture('../../assets/textures/enemy2pack/death.png'),
                  'shoot': arcade.load_texture('../../assets/textures/enemy2pack/shoot.png')
                  }
                }

        self.enemies_settings = {
            't': {'can_attack': True, 'can_move': True, 'd': 60},
            'w': {'can_attack': True, 'can_move': True, 'd': 60},
        }

        Enemies.precompute_texture_slices_for_all_enemies(self.enemies_textures)

        self.enemies = []

        self.times_of_day = 17
        self.wall_batch = arcade.SpriteList()
        self.texture_slices = {}


        self.block_size = 100
        self.wall_textures = {
            'W': arcade.load_texture('../../assets/textures/sky&walls/lab.jpg'),
            'K': arcade.load_texture('../../assets/textures/sky&walls/labwithKalash.png'),
            'D': arcade.load_texture('../../assets/textures/sky&walls/door.jpg'),
            'G': arcade.load_texture('../../assets/textures/sky&walls/gates.png'),
            'w': arcade.load_texture('../../assets/textures/sky&walls/labwithdoor.png'),
            's': arcade.load_texture('../../assets/textures/sky&walls/stena.jpg'),
            'L': arcade.load_texture('../../assets/textures/sky&walls/lift.png'),
            'd': arcade.load_texture('../../assets/textures/sky&walls/lab.jpg'),
            '3': arcade.load_texture('../../assets/textures/sky&walls/deactive.png'),
            '5': arcade.load_texture('../../assets/textures/sky&walls/deactive.png'),
            '7': arcade.load_texture('../../assets/textures/sky&walls/deactive.png'),
            'A': arcade.load_texture('../../assets/textures/sky&walls/active.png'),

        }
        for let, texture in self.wall_textures.items():
            self.texture_slices[let] = []
            for x in range(block_size):
                self.texture_slices[let].append(texture.crop(x * (texture.width / block_size), 0, 1, texture.height))
        self.text_map = [
            'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW',
            'WWdWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW',
            'GP.D...................................W',
            'WWdW...................................W',
            'WWWW...................................W',
            'WWWW...................................W',
            'WWWW...................................W',
            'WWWWWWDWWWWWWWWWDWWWWWWWWWWWWDWWWWWWWWWW',
            'WWWW.........WW...W.........W.W........W',
            'WWWW.........WW...W.........D.D........W',
            'WWWW.........WWWWWW.........W.W........W',
            'WWWW.........WWWLWWWWWWWWWWWW.WWWWWWWWWW',
            'WWWW.........W3...W.........W.W........W',
            'WWWW.........W5...W.........W.W........W',
            'WWWW.........W7.............D.D........W',
            'WWWW.........WW...W.........W.W........W',
            'WWWWWWWWWWWWWWWWKWWWWWWWWWWWWWWWWWWWWWWW'
        ]

        self.robberied_count = 0
        self.map_width, self.map_height = len(self.text_map[0]), len(self.text_map)
        self.map_textures = {}
        self.block_map = set()

        self.radar = set()
        self.radar_scale = 10

        self.pathfinding = PathFinding(self)

        with open('../../data/data.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            saved_health = int(lines[1])
            self.usp.patrons, self.usp.magazines = (int( lines[2].split('/')[0]), int( lines[2].split('/')[1]))

            f = False
            ybp = 0
            for row in self.text_map:
                if f:
                    break
                xbp = 0
                for col in list(row):
                    if col == 'P':
                        self.player = Player(xbp, ybp)
                        self.player.health = saved_health
                        f = True
                        break
                    xbp += self.block_size
                ybp += self.block_size
            ybp = 0



        self.usp_list = arcade.SpriteList()
        self.usp_list.append(self.usp)
        self.kalash_list = arcade.SpriteList()
        self.kalash_list.append(self.kalash)
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
                        0.8 if col != 'b' else 1,
                        1,
                        self.enemies_settings[col]['can_move'],
                        self.enemies_settings[col]['can_attack'],
                        False,
                        True,
                        death_duration=self.enemies_settings[col]['d']
                    )
                    spr.set_pathfinding(self.pathfinding)
                    self.enemies.append(spr)

                xbp += self.block_size
            ybp += self.block_size
        self.light_coeff = 0.0000001
        self.hud_batch = Batch()

        self.button_to_press = arcade.Text(
            '''Нажмите "Е", чтобы использовать.''',
            0, 0,
            arcade.color.WHITE,
            anchor_x='center',
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
        self.background_sprite_list = arcade.SpriteList()
        self.background_sprite_list.append(self.background_sprite)

        self.health_list.append(self.health_text)
        self.music_player_bg = arcade.load_sound('../../assets/sounds/background/09. Night 3.mp3').play(0.3, loop=True)
        self.patrons_sound = arcade.load_sound(
            '../../assets/sounds/background/bullet-casing-7mm-bullets-drop-pile-cement_my8iaf4o.mp3')
        self.zip_bag = arcade.load_sound('../../assets/sounds/background/bbe1c9e31bbaee7.mp3')
        self.steps_sound = arcade.load_sound('../../assets/sounds/background/6a371044071ac0e.mp3')
        self.timer_steps = 0
        self.player.angle = 0

        self.subtitles_label = UILabel('', font_size=20,
                              text_color=arcade.color.WHITE,
                              width=300,
                              align="center")
        self.fps_anchor.add(
            child=self.subtitles_label,
            anchor_x="center",
            anchor_y="bottom",
            align_y=10
        )
        self.timer_for_st = 0
        self.flag1= True
        self.timer_for_new_patrons = 3
        self.add_patrons = UILabel('', font_size=20,
                              text_color=arcade.color.WHITE,
                              width=300,
                              align="right")
        self.fps_anchor.add(
            child=self.add_patrons,
            anchor_x="right",
            anchor_y="bottom",
            align_y=50
        )
        self.timer_death = 0

        self.floor_tex = self.window.ctx.load_texture('../../assets/textures/sky&walls/textur-gas-kvas-com-tc5o-p-teksturi-pol-laboratorii-5.jpg')
        self.ceil_tex = self.window.ctx.load_texture('../../assets/textures/sky&walls/ceiling.jpg')

        self.floor_quad = arcade.gl.geometry.quad_2d_fs()
        self.floor_prog = self.window.ctx.program(
            vertex_shader="""
                                    #version 330
                                    in vec2 in_vert;
                                    in vec2 in_uv;
                                    out vec2 v_uv;
                                    void main() {
                                        v_uv = in_uv;
                                        gl_Position = vec4(in_vert, 0.0, 1.0);
                                    }
                                    """,
            fragment_shader=FLOOR_FRAGMENT_SHADER
        )
        self.floor_prog['u_tex_floor'] = 0
        self.floor_prog['u_tex_ceiling'] = 1

        self.floor_prog['u_res'] = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.floor_prog['u_block_size'] = float(self.block_size)
        self.floor_prog['u_fov'] = float(FOV)
        self.floor_prog['u_coeff'] = float(coefficent / (dep_coeff / 1.5))
        self.floor_prog['u_player_height'] = 0.5

        self.back = arcade.load_texture('../../assets/textures/sky&walls/light.png')
        self.current_slide = self.back
        self.loading = arcade.load_texture('../../assets/textures/sky&walls/loading.png')
        self.s1 = arcade.load_texture('../../assets/textures/elements/s1.png')
        self.s2 = arcade.load_texture('../../assets/textures/elements/s2.png')



    def on_draw(self):
        """ Очистка окна """
        self.clear()
        self.wall_batch.clear()
        if self.flag2:
            arcade.draw_texture_rect(self.current_slide,
                                     arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH,
                                                      SCREEN_HEIGHT))

            return



        if self.player.health <= 0:
            arcade.draw_texture_rect(arcade.load_texture('../../assets/textures/sky&walls/death.png'), arcade.rect.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT))
            return

        def draw_floor_and_ceiling():
            self.floor_tex.use(0)
            self.ceil_tex.use(1)
            self.floor_prog['u_player_pos'] = (self.player.x, self.player.y)
            self.floor_prog['u_player_angle'] = self.player.angle
            self.floor_prog['u_ver_a'] = float(self.player.ver_a)

            self.floor_quad.render(self.floor_prog)

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

                c = 255 - int(255 / (1 + ray_len ** 2 * self.light_coeff))

                wall = arcade.Sprite(
                    self.texture_slices[text_let][offset],
                    1,
                    ray * scale,
                    half_height - self.player.ver_a
                )
                wall.height = h_c
                wall.width = scale
                wall.color = (wall.color[0] - c, wall.color[1] - c, wall.color[2] - c)

                self.wall_batch.append(wall)

        draw_floor_and_ceiling()

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

            if self.draw_key or self.draw_unlock:
                self.button_to_press.x = self.player.aim_x
                self.button_to_press.y = self.player.aim_y + 20
                self.hud_batch.draw()
            if self.add_patrons.text == 'Аптечка':
                self.medicals_list.draw()

            if self.player.damage_indicator_angle is not None and self.player.damage_indicator_timer > 0:

                arcade.draw_arc_outline(
                    self.player.aim_x, self.player.aim_y,
                    50, 50,
                    arcade.color.RED,
                    degrees(self.player.angle - self.player.damage_indicator_angle - 0.2),
                    degrees(self.player.angle - self.player.damage_indicator_angle + 0.2),
                    5, 255
                )

            if self.player.current_gun_list:
                self.player.current_gun_list.draw()

            self.background_sprite_list.draw()

            self.health_list.draw()
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
        if hasattr(self, 'flag2'):
            if self.flag2:

                if not hasattr(self, 'local_track'):
                    self.local_track = arcade.load_sound(
                        '../../assets/sounds/background/metro-last-light-01-reminiscence_8MwVNx6l.mp3').play(0.3)
                self.timer_for_slide += delta_time
                if self.current_slide == self.back and self.timer_for_slide > 1.5:
                    self.current_slide = self.s1
                    self.timer_for_slide = 0
                    self.player = arcade.load_sound('../../assets/sounds/background/Самое время....mp3').play()
                if self.current_slide == self.s1 and self.timer_for_slide > 3:
                    self.current_slide = self.s2
                    self.timer_for_slide = 0
                    self.player = arcade.load_sound('../../assets/sounds/background/Вирус....mp3').play()
                if self.current_slide == self.s2 and self.timer_for_slide > 38:
                    self.current_slide = self.loading
                    self.timer_for_slide = 0
                if self.current_slide == self.loading and self.timer_for_slide > 0:
                    arcade.stop_sound(self.local_track)
                    from src.views.stage4 import Stage4
                    game_view = Stage4()
                    self.window.show_view(game_view)







                return
        if self.player is None:
            return
        if self.player.health <= 0 and self.timer_death < 1:
            self.timer_death += delta_time
            return
        elif self.timer_death >= 1:
            arcade.stop_sound(self.music_player_bg)
            arcade.stop_sound(self.player.get_damage_music)
            if hasattr(self, 'steps_player'):
                arcade.stop_sound(self.steps_player)
            game_view = Stage3()
            self.window.show_view(game_view)
            return
        if self.timer_for_new_patrons > 0:
            self.timer_for_new_patrons -= delta_time
            if self.timer_for_new_patrons <= 0:
                self.add_patrons.text = ''
        self.timer_for_st -= delta_time
        self.timer_steps += delta_time
        dx, dy = 0, 0
        if self.timer_for_st <= 0 and self.subtitles_label.text:
            self.subtitles_label.text = ''


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
        if 200 < self.player.x < 300 and 200 < self.player.y < 300 and -0.5 < sin(self.player.angle) < 0.5 and cos(self.player.angle) > 0.8 and (300, 200) in self.block_map:
            self.draw_unlock = (300, 200)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 600 < self.player.x < 700 and 600 < self.player.y < 700 and 0.7 < sin(self.player.angle) and -0.6 < cos(self.player.angle) < 0.6 and (600, 700) in self.block_map:
            self.draw_unlock = (600, 700)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 1600 < self.player.x < 1700 and 600 < self.player.y < 700 and 0.7 < sin(self.player.angle) and -0.6 < cos(self.player.angle) < 0.6 and (1600, 700) in self.block_map:
            self.draw_unlock = (1600, 700)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 2900 < self.player.x < 3000 and 600 < self.player.y < 700 and 0.7 < sin(self.player.angle) and -0.6 < cos(self.player.angle) < 0.6 and (2900, 700) in self.block_map:
            self.draw_unlock = (2900, 700)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 2900 < self.player.x < 3000 and 900 < self.player.y < 1000 and -0.5 < sin(self.player.angle) < 0.5 and cos(self.player.angle) > 0.8 and (3000, 900) in self.block_map:
            self.draw_unlock = (3000, 900)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 2900 < self.player.x < 3000 and 900 < self.player.y < 1000 and -0.6 < sin(self.player.angle) < 0.6 and -0.8 > cos(self.player.angle) and (2800, 900) in self.block_map:
            self.draw_unlock = (2800, 900)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 2900 < self.player.x < 3000 and 1400 < self.player.y < 1500 and -0.6 < sin(self.player.angle) < 0.6 and -0.8 > cos(self.player.angle) and (2800, 1400) in self.block_map:
            self.draw_unlock = (2800, 1400)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 2900 < self.player.x < 3000 and 1400 < self.player.y < 1500 and -0.5 < sin(self.player.angle) < 0.5 and cos(self.player.angle) > 0.8 and (3000, 1400) in self.block_map:
            self.draw_unlock = (3000, 1400)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 1500 < self.player.x < 1600 and 1400 < self.player.y < 1500 and -0.6 < sin(self.player.angle) < 0.6 and cos(self.player.angle) < -0.8 and self.texture_slices['7'] != self.texture_slices['A']:
            self.draw_unlock = (1400, 1400)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 1500 < self.player.x < 1600 and 1300 < self.player.y < 1400 and -0.6 < sin(self.player.angle) < 0.6 and cos(self.player.angle) < -0.8 and self.texture_slices['5'] != self.texture_slices['A']:
            self.draw_unlock = (1400, 1300)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 1500 < self.player.x < 1600 and 1200 < self.player.y < 1300 and -0.6 < sin(self.player.angle) < 0.6 and cos(self.player.angle) < -0.8 and self.texture_slices['3'] != self.texture_slices['A']:
            self.draw_unlock = (1400, 1200)
            self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

        elif 1600 < self.player.x < 1700 and 1500 < self.player.y < 1600 and 0.7 < sin(self.player.angle) and -0.6 < cos(self.player.angle) < 0.6 and self.texture_slices['K'] != self.texture_slices['W']:
            self.draw_unlock = (1600, 1600)
        elif 1600 < self.player.x < 1700 and 1200 < self.player.y < 1300 and -0.7 > sin(self.player.angle) and -0.6 < cos(self.player.angle) < 0.6 and (1600, 1100) in self.block_map:
            self.draw_unlock = (1600, 1100)




        else:
            self.draw_unlock = False


        self.fps_counter += 1
        self.fps_timer += delta_time

        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
            self.fps.text = self.current_fps

        if not self.window._mouse_visible:
            self.custom_mouse_motion(self.window._mouse_x, self.window._mouse_y, delta_time)

        if self.player.current_gun_list:
            self.player.current_gun_list.update(delta_time)
            self.patrons.text = f'{self.player.current_gun_list[0].patrons}/{self.player.current_gun_list[0].magazines}'
        self.draw_key = False
        for enemy in self.enemies:
            update_enemy = enemy.update(delta_time)


            if enemy.has_patrons and type(
                    update_enemy) == str and enemy.distance_to_player <= self.block_size and enemy.current_texture_name == 'death':
                self.draw_key = True
                self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'

                if arcade.key.E in self.player.keys_pressed and self.draw_key:
                    self.zip_bag.play()
                    n = randint(2, 15)
                    self.robberied_count += 1
                    self.add_patrons.text = f'+{n}'
                    if self.robberied_count == 9:
                        self.add_patrons.text = 'Ключ-карта от ворот №5'
                        arcade.load_sound('../../assets/sounds/background/game-bonus-french_zkfnabeu.mp3').play()
                    elif self.robberied_count == 11:
                        self.add_patrons.text = 'Аптечка'
                        arcade.load_sound('../../assets/sounds/background/med.mp3').play()
                        self.player.health = 100


                    self.timer_for_new_patrons = 3
                    self.player.current_gun_list[0].magazines += n
                    self.patrons_sound.play()
                    enemy.has_patrons = False
                    self.player.keys_pressed.remove(arcade.key.E)


        if 400 < self.player.x < 500 and 200 < self.player.y < 300 and self.flag1:
            arcade.load_sound('../../assets/sounds/Edward_monolog/Антуражно.mp3').play()
            self.timer_for_st = 3
            self.subtitles_label.text = 'Антуражно'
            self.flag1 = False


        if self.player.damage_indicator_timer > 0:
            self.player.damage_indicator_timer -= delta_time
            if self.player.damage_indicator_timer < 0:
                self.player.damage_indicator_timer = 0
                self.player.damage_indicator_angle = None

        self.health.text = str(self.player.health)
        self.health_list[-1].scale = max((100 - self.player.health) // 10, 1)

    def custom_mouse_motion(self, x, y, delta):
        dx, dy = x - int((SCREEN_WIDTH * SCREEN_SCALE) // 2), y - int((SCREEN_HEIGHT * SCREEN_SCALE) // 2)
        self.player.angle += dx * delta * 0.1

        if self.player.ver_a < -SCREEN_HEIGHT:
            self.player.ver_a = -70

        if dy > 0:
            if SCREEN_HEIGHT > self.player.ver_a + dy * delta * 50:
                self.player.ver_a += dy * delta * 50
        if dy < 0:
            if self.player.ver_a + dy * delta * 50 > -SCREEN_HEIGHT:
                self.player.ver_a += dy * delta * 50
        self.window.set_mouse_position(int((SCREEN_WIDTH * SCREEN_SCALE) // 2), int((SCREEN_HEIGHT * SCREEN_SCALE) // 2))

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
        if self.flag2:
            return
        if not self.player_moved:
            # arcade.load_sound('sounds/Edward_monolog/Вспомнить навыки....mp3').play()
            # self.subtitles_label.text = 'Надо бы вспомнить навыки стрельбы, тем более после такой посадочки!'
            # self.timer_for_st = 7
            self.player_moved = True

        if key == arcade.key.ESCAPE:
            arcade.stop_sound(self.music_player_bg)
            if hasattr(self.player, 'get_damage_music') and self.player.get_damage_music:
                try:
                    arcade.stop_sound(self.player.get_damage_music)
                except:
                    pass
            if hasattr(self, 'steps_player') and self.steps_player:
                try:
                    arcade.stop_sound(self.steps_player)
                except:
                    pass

            self.window.set_mouse_visible(True)
            from src.views.main_menu import MainMenu
            menu = MainMenu()
            self.window.show_view(menu)


        if key == arcade.key.KEY_1 and self.texture_slices['K'] == self.texture_slices['W']:
            self.player.current_gun_list = self.kalash_list

        if key == arcade.key.KEY_2:
            self.player.current_gun_list = self.usp_list


        if key == arcade.key.E:
            if self.draw_unlock:
                if (300, 200) in self.block_map and self.draw_unlock == (300, 200):
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((300, 200))
                    self.texture_slices['d'] = self.texture_slices['w']

                elif (600, 700) in self.block_map and self.draw_unlock == (600, 700):
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((600, 700))
                elif (1600, 700) in self.block_map and self.draw_unlock ==(1600, 700) :
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((1600, 700))
                    arcade.load_sound('../../assets/sounds/Edward_monolog/Почему такая....mp3').play()
                    self.timer_for_st = 6
                    self.subtitles_label.text = 'Почему такая пустая? Неужели они уже прорвались'

                elif (2900, 700) in self.block_map and self.draw_unlock == (2900, 700):
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((2900, 700))
                    arcade.load_sound('../../assets/sounds/Edward_monolog/Раньше....mp3').play()
                    self.timer_for_st = 12
                    self.subtitles_label.text = ('Раньше тут наблюдали за поведением испытуемых,'
                                                 ' а на нижнем этаже находился блок управления - именно туда они скорее всего рвутся')

                elif (3000, 900) in self.block_map and self.draw_unlock ==(3000, 900) :
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((3000, 900))

                elif (2800, 900) in self.block_map and self.draw_unlock == (2800, 900):
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((2800, 900))

                elif (2800, 1400) in self.block_map and self.draw_unlock == (2800, 1400):
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((2800, 1400))

                elif (3000, 1400) in self.block_map and self.draw_unlock == (3000, 1400):
                    arcade.load_sound('../../assets/sounds/background/interior-door-handle.mp3').play()
                    self.block_map.remove((3000, 1400))

                elif (1400, 1200) in self.block_map and self.draw_unlock == (1400, 1200):
                    arcade.load_sound('../../assets/sounds/background/49023_570752-lq55.mp3').play()
                    self.texture_slices['3'] = self.texture_slices['A']
                    if (self.texture_slices['3'] == self.texture_slices['5'] == self.texture_slices['7'] ==
                            self.texture_slices['A']):
                        arcade.load_sound('../../assets/sounds/background/221653992a693ef.mp3').play()
                elif (1400, 1300) in self.block_map and self.draw_unlock == (1400, 1300):
                    arcade.load_sound('../../assets/sounds/background/49023_570752-lq55.mp3').play()
                    self.texture_slices['5'] = self.texture_slices['A']
                    if (self.texture_slices['3'] == self.texture_slices['5'] == self.texture_slices['7'] ==
                            self.texture_slices['A']):
                        arcade.load_sound('../../assets/sounds/background/221653992a693ef.mp3').play()
                elif (1400, 1400) in self.block_map and self.draw_unlock == (1400, 1400):
                    arcade.load_sound('../../assets/sounds/background/49023_570752-lq55.mp3').play()
                    self.texture_slices['7'] = self.texture_slices['A']
                    if (self.texture_slices['3'] == self.texture_slices['5'] == self.texture_slices['7'] ==
                            self.texture_slices['A']):
                        arcade.load_sound('../../assets/sounds/background/221653992a693ef.mp3').play()

                elif self.draw_unlock == (1600, 1600) and self.texture_slices['K'] != self.texture_slices['W']:
                    arcade.load_sound('../../assets/sounds/guns/quick-click-reload.mp3').play()
                    self.texture_slices['K'] = self.texture_slices['W']
                    self.player.current_gun_list = self.kalash_list
                    self.icons_list = arcade.SpriteList()
                    self.ak_icon = arcade.Sprite('../../assets/textures/guns/AK-47/icon2.png', scale=0.1)
                    self.ak_icon.right = SCREEN_WIDTH - 5
                    self.ak_icon.bottom = half_height + 5
                    self.usp_icon = arcade.Sprite('../../assets/textures/guns/USP/icon2.png', scale=0.1)
                    self.usp_icon.right = SCREEN_WIDTH - 5
                    self.usp_icon.top = half_height - 5
                    self.icons_list.append(self.ak_icon)
                    self.icons_list.append(self.usp_icon)
                elif self.draw_unlock == (1600, 1100) and not(self.texture_slices['3'] == self.texture_slices['5'] == self.texture_slices['7'] == self.texture_slices['A']):
                    self.button_to_press.text = 'Отсутствует питание'
                    arcade.load_sound('../../assets/sounds/background/error.wav').play()
                elif self.draw_unlock == (1600, 1100) and (self.texture_slices['3'] == self.texture_slices['5'] == self.texture_slices['7'] == self.texture_slices['A']):
                    self.button_to_press.text = 'Нажмите "Е", чтобы использовать.'
                    arcade.stop_sound(self.music_player_bg)
                    if hasattr(self.player, 'get_damage_music') and self.player.get_damage_music:
                        try:
                            arcade.stop_sound(self.player.get_damage_music)
                        except:
                            pass
                    if hasattr(self, 'steps_player') and self.steps_player:
                        try:
                            arcade.stop_sound(self.steps_player)
                        except:
                            pass

                    with open('../../data/data.txt', 'w', encoding='utf-8') as f:
                        f.write(f"{self.current_stage + 1}\n")
                        f.write(f"{self.player.health}\n")
                        f.write(f"{self.usp.patrons}/{self.usp.magazines}\n")
                        if hasattr(self, 'usp_icon'):
                            f.write(f"{self.kalash.patrons}/{self.kalash.magazines}\n")
                    with open('../../data/statistics.txt', 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f.readlines()]
                        old_shoot = int(lines[0])
                        old_h = int(lines[1])
                        old_b = int(lines[2])

                    with open('../../data/statistics.txt', 'w', encoding='utf-8') as f:
                        f.write(f"{self.shoot + old_shoot}\n")
                        f.write(f"{self.headshot + old_h}\n")
                        f.write(f"{self.bodyshot + old_b}\n")
                    self.flag2 = True








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
        row, col = randint(1, self.map_height - 1), randint(1, self.map_width - 1)
        while self.text_map[row][col] != '.':
            row, col = randint(1, self.map_height - 1), randint(1, self.map_width - 1)
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
            False,
            True
        )
        spr.set_pathfinding(self.pathfinding)
        self.enemies.append(spr)


if __name__ == '__main__':
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "CS 3")
    start_view = Stage3()
    window.show_view(start_view)
    window.set_fullscreen(True)
    window.run()