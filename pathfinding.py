from main import *
from enemy import *
from typing import List, Tuple, Dict, Set
from collections import deque
from functools import lru_cache

class PathFinding:
    def __init__(self, game):
        self.game = game
        self.map = game.text_map
        self.ways = [(-1, 0), (0, -1), (1, 0), (0, 1),
                     (-1, -1), (1, -1), (1, 1), (-1, 1)]
        self.graph: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        self.build_graph()

    def build_graph(self):
        for y, row in enumerate(self.map):
            for x, col in enumerate(row):
                if col != 'W':
                    neighbors = []
                    for dx, dy in self.ways:
                        nx, ny = x + dx, y + dy
                        if 0 <= ny < len(self.map) and 0 <= nx < len(row):
                            if self.map[ny][nx] != 'W':
                                neighbors.append((nx, ny))
                    self.graph[(x, y)] = neighbors

    @lru_cache()
    def get_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[int, int]:
        if start == goal:
            return goal

        gy, gx = goal[1], goal[0]
        if (0 <= gy < len(self.map) and 0 <= gx < len(self.map[0]) and
                self.map[gy][gx] == 'W'):
            goal = self.find_nearest_walkable(goal)
            if goal is None:
                return start

        visited = self.bfs(start, goal)
        path = self.reconstruct_path(start, goal, visited)

        if path and len(path) > 1:
            return path[1]
        return start

    def bfs(self, start, goal):
        queue = deque([start])
        visited = {start: None}

        while queue:
            current = queue.popleft()

            if current == goal:
                break

            for neighbor in self.graph.get(current, []):
                if neighbor not in visited:
                    if self.is_valid_move(current, neighbor):
                        queue.append(neighbor)
                        visited[neighbor] = current

        return visited

    def is_valid_move(self, from_cell, to_cell):
        fx, fy = from_cell
        tx, ty = to_cell

        if abs(fx - tx) + abs(fy - ty) == 1:
            return True

        if self.map[ty][fx] != 'W' and self.map[fy][tx] != 'W':
            return True

        return False

    def reconstruct_path(self, start, goal, visited):
        if goal not in visited:
            return None

        path = []
        current = goal

        while current != start:
            path.append(current)
            current = visited[current]

        path.append(start)
        path.reverse()
        return path

    def find_nearest_walkable(self, cell):
        x, y = cell
        max_radius = 5

        for radius in range(1, max_radius + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = x + dx, y + dy
                    if (0 <= ny < len(self.map) and 0 <= nx < len(self.map[0])):
                        if self.map[ny][nx] != 'W':
                            return (nx, ny)
        return None

    # def get_direction_to_cell(self, from_pos, to_cell):
    #     target_x = to_cell[0] * block_size + block_size // 2
    #     target_y = to_cell[1] * block_size + block_size // 2
    #
    #     dx = target_x - from_pos[0]
    #     dy = target_y - from_pos[1]
    #
    #     distance = sqrt(dx * dx + dy * dy)
    #     if distance > 0:
    #         return dx / distance, dy / distance
    #     return 0, 0