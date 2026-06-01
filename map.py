import random
#https://indienova.com/indie-game-development/procedural-content-generation-tile-based-random-cave-map/
import random
from collections import deque
from grid import Vec2
from util import load_image
from events import DamageEvent

WALL = 1 
VOID = 0 #空
EXIT = 3

SPIKE = 1
CANDLE = 1

class Map:

    def __init__(self, width, height, camera):

        self.width = width
        self.height = height
        self.camera = camera

        self.terrain = []
        self.traps = []
        self.deco = []

        self.occupants = {}  # 改为字典：{(x, y): pawn_object}

        self.tiles = [
            load_image("arts/sprite/tiles/tile0.png",(32,32)),
            load_image("arts/sprite/tiles/tile1.png",(32,32)),
            load_image("arts/sprite/tiles/tile2.png",(32,32)),
            load_image("arts/sprite/tiles/tile3.png",(32,32)),
            load_image("arts/sprite/tiles/tile4.png",(32,32)),
        ]

        self.traptile = {"spike":load_image("arts/sprite/tiles/trap1.png",(32,32)),}

        self.decotile = [
            load_image("arts/sprite/tiles/tile0.png",(32,32)),
            load_image("arts/sprite/tiles/deco1.png",(32,32)),
        ]

    # =========================
    # 地图生成入口
    # =========================

    def generate_map(self):

        self.init_random()
        # self.run_cellular_automata()

        start = (1, self.height // 2)
        end = (self.width - 2, self.height // 2)

        # path = self.generate_main_path(start, end)

        # self.carve_path(path)

        # self.ensure_connectivity(start)

        self.place_exit()

        self.generate_traps()

    # =========================
    # 随机初始化
    # =========================

    def init_random(self):

        self.terrain = []
        self.traps = [[0]*self.width for _ in range(self.height)]
        self.deco = [[0]*self.width for _ in range(self.height)]

        for y in range(self.height):

            row = []

            for x in range(self.width):

                if x == 0 or y == 0 or x == self.width-1 or y == self.height-1:
                    row.append(WALL)
                else:
                    make_wall = False

                    # 基础 5% 墙
                    if random.random() < 0.05:
                        make_wall = True

                    # 如果左边是墙，则额外 20% 延伸
                    elif row[-1] == WALL and random.random() < 0.20:
                        make_wall = True

                    row.append(WALL if make_wall else VOID)

            self.terrain.append(row)

    # =========================
    # Cellular Automata
    # =========================

    def run_cellular_automata(self):
        for _ in range(4):
            self.smooth()

    def smooth(self):

        new_map = [[0]*self.width for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):

                r1 = self.count_walls(x, y, 1)
                r2 = self.count_walls(x, y, 2)

                if r1 >= 5 or r2 <= 4:
                    new_map[y][x] = WALL
                else:
                    new_map[y][x] = VOID

        self.terrain = new_map

    def count_walls(self, x, y, r):
        count = 0
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                # 不跳过自身，包含中心格
                nx = x + dx
                ny = y + dy
                if nx < 0 or ny < 0 or nx >= self.width or ny >= self.height:
                    count += 1
                elif self.terrain[ny][nx] == WALL:
                    count += 1
        return count

    # =========================
    # 主路径生成
    # =========================

    def generate_main_path(self,start,end):

        x,y = start
        path = [(x,y)]

        while (x,y) != end:

            dx = end[0] - x
            dy = end[1] - y

            options = []

            if dx > 0: options.append((1,0))
            if dx < 0: options.append((-1,0))
            if dy > 0: options.append((0,1))
            if dy < 0: options.append((0,-1))

            if random.random() < 0.3:
                options += [(1,0),(-1,0),(0,1),(0,-1)]

            step = random.choice(options)

            x += step[0]
            y += step[1]

            x = max(1,min(self.width-2,x))
            y = max(1,min(self.height-2,y))

            path.append((x,y))

        return path

    # =========================
    # 挖掘路径
    # =========================

    def carve_path(self,path):

        for (x,y) in path:

            for dy in range(-1,2):
                for dx in range(-1,2):

                    nx = x + dx
                    ny = y + dy

                    if 0 < nx < self.width-1 and 0 < ny < self.height-1:
                        self.terrain[ny][nx] = VOID

    # =========================
    # 连通性检查
    # =========================

    def ensure_connectivity(self,start):

        reachable = self.flood_fill(start)

        for y in range(self.height):
            for x in range(self.width):

                if self.terrain[y][x] == VOID and (x,y) not in reachable:
                    self.terrain[y][x] = WALL

    def flood_fill(self,start):

        stack = [start]
        visited = set()

        while stack:

            x,y = stack.pop()

            if (x,y) in visited:
                continue

            visited.add((x,y))

            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:

                nx = x + dx
                ny = y + dy

                if 0 <= nx < self.width and 0 <= ny < self.height:

                    if self.terrain[ny][nx] == VOID:
                        stack.append((nx,ny))

        return visited

    # =========================
    # 出口
    # =========================

    def place_exit(self):
        self.terrain[62][1]= EXIT
        self.terrain[62][14]= EXIT

    # =========================
    # 陷阱生成
    # =========================

    # def generate_traps(self):

    #     for y in range(1,self.height-1):
    #         for x in range(1,self.width-1):

    #             if self.terrain[y][x] == VOID and self.terrain[y+1][x] == WALL:

    #                 if random.random() < 0.05:
    #                     self.traps[y][x] = SPIKE

    #                 elif random.random() < 0.1:
    #                     self.deco[y][x] = CANDLE

    def generate_traps(self):
        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                if self.terrain[y][x] == VOID and self.terrain[y+1][x] == WALL:
                    
                    if random.random() < 0.05:
                        self.traps[y][x] = SpikeTrap(Vec2(x, y), damage=2)  # ← 存实例
                    
                    elif random.random() < 0.1:
                        self.deco[y][x] = CANDLE  # deco 不需要行为，常量即可
    # =========================
    # Tile查询
    # =========================

    def get_terrain(self, pos):
        return self.terrain[pos.y][pos.x]

    def get_trap(self, pos):
        return self.traps[pos.y][pos.x]

    # =========================
    # 渲染
    # =========================

    def draw_map(self, screen):

        for y in range(self.height):
            for x in range(self.width):

                tile_id = self.terrain[y][x]
                tile = self.tiles[tile_id]

                screen_pos = self.camera.apply(Vec2(x, y))
                screen.blit(tile, screen_pos)

                trap = self.traps[y][x]
                if trap:
                    tile = self.traptile[trap.type_id]   # ← 用 type_id 查贴图
                    screen.blit(tile, screen_pos)

                deco_id = self.deco[y][x]
                if deco_id:
                    tile = self.decotile[deco_id]
                    screen.blit(tile, screen_pos)

                # if tile_id == 0 :
                #     text = f"{x},{y}"
                #     text_img = self.small_font.render(text, True, GRAY)
                #     screen.blit(text_img, screen_pos)

    def get_occupant(self, pos):
        return self.occupants.get(pos, None)
    
    def is_occupied(self, pos):
            # 转换为元组或字符串，因为 Vec2 对象通常不能直接作为字典的 key (除非你重写了 __hash__)
            return (pos.x, pos.y) in self.occupants
    
    def is_walkable(self, pos):
        """地面生物可站立:地面tile且无占用"""
        return self.is_wall(pos + Vec2(0,1))  and not self.is_wall(pos)       # 自己位置不是墙且脚下是墙
    
    def is_flyable(self, pos):
        """飞行生物可生成/移动:非墙tile且无占用"""
        return self.get_terrain(pos) != WALL 

    def is_wall(self, pos):
    # 安全检查：如果超出地图范围，一律视为墙
        if pos.x < 0 or pos.x >= self.width or pos.y < 0 or pos.y >= self.height:
            print("index out of range")
            return True
        return self.get_terrain(pos) == WALL
    
    def occupy(self, pos, pawn):
            self.occupants[(pos.x, pos.y)] = pawn

    def destroy_tile(self, pos):
        if self.get_terrain(pos)== WALL:  # 只能破坏墙
            self.terrain[pos.y][pos.x] = VOID


class Trap:
    def __init__(self, pos):
        self.pos = pos

    def on_enter(self, pawn):
        raise NotImplementedError

class SpikeTrap(Trap):
    def __init__(self, pos, damage):
        super().__init__(pos)
        self.damage = damage
        self.type_id = "spike"

    def on_enter(self, pawn):
        pawn.events.push(DamageEvent(None, pawn, self.damage))  # source=None 表示环境伤害
