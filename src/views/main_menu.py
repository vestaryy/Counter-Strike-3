import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from src.player.settings import *
import arcade
import random
from arcade.particles import FadeParticle, Emitter, EmitBurst
from arcade.gui import UIManager, UIFlatButton, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout


def gravity_drag(p):
    p.change_y += -0.02
    p.change_x *= 0.97
    p.change_y *= 0.97


class FallingObject(arcade.Sprite):
    def __init__(self, texture,  game, scale=1.0):
        super().__init__(texture, scale)
        self.game = game
        self.center_x = random.randint(SCREEN_WIDTH // 2 - 400,SCREEN_WIDTH)
        self.center_y = SCREEN_HEIGHT
        self.speed_y = random.uniform(-150, -200)
        self.speed_x = 0
        self.rotation_speed = random.uniform(-3, 3)
        self.engine = arcade.PhysicsEngineSimple(self, self.game.li)

        if SCREEN_WIDTH // 2 - 400 <= self.center_x <= SCREEN_WIDTH // 2 - 380:
            self.rotation_speed = abs(self.rotation_speed)


    def update(self, dt):
        super().update()
        self.engine.update()
        self.angle += self.rotation_speed
        self.center_y += self.speed_y * dt
        self.center_x += self.speed_x * dt

class NewGamePreview(arcade.View):
    def on_show_view(self) -> None:
        self.background_color = (0,0,0)
        self.airoport_sound = arcade.load_sound('../../assets/sounds/background/aroport.mp3')
        self.edward_sound = arcade.load_sound('../../assets/sounds/background/edward.mp3')
        self.some_time_passed = arcade.load_sound('../../assets/sounds/background/some time passed.mp3')
        self.aircrash_sound = arcade.load_sound(
            '../../assets/sounds/background/plane-crash-disturbing-sound-fx-78bpm-f-minor_GqnJUo0r.wav')
        self.surv_sound = arcade.load_sound('../../assets/sounds/background/surv.mp3')
        self.slide1 = arcade.load_texture('../../assets/textures/elements/slide1.png')
        self.slide2 = arcade.load_texture('../../assets/textures/elements/slide2.png')
        self.slide3 = arcade.load_texture('../../assets/textures/elements/slide3.png')
        self.slide4 = arcade.load_texture('../../assets/textures/elements/slide4.png')
        self.slide5 = arcade.load_texture('../../assets/textures/elements/slide5.png')
        self.background_slide = arcade.load_texture('../../assets/textures/sky&walls/light.png')
        self.timer_for_slide = 0
        self.current_slide = self.background_slide
        self.start_game = False
        with open('../../data/data.txt', 'w', encoding='utf-8') as f:
            f.write('1\n')

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.current_slide, arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

    def on_update(self, delta_time: float):
        if self.start_game:
            return

        self.timer_for_slide += delta_time
        if self.current_slide == self.background_slide and self.timer_for_slide > 1.5:
            self.current_slide = self.slide1
            self.timer_for_slide = 0
            self.player = self.airoport_sound.play()
        if self.current_slide == self.slide1 and self.timer_for_slide > 15:
            self.current_slide = self.slide2
            self.timer_for_slide = 0
            self.player = self.edward_sound.play()
        if self.current_slide == self.slide2 and self.timer_for_slide > 12:
            self.current_slide = self.slide3
            self.timer_for_slide = 0
            self.player = self.some_time_passed.play()
        if self.current_slide == self.slide3 and self.timer_for_slide > 5:
            self.current_slide = self.slide4
            self.timer_for_slide = 0
            self.player = self.aircrash_sound.play()
        if self.current_slide == self.slide4 and self.timer_for_slide > 10:
            self.current_slide = self.slide5
            self.timer_for_slide = 0
            self.player = self.surv_sound.play()
        if self.current_slide == self.slide5 and self.timer_for_slide > 15:
            self.start_game = True
            arcade.stop_sound(self.player)
            from src.views.stage1 import Stage1
            game_view = Stage1()
            self.window.show_view(game_view)

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.SPACE:
            self.current_slide = self.background_slide
            arcade.stop_sound(self.player)
            self.start_game = True
            from src.views.stage1 import Stage1
            game_view = Stage1()
            self.window.show_view(game_view)

class MainMenu(arcade.View):
    def make_explosion(self, x, y):

        spark_emitter = Emitter(
            center_xy=(x, y),
            emit_controller=EmitBurst(100),
            particle_factory=lambda _: FadeParticle(
                filename_or_texture=random.choice(self.spark_textures),
                change_xy=arcade.math.rand_in_circle((0.0, 0.0), 8.0),
                lifetime=random.uniform(0.8, 1.5),
                start_alpha=255,
                end_alpha=0,
                scale=random.uniform(0.4, 0.7),
                mutation_callback=gravity_drag,
            ),
        )

        smoke_emitter = Emitter(
            center_xy=(x, y),
            emit_controller=EmitBurst(30),
            particle_factory=lambda _: FadeParticle(
                filename_or_texture=self.smoke_texture,
                change_xy=arcade.math.rand_in_circle((0.0, 0.0), 3.0),
                lifetime=random.uniform(1.5, 2.5),
                start_alpha=180,
                end_alpha=0,
                scale=random.uniform(0.8, 1.2),
            ),
        )

        self.emitters.append(spark_emitter)
        self.emitters.append(smoke_emitter)
    def __init__(self):
        super().__init__()
        #self.window.background_color = (190, 150, 0)

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)

        self.setup_widgets()

        self.manager.add(self.anchor_layout)

        self.background_sprite = arcade.Sprite('../../assets/textures/elements/123.jpg', 2.1 - SCREEN_SCALE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.background_sprite_list = arcade.SpriteList()
        self.background_sprite_list.append(self.background_sprite)
        self.background_sound = arcade.load_sound('../../assets/sounds/background/backgroudmaunmenu.wav')
        self.background_player = arcade.play_sound(self.background_sound, loop=True)

        self.world_camera = arcade.camera.Camera2D()
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,
            max_amplitude=15.0,
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )
        self.timer_camera = 0
        self.spawn_timer = 0
        self.emitters = []

        self.spark_textures = [
            arcade.make_soft_circle_texture(8, arcade.color.RED),
            arcade.make_soft_circle_texture(8, arcade.color.ORANGE),
            arcade.make_soft_circle_texture(8, arcade.color.YELLOW),
            arcade.make_soft_circle_texture(8, arcade.color.WHITE),
        ]

        self.smoke_texture = arcade.make_soft_circle_texture(15, arcade.color.GRAY, 200, 100)
        self.clicked_sound = arcade.load_sound('../../assets/sounds/background/clicked.mp3')

        self.sprite_button_new_game = arcade.SpriteSolidColor(350, 100)
        (self.sprite_button_new_game.left,
         self.sprite_button_new_game.right,
         self.sprite_button_new_game.bottom,
         self.sprite_button_new_game.top) = 25, 375, SCREEN_HEIGHT - 355, SCREEN_HEIGHT - 255





        self.li = arcade.SpriteList()
        self.li.append(self.sprite_button_new_game)

        self.falling_textures = [
            arcade.load_texture('../../assets/textures/elements/1672965555_grizly-club-p-tekstura-puli-1.png')
        ]


        self.falling_objects = arcade.SpriteList()

    def setup_widgets(self):
        self.button_style = {
            'normal': UIFlatButton.UIStyle(
                font_size=20,
                font_name='Simsun',
                font_color=arcade.color.BLACK,
                bg=(0,0,0,0),
                border=arcade.color.BLACK,
                border_width=2,
            ),
            'hover': UIFlatButton.UIStyle(
                font_size=20,
                font_name='Simsun',
                font_color=arcade.color.GRAY,
                bg=(0, 0, 0, 0),
                border=arcade.color.GRAY,
                border_width=2,
            ),
            'press': UIFlatButton.UIStyle(
                font_size=20,
                font_name='Simsun',
                font_color=arcade.color.BLACK,
                bg=(0, 0, 0, 0),
                border=arcade.color.BLACK,
                border_width=2,
            ),
            'disabled': UIFlatButton.UIStyle(
                font_size=20,
                font_name='Simsun',
                font_color=arcade.color.BLACK,
                bg=(0, 0, 0, 0),
                border=arcade.color.BLACK,
                border_width=2,
            )
        }
        label = UILabel(
            text="Counter-Strike-3",
            font_name='SimSun',
            font_size=60,
            text_color=arcade.color.BLACK,
            bold=True
        )

        self.anchor_layout.add(
            child=label,
            anchor_x="left",
            anchor_y="top",
            align_x=250,
            align_y=-35
        )

        start_game_button = UIFlatButton(text="Новая игра",
                                         width=350,
                                         height=100,
                                         style=self.button_style)
        start_game_button.on_click = self.new_game

        continue_button = UIFlatButton(text="Продолжить игру",
                                       width=350,
                                       height=100,
                                       style=self.button_style,
                                       multiline=True)
        continue_button.on_click = self.continue_game

        training_button = UIFlatButton(text="Тренировка",
                                       width=350,
                                       height=100,
                                       style=self.button_style,
                                       multiline=True)
        training_button.on_click = self.training_game

        leave_button = UIFlatButton(text="Выйти",
                                       width=350,
                                       height=100,
                                       style=self.button_style,
                                       multiline=True)
        leave_button.on_click = self.leave_game


        self.anchor_layout.add(
            child=start_game_button,
            anchor_x="left",
            anchor_y="top",
            align_x=25,
            align_y=-255
        )
        self.anchor_layout.add(
            child=continue_button,
            anchor_x="left",
            anchor_y="top",
            align_x=25,
            align_y=-410
        )
        self.anchor_layout.add(
            child=training_button,
            anchor_x="left",
            anchor_y="top",
            align_x=25,
            align_y=-565
        )
        self.anchor_layout.add(
            child=leave_button,
            anchor_x="left",
            anchor_y="top",
            align_x=25,
            align_y=-720
        )
    def new_game(self, event):
        self.clicked_sound.play()
        arcade.stop_sound(self.background_player)

        veiw = NewGamePreview()
        self.window.show_view(veiw)

    def continue_game(self, event):
        self.clicked_sound.play()

        with open('../../data/data.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            if not lines:
                return
            arcade.stop_sound(self.background_player)
            if lines[0] == '1':
                from src.views.stage1 import Stage1
                game_view = Stage1()
            if lines[0] == '2':
                from src.views.stage2 import Stage2
                game_view = Stage2()
            if lines[0] == '3':
                from src.views.stage3 import Stage3
                game_view = Stage3()
            if lines[0] == '4':
                from src.views.stage4 import Stage4
                game_view = Stage4()



            self.window.show_view(game_view)

    def training_game(self, event):
        self.clicked_sound.play()
        arcade.stop_sound(self.background_player)
        self.manager.disable()
        from src.views.training import Training
        training_view = Training()
        self.window.show_view(training_view)

    def leave_game(self, event):
        self.clicked_sound.play()
        self.window.close()





    def on_draw(self):
        self.clear()
        self.camera_shake.update_camera()
        self.world_camera.use()
        self.camera_shake.readjust_camera()

        self.background_sprite_list.draw()


        for emitter in self.emitters:
            emitter.draw()

        self.manager.draw()
        self.falling_objects.draw()

    def on_update(self, delta_time: float) -> bool | None:
        self.spawn_timer += delta_time
        self.camera_shake.update(delta_time)
        self.timer_camera += delta_time

        for obj in self.falling_objects:
            obj.update(delta_time)
            if not arcade.check_for_collision(obj, self.background_sprite):
                self.falling_objects.remove(obj)

        if self.spawn_timer > 1:
            self.falling_objects.append(FallingObject(random.choice(self.falling_textures), self, 0.1))
            self.spawn_timer = 0




        emitters_to_remove = []
        for emitter in self.emitters:
            emitter.update(delta_time)

            if emitter.can_reap():
                emitters_to_remove.append(emitter)

        for emitter in emitters_to_remove:
            self.emitters.remove(emitter)

        if self.timer_camera >= 60:
            self.camera_shake.start()
            self.timer_camera = 0



    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.make_explosion(x, y)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "CS 3")
    window.set_fullscreen(True)
    start_view = MainMenu()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()