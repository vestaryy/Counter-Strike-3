from random import randint
from src.player.settings import *
TEXTURE_SLICES_CACHE = {}


class Enemies:
    @staticmethod
    def precompute_texture_slices_for_all_enemies(enemies_textures_dict):
        global TEXTURE_SLICES_CACHE

        NUM_SLICES_WIDTH = 10
        NUM_SLICES_OFFSET = 10

        TEXTURE_SLICES_CACHE = {}

        for enemy_type, textures_dict in enemies_textures_dict.items():
            for texture_name, texture_obj in textures_dict.items():

                TEXTURE_SLICES_CACHE[f"{enemy_type}_{texture_name}"] = {}

                for width_idx in range(NUM_SLICES_WIDTH):
                    rel_width = 0.1 + 0.9 * (width_idx / max(1, NUM_SLICES_WIDTH - 1))
                    slice_width = max(1, int(texture_obj.width * rel_width))

                    for offset_idx in range(NUM_SLICES_OFFSET):
                        rel_offset = offset_idx / max(1, NUM_SLICES_OFFSET - 1)

                        max_offset = texture_obj.width - slice_width
                        start_x = int(rel_offset * max_offset) if max_offset > 0 else 0

                        cache_key = f"{start_x}_{slice_width}"

                        cropped_texture = texture_obj.crop(start_x, 0, slice_width, texture_obj.height)
                        TEXTURE_SLICES_CACHE[f"{enemy_type}_{texture_name}"][cache_key] = cropped_texture

        return TEXTURE_SLICES_CACHE

    def __init__(self, game_window, enemy_type, dict_textures, pos, scale, floor_offset, cd, can_move, can_attack, respawn_after_die, delete_after_die, hp=100, death_duration=60, max_chase_distance=randint(7, 10) * block_size):
        self.game = game_window
        self.delete_after_die = delete_after_die
        self.has_patrons = True
        self.enemy_type = enemy_type
        self.can_move = can_move
        self.can_attack = can_attack
        if 'shoot' not in dict_textures:
            dict_textures['shoot'] = dict_textures['default']

        self.dict_textures = dict_textures
        self.current_texture_name = 'default'
        self.current_texture = dict_textures[self.current_texture_name]

        self.health = hp
        self.hit_timer = 0
        self.hit_duration = 0.2
        self.is_hit = False

        self.is_dead = False
        self.death_timer = 0
        self.death_duration = death_duration

        self.scale = scale
        self.floor_offset = floor_offset
        self.sprite_radius = 15

        self.x = pos[0] * block_size + block_size // 2
        self.y = pos[1] * block_size + block_size // 2

        self.screen_x = 0
        self.screen_y = 0
        self.proj_width = 0
        self.proj_height = 0
        self.visible = False
        self.ray_index = -1
        self.corrected_distance = 0

        self.map_x = int(pos[0])
        self.map_y = int(pos[1])

        self.left_clip = 0
        self.right_clip = 0
        self.visible_left = 0
        self.visible_right = 0
        self.visible_width = 0
        self.texture_crop_x = 0
        self.texture_crop_width = 1

        self.speed = randint(50, 100)
        self.target_cell = None
        self.next_cell = None
        self.pathfinding = None
        self.path_update_timer = 0
        self.path_update_interval = 0.5

        self.chasing = False
        self.max_chase_distance = max_chase_distance
        self.min_chase_distance = randint(2, 4) * block_size

        self.animation_timer = 0
        self.is_moving = False
        self.walk_phase = 0

        self.last_crop_params = None
        self.cropped_texture_cache = None

        self.move_smoothness = 0.2
        self.velocity_x = 0
        self.velocity_y = 0

        self.stuck_timer = 0
        self.stuck_threshold = 1.5
        self.last_position = (self.x, self.y)
        self.last_target_distance = float('inf')

        self.sprite = arcade.Sprite()
        self.sprite.texture = self.current_texture
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)

        self.attack_cooldown = cd
        self.attack_timer = 0
        self.is_attacking = False
        self.attack_damage = 10
        self.attack_duration = 0.3
        self.attack_animation_timer = 0
        self.attack_sound = arcade.load_sound('../../assets/sounds/guns/enemies12_shoot.wav')
        self.respawn_after_die = respawn_after_die

    def set_pathfinding(self, pathfinding_system):
        self.pathfinding = pathfinding_system

    def get_texture_slice(self, texture_name, crop_x, crop_width):
        texture_width = self.dict_textures[texture_name].width

        abs_start_x = int(crop_x * texture_width)
        abs_slice_width = int(crop_width * texture_width)

        abs_start_x = max(0, min(texture_width - 1, abs_start_x))
        abs_slice_width = max(1, min(texture_width - abs_start_x, abs_slice_width))

        slices_dict = TEXTURE_SLICES_CACHE.get(f"{self.enemy_type}_{texture_name}", {})

        if f"{abs_start_x}_{abs_slice_width}" in slices_dict:
            return slices_dict[f"{abs_start_x}_{abs_slice_width}"]

        best_key = None
        best_distance = float('inf')

        for key in slices_dict.keys():
            cached_start_x, cached_slice_width = map(int, key.split('_'))

            total_distance = abs(abs_start_x - cached_start_x) * 0.3 + abs(abs_slice_width - cached_slice_width) * 0.7

            if total_distance < best_distance:
                best_distance = total_distance
                best_key = key

        if best_key and best_distance < 50:
            return slices_dict[best_key]

        return self.dict_textures[texture_name].crop(abs_start_x, 0, abs_slice_width, self.dict_textures[texture_name].height)

    def update_ai(self, delta_time):
        if not self.game.player_moved:
            return

        if self.is_dead:
            self.death_timer += delta_time
            if self.death_timer >= self.death_duration:
                if self in self.game.enemies and self.delete_after_die:
                    self.game.enemies.remove(self)
            return

        if self.is_attacking and self.is_dead:
            self.is_attacking = False
            self.attack_animation_timer = 0

        if self.attack_timer > 0:
            self.attack_timer -= delta_time

        if self.is_attacking:
            self.attack_animation_timer += delta_time
            if self.attack_animation_timer >= self.attack_duration:
                self.is_attacking = False
                self.attack_animation_timer = 0
                if not self.chasing and not self.is_hit:
                    self.current_texture_name = 'default'

        if self.is_hit:
            self.hit_timer += delta_time
            if self.hit_timer >= self.hit_duration:
                self.is_hit = False
                if not self.chasing and not self.is_attacking:
                    self.current_texture_name = 'default'
                elif self.chasing:
                    self.current_texture_name = 'walk1' if self.walk_phase == 0 else 'walk2'

        self.path_update_timer += delta_time
        self.animation_timer += delta_time


        current_pos = (self.x, self.y)
        pos_change = sqrt((current_pos[0] - self.last_position[0]) ** 2 +
                          (current_pos[1] - self.last_position[1]) ** 2)

        if pos_change < 5:
            self.stuck_timer += delta_time
        else:
            self.stuck_timer = 0
            self.last_position = current_pos

        if self.is_attacking:
            return

        if (self.distance_to_player <= self.min_chase_distance and
                self.attack_timer <= 0 and
                not self.is_hit and
                not self.is_dead and
                self.can_see_player() and self.can_attack):
            self.attack_player()
            return

        if not self.can_move:
            return

        if (self.distance_to_player < self.max_chase_distance and
                self.distance_to_player > self.min_chase_distance and
                not self.is_hit and
                self.can_see_player()):

            self.chasing = True
            self.is_moving = True

            if (self.path_update_timer >= self.path_update_interval or
                self.target_cell is None or
                self.stuck_timer >= self.stuck_threshold) and self.pathfinding:
                self.update_path_to_player()
                self.path_update_timer = 0
                self.stuck_timer = 0

            self.follow_path(delta_time)

            if not self.is_hit and not self.is_attacking and self.animation_timer >= 0.2:
                self.walk_phase = (self.walk_phase + 1) % 2
                new_texture_name = 'walk1' if self.walk_phase == 0 else 'walk2'

                if new_texture_name != self.current_texture_name:
                    self.current_texture_name = new_texture_name
                self.animation_timer = 0
        else:
            self.chasing = False
            self.is_moving = False
            self.target_cell = None
            self.velocity_x = 0
            self.velocity_y = 0
            self.stuck_timer = 0

            if not self.is_hit and not self.is_attacking and self.current_texture_name != 'default':
                self.current_texture_name = 'default'


    def can_see_player(self):
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y

        if self.distance_to_player == 0:
            return True

        dir_x = dx / self.distance_to_player
        dir_y = dy / self.distance_to_player
        steps = int(self.distance_to_player / 10)
        for i in range(1, steps):
            check_x = self.x + dir_x * i * 10
            check_y = self.y + dir_y * i * 10

            map_x = int(check_x // block_size) * block_size
            map_y = int(check_y // block_size) * block_size

            if (map_x, map_y) in self.game.block_map:
                return False

        return True

    def update_path_to_player(self):
        if not self.pathfinding or not self.can_move:
            return



        self.target_cell = self.pathfinding.get_path((int(self.x // block_size), int(self.y // block_size)), (int(self.game.player.x // block_size),
                       int(self.game.player.y // block_size)))

        if self.target_cell == (int(self.x // block_size), int(self.y // block_size)):
            self.target_cell = None
        else:
            target_x = self.target_cell[0] * block_size + block_size // 2
            target_y = self.target_cell[1] * block_size + block_size // 2

            dx = target_x - self.x
            dy = target_y - self.y

            if self.distance_to_player > 0:
                self.velocity_x = dx / self.distance_to_player
                self.velocity_y = dy / self.distance_to_player

    def follow_path(self, delta_time):
        if not self.target_cell or not self.can_move:
            return

        target_x = self.target_cell[0] * block_size + block_size // 2
        target_y = self.target_cell[1] * block_size + block_size // 2

        dx_to_target = target_x - self.x
        dy_to_target = target_y - self.y
        distance_to_target = sqrt(dx_to_target * dx_to_target + dy_to_target * dy_to_target)

        if distance_to_target < 10:
            self.update_path_to_player()
            return

        target_dx = dx_to_target / distance_to_target if distance_to_target > 0 else 0
        target_dy = dy_to_target / distance_to_target if distance_to_target > 0 else 0

        self.velocity_x += (target_dx - self.velocity_x) * self.move_smoothness
        self.velocity_y += (target_dy - self.velocity_y) * self.move_smoothness

        speed_magnitude = sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        if speed_magnitude > 0:
            self.velocity_x /= speed_magnitude
            self.velocity_y /= speed_magnitude

        final_dx = self.velocity_x * self.speed * delta_time
        final_dy = self.velocity_y * self.speed * delta_time

        if self.can_move_to(self.x + final_dx, self.y + final_dy):
            self.x += final_dx
            self.y += final_dy
        else:
            self.try_avoid_obstacle(final_dx, final_dy, delta_time)
            self.stuck_timer = 0

    def try_avoid_obstacle(self, dx, dy, delta_time):
        angles = [pi / 4, -pi / 4, pi / 2, -pi / 2, 3 * pi / 4, -3 * pi / 4]

        for angle in angles:
            new_dx = dx * cos(angle) - dy * sin(angle)
            new_dy = dx * sin(angle) + dy * cos(angle)

            magnitude = sqrt(new_dx ** 2 + new_dy ** 2)
            if magnitude > 0:
                new_dx = new_dx / magnitude * self.speed * delta_time * 0.7
                new_dy = new_dy / magnitude * self.speed * delta_time * 0.7

                if self.can_move_to(self.x + new_dx, self.y + new_dy):
                    self.x += new_dx
                    self.y += new_dy
                    self.velocity_x = new_dx / (self.speed * delta_time * 0.7)
                    self.velocity_y = new_dy / (self.speed * delta_time * 0.7)
                    break

    def update(self, delta_time):


        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y

        self.distance_to_player = sqrt(dx ** 2 + dy ** 2)
        self.update_ai(delta_time)
        c = int(255 / (1 + self.distance_to_player ** 2 * self.game.light_coeff))
        self.sprite.color = (max(0, c), max(0, c), max(0, c))

        if self.distance_to_player < 10:
            self.visible = False
            self.sprite.visible = False
            return


        delta_angle = atan2(dy, dx) - self.game.player.angle

        while delta_angle > pi:
            delta_angle -= 2 * pi
        while delta_angle < -pi:
            delta_angle += 2 * pi


        left_angle = atan2(dy, dx) -  atan2(self.sprite_radius, self.distance_to_player)
        right_angle = atan2(dy, dx) +  atan2(self.sprite_radius, self.distance_to_player)

        left_delta = left_angle - self.game.player.angle
        right_delta = right_angle - self.game.player.angle

        while left_delta > pi: left_delta -= 2 * pi
        while left_delta < -pi: left_delta += 2 * pi
        while right_delta > pi: right_delta -= 2 * pi
        while right_delta < -pi: right_delta += 2 * pi

        left_ray_index = int((left_delta + half_FOV) / delta_ray)
        right_ray_index = int((right_delta + half_FOV) / delta_ray)

        right_ray_index = min(num_rays - 1, right_ray_index)

        if right_ray_index < 0 or left_ray_index >= num_rays or left_ray_index > right_ray_index:
            self.visible = False
            self.sprite.visible = False
            return

        self.left_clip = left_ray_index
        self.right_clip = right_ray_index

        visible_left = max(0, left_ray_index)
        visible_right = min(num_rays - 1, right_ray_index)

        if visible_left > visible_right:
            self.visible = False
            self.sprite.visible = False
            return

        visible_segments = []
        current_segment_start = -1

        for ray_idx in range(left_ray_index, right_ray_index + 1):
            ray_angle = self.game.player.angle - half_FOV + ray_idx * delta_ray
            ray_dir_x = cos(ray_angle)
            ray_dir_y = sin(ray_angle)

            wall_dist = self.get_wall_distance_in_direction(ray_dir_x, ray_dir_y)

            sprite_ray_dist = self.distance_to_player * cos(atan2(self.y - self.game.player.y, self.x - self.game.player.x) - ray_angle)

            if sprite_ray_dist < wall_dist + 5:
                if current_segment_start == -1:
                    current_segment_start = ray_idx
            else:
                if current_segment_start != -1:
                    visible_segments.append((current_segment_start, ray_idx - 1))
                    current_segment_start = -1

        if current_segment_start != -1:
            visible_segments.append((current_segment_start, right_ray_index))

        if not visible_segments:
            self.visible = False
            self.sprite.visible = False
            return

        largest_segment = max(visible_segments, key=lambda seg: seg[1] - seg[0])
        self.visible_left, self.visible_right = largest_segment
        self.visible_width = self.visible_right - self.visible_left + 1

        total_width = self.right_clip - self.left_clip + 1

        if total_width > 0:
            visible_start_relative = max(0, self.visible_left - self.left_clip)
            self.texture_crop_x = visible_start_relative / total_width

            self.texture_crop_width = self.visible_width / total_width
        else:
            self.texture_crop_x = 0
            self.texture_crop_width = 1

        if self.is_attacking:
            texture_to_use = 'shoot'
        else:
            texture_to_use = self.current_texture_name


        if (self.last_crop_params != f"{self.texture_crop_x:.3f}_{self.texture_crop_width:.3f}_{texture_to_use}" or
                self.cropped_texture_cache is None):

            self.current_texture = self.get_texture_slice(
                texture_to_use,
                self.texture_crop_x,
                self.texture_crop_width
            )

            self.last_crop_params = f"{self.texture_crop_x:.3f}_{self.texture_crop_width:.3f}_{texture_to_use}"
            self.cropped_texture_cache = self.current_texture
        else:
            self.current_texture = self.cropped_texture_cache

        self.corrected_distance = self.distance_to_player * cos(delta_angle)
        self.ray_index = self.visible_left + self.visible_width // 2

        current_scale = self.scale
        if self.is_dead:
            current_scale = 0.2

        self.proj_height = coefficent / (self.corrected_distance + 0.0001) * current_scale
        texture_ratio = self.current_texture.width / self.current_texture.height
        self.proj_width = self.proj_height * texture_ratio


        current_floor_offset = self.floor_offset
        if self.is_dead:
            current_floor_offset = 2
        self.screen_y = half_height - self.game.player.ver_a - self.proj_height * current_floor_offset
        self.screen_x = self.visible_left * scale

        self.visible = True

        self.sprite.texture = self.current_texture
        self.sprite.center_x = self.screen_x + self.proj_width / 2
        self.sprite.center_y = self.screen_y + self.proj_height / 2
        self.sprite.width = self.proj_width
        self.sprite.height = self.proj_height
        self.sprite.visible = True

        if (self.screen_x < self.game.player.aim_x < self.screen_x + self.proj_width and
                self.screen_y < self.game.player.aim_y < self.screen_y + self.proj_height * 0.8):
            return 'bodyshot'

        if (self.screen_x + self.proj_width * 0.3 < self.game.player.aim_x <
                self.screen_x + self.proj_width * 0.3 + self.proj_width * 0.4 and
                self.screen_y + self.proj_height * 0.8 < self.game.player.aim_y <
                self.screen_y + self.proj_height * 0.8 + self.proj_height // 5):
            return 'headshot'

    def get_damage(self, damage, part):
        self.health -= damage if self.enemy_type != 'b' else -damage
        if self.enemy_type == 'b' and self.game.current_stage == 1:
            if self.health > 200 and (700, 700) in self.game.block_map:
                self.game.block_map.remove((700, 700))

        self.is_hit = True
        self.hit_timer = 0

        if part in self.dict_textures:
            self.current_texture_name = part

        if self.health <= 0:
            self.die()
            return

        self.chasing = False
        self.is_moving = False
        self.target_cell = None

    def attack_player(self):
        self.is_attacking = True
        self.attack_animation_timer = 0
        self.attack_timer = self.attack_cooldown
        self.current_texture_name = 'shoot'
        self.chasing = False
        self.is_moving = False
        self.target_cell = None
        self.velocity_x = 0
        self.velocity_y = 0

        self.game.player.get_damage(self, self.attack_damage)
        self.attack_sound.play()

    def die(self):
        if self.respawn_after_die:
            self.game.add_random_enemy()
        self.is_dead = True
        self.death_timer = 0
        self.current_texture_name = 'death'
        self.chasing = False
        self.is_moving = False
        self.target_cell = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_attacking = False

    def can_move_to(self, x, y):
        for i in range(8):
            check_x = x + self.sprite_radius * cos(2 * pi * i / 8)
            check_y = y + self.sprite_radius * sin(2 * pi * i / 8)

            map_x = check_x // block_size * block_size
            map_y = check_y // block_size * block_size

            if (map_x, map_y) in self.game.block_map:
                return False

        for other_enemy in self.game.enemies:
            if other_enemy != self:
                dx = x - other_enemy.x
                dy = y - other_enemy.y

                if sqrt(dx * dx + dy * dy) < self.sprite_radius * 2:
                    return False

        return True

    def get_wall_distance_in_direction(self, ray_dir_x, ray_dir_y):
        map_x = int(self.game.player.x // block_size)
        map_y = int(self.game.player.y // block_size)

        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float('inf')
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float('inf')

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (self.game.player.x - map_x * block_size) * delta_dist_x / block_size
        else:
            step_x = 1
            side_dist_x = ((map_x + 1) * block_size - self.game.player.x) * delta_dist_x / block_size

        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (self.game.player.y - map_y * block_size) * delta_dist_y / block_size
        else:
            step_y = 1
            side_dist_y = ((map_y + 1) * block_size - self.game.player.y) * delta_dist_y / block_size

        while True:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                distance = side_dist_x - delta_dist_x
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                distance = side_dist_y - delta_dist_y

            map_coord_x = map_x * block_size
            map_coord_y = map_y * block_size

            if (map_coord_x, map_coord_y) in self.game.block_map:
                return distance * block_size

            if map_x < 0 or map_x >= self.game.map_width or map_y < 0 or map_y >= self.game.map_height:
                break

        return float('inf')


    def draw(self):
        # if self.visible:
        self.sprite_list.draw()

