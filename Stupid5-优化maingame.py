import pygame
import sys
import random
import logging
import json

def load_events_from_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_events = json.load(f)
    
    # 将字符串形式的 condition 编译成 lambda 表达式
    def compile_condition(cond_str):
        if cond_str == "always":
            return lambda p: True
        else:
            return lambda p: eval(cond_str, {}, {"player": p})

    for event in raw_events:
        for opt in event["options"]:
            cond_str = opt.get("condition", "always")
            opt["condition"] = compile_condition(cond_str)

    return raw_events

# 初始化加载
events = load_events_from_json("events.json")

# 初始化 Pygame
pygame.init()
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simplicity is All You Need")
clock = pygame.time.Clock()
pygame.mixer.init()  # 初始化音频系统
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# # 载入背景音乐
# try:
#     pygame.mixer.music.load("assets/Strange world.mp3")  # 替换为你的音乐文件路径
#     pygame.mixer.music.set_volume(1)  # 设置音量（0.0 到 1.0）
#     pygame.mixer.music.play(-1)  # -1 表示循环播放
# except pygame.error as e:
#     print(f"无法载入背景音乐: {e}")

def load_image(path, scale=None):
    try:
        image = pygame.image.load(path)
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except pygame.error:
        logger.error("Failed to load image: %s", path)
        return pygame.Surface((100, 100))  # Fallback

# 字体和颜色
FONT = pygame.font.SysFont("Perfect DOS VGA 437", 24)
CN_FONT = pygame.font.SysFont("萝莉体", 24)
BIGFONT = pygame.font.SysFont("萝莉体", 36)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

# 截获属性变化
class AutoUpdateDict(dict):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.debug = True

    def __setitem__(self, key, value):
        old_value = self.get(key, None)
        super().__setitem__(key, value)
        if self.debug:
            logger.debug("%s changed from %s to %s", key, old_value, value)
        self.parent.on_stat_change()

    def update(self, *args, mode="set", **kwargs):
        updates = dict(*args, **kwargs)
        for key, value in updates.items():
            if mode == "add":
                self[key] = self.get(key, 0) + value
            else:  # mode == "set"
                self[key] = value

class Player:
    #S.T.U.P.I.D.属性
    attribute_names = {
    'S': 'Speech',           # 辩论 ——你的说话能力 0-你不能说话 1-5你只能说“是”或“否” 6-10你只能说5个字以内的句子 11-15你可以说话，但不能嘴炮 16+能嘴炮
    'T': 'Thoughtfulness',   # 思考性 —— 三思而后行
    'U': 'Understanding',    # 理解力 —— EQ
    'P': 'Perception',       # 感知力 —— 察觉细节、洞察环境 0-瞎子 1-5无法阅读和看清物品属性，标签 6-10远程武器和法杖命中率低 11-15你无法观察到蛛丝马迹 16+你可以看到
    'I': 'Intelligence',     # 智慧 —— IQ 0-脑瘫儿，无法说话 1-5文盲，无常识，会无理由骂人 6-10你的对话会随机用无意义字符替代，且没有学科知识 11-15你无法做很复杂的事/推理 16+你可以理解一切
    'D': 'Diligence'         # 勤奋 —— 努力程度 0-你无法出远门/升级 1-5你无法学习新知识，只能看一行文字 6-10你无法调制/锻造 11-15经验倍率下降 16+你可以做任何
    }
    # 人物头像
    sp_image = load_image('assets/sp.png',(190, 190))

    def __init__(self, base_stats=None):
        if base_stats is None:
            base_stats = {k: 20 for k in ['S', 'T', 'U', 'P', 'I', 'D']}
            base_stats['sp'] = 20
            base_stats['hp'] = 20 # 血量，上限为sp

        self.base_stats = AutoUpdateDict(self, base_stats)  
        self.inventory = Inventory()
        self.equipment = Equipment()
        self.background = None
        self.buffs = set()  
        self.debuffs = set()
        self.warning = 0

    def apply_background(self, background):
        self.background = background["name"]
        for k, v in background.get("modifiers", {}).items():
            if k in self.base_stats:
                self.base_stats[k] += v

    def current_stats(self):
        stats = self.base_stats.copy()
        for item in self.equipment.slots.values():
            if item:
                for attr, bonus in item.modifiers.items():
                    stats[attr] += bonus
        return stats
    
    def on_stat_change(self):
        self.check_tooSmart()
        self.check_tooStupid()
        # self.update_status_effects()
        # self.recalculate_buffs()
        if self.current_stats()['I'] < 6: # 低智力有骂人选项
            if "rude_response" not in self.buffs:
                self.buffs.add("rude_response")
                self.base_stats['sp'] += 50
                self.heal(10)    
                logger.debug("Added buff: rude_response due to Intelligence < 6")
        else:
            if "rude_response" in self.buffs:
                self.buffs.discard("rude_response")
                self.base_stats['sp'] -= 50  
                logger.debug("Removed buff: rude_response due to Intelligence >= 6")

        if self.current_stats()['P'] < 6:  # 低感知无法查看物品属性
            if "no_item_info" not in self.debuffs:
                self.debuffs.add("no_item_info")
                logger.debug("Added debuff: no_item_info due to Perception < 6")
        else:
            if "no_item_info" in self.debuffs:
                self.debuffs.discard("no_item_info")
                logger.debug("Removed debuff: no_item_info due to Perception >= 6")


    def show_warning(self, message, image_path, scale=None):
        screen.fill(BLACK)
        image=load_image(image_path,scale)
        screen.blit(image, (400, 100))
        draw_multiline_dialog(message, start_y=400, font=FONT, color=RED)
        pygame.display.flip()

    
    def check_tooSmart(self):
        stats = self.current_stats()
        intelligence = stats['I']

        Warning_text1 = ["You are too smart!","Stay Simple! Stay Foolish!","Or you will be punished!",]
        Warning_text2 = ["You are too smart!","Your life will end","Please go to hell!",]

        if self.warning == 0 and intelligence > 24:
            self.show_warning(Warning_text1, 'assets/Warning.png',(300, 250))
            self.warning = 1
        if intelligence > 30:
            self.show_warning(Warning_text2, 'assets/Warning.png',(300, 250))
            self.warning = 1
            Outro()
    

    def check_tooStupid(self):
        stats = self.current_stats()
        intelligence = stats['I']

        Warning_text1 = ["You are getting simpler!","Work Harder!",]
        Warning_text2 = ["Contratulation!","You have become a export in simplicity!",]

        if self.warning == 0 and intelligence < 11:
            self.show_warning(Warning_text1, 'assets/magic.png')
            self.warning = 1
        if self.warning != 2 and intelligence < 1:
            self.show_warning(Warning_text2, 'assets/magic.png')
            self.warning = 2


    def take_damage(self, amount):
        self.base_stats['hp'] -= amount
        if self.base_stats['hp'] < 0:
            self.base_stats['hp'] = 0
            screen.fill(BLACK)
            draw_text("You are dead!", 100, 300, BIGFONT, RED)
            pygame.display.flip()
            pygame.time.wait(2000)
            Outro()

    def heal(self, amount):
        self.base_stats['hp'] += amount
        if self.base_stats['hp'] > self.base_stats['sp']:
            self.base_stats['hp'] = self.base_stats['sp']

    def add_debuff(self, debuff_name):
        self.debuffs.add(debuff_name)

    def remove_debuff(self, debuff_name):
        self.debuffs.discard(debuff_name)

    def has_debuff(self, debuff_name):
        return debuff_name in self.debuffs

    def show_buff(self):
        stats = self.current_stats()
        for k, v in stats.items():
            print(f"{k}: {v}")
        print(f"Debuffs: {list(self.debuffs)}")
        
# --- 示例物品 ---
item_data = [
    {"name": "Earphone", "slot": "head", "modifiers": {"P": -5}, "description": "Blocks you from the noisy world."},
    {"name": "Nightcap", "slot": "head", "modifiers": {"D": -3,"U": 1}, "description": "Have a nice sleep!"},
    {"name": "Cat Ear", "slot": "head", "modifiers": {"S": 2,"U":2,"I":-5}, "description": "Neko is cute.", "curse": True},
    {"name": "Glasses", "slot": "eyes", "modifiers": {"P": 3 , "I": 1}, "description": "Improves your sight.But you can't unequip it.","curse": True},
    {"name": "Kaleidoscope", "slot": "eyes", "modifiers": {"P": -5}, "description": "Makes you dizzy."},
    {"name": "C++ Primer", "slot": "book", "modifiers": {"I": 2}, "description": "C++."},
    {"name": "Galgame Guidebook", "slot": "book", "modifiers": {"I": -2,"S":-5,"U":2}, "description": "2d fans."},
    {"name": "Keyboard", "slot": "weapon", "modifiers": {"D": 2}, "description": "Keyboard is a nice weapon."},
    {"name": "Mouth Cannon", "slot": "weapon", "modifiers": {"D": 2}, "description": "F**k words is its bullet."},
    {"name": "404 Not Found", "slot": "passive", "modifiers": {"U": -5}, "description": "Server Under Maintenance."},
    {"name": "Cheat Engine", "slot": "passive", "modifiers": {"I": 10}, "description": "Ultimate Silver builet."},  
    {"name": "Control Key", "slot": "passive", "modifiers": {"I": -5}, "description": "Skip Dialog Automatically."},
    {"name": "Neko Lover", "slot": "passive", "modifiers": {"I": -5,"S": -5}, "description": "Her smile recover your H-power automatically."}, 

]
class Item:
    def __init__(self, name, slot, modifiers, description, curse=None):
        self.name = name
        self.slot = slot
        self.modifiers = modifiers
        self.description = description
        self.curse = curse

    def get_item_data_by_name(item_name):
        for item in item_data:
            if item["name"] == item_name:
                return item
        print(f"[WARNING] 物品 '{item_name}' 不存在于 item_data 中！")
        return None

class Inventory:
    def __init__(self):
        self.items = []
        self.capacity = 20

    def add_item(self, item):
        if len(self.items) < self.capacity:
            self.items.append(item)
            if hasattr(item, 'name'):
                print(f"[DEBUG] 加入背包: {item.name}")
            return True
        print("[DEBUG] 背包已满，无法添加物品")
        return False
    
    def has_item(self, item_name):
        return any(item.name == item_name for item in self.items)
    
    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            print(f"[DEBUG] 加入背包: {item.name}")
            return True
        return False
    
    def remove_item_by_name(self, item_name):
        for item in self.items:
            if item.name == item_name:
                self.items.remove(item)
                print(f"[DEBUG] 移除了物品：{item_name}")
                return True
        print(f"[WARNING] 背包中没有找到物品：{item_name}")
        return False

class Equipment:
    def __init__(self):
        self.slots = {"head": None, "eyes": None, "book": None, "weapon":None,"passive": None}

    def equip(self, item, inventory):
        if item.slot in self.slots:
            if self.slots[item.slot]:
                if self.slots[item.slot].curse:
                    draw_text(f"Cannot unequip cursed item: {self.slots[item.slot].name}", 100, 300, FONT, RED)
                    pygame.display.flip()
                    pygame.time.wait(1000)
                else:
                    inventory.add_item(self.slots[item.slot])
                    self.slots[item.slot] = item
                    inventory.remove_item(item)
            else:
                self.slots[item.slot] = item
                inventory.remove_item(item)
        # 检查是否是Control Key
        if item.name == "Control Key":
            player.buffs.add("skip_dialog")
            print("[DEBUG] 获得buff: skip_dialog")
        if item.name == "Neko Lover":
            player.buffs.add("auto_heal")
            print("[DEBUG] 获得buff: auto_heal")
        player.on_stat_change()        

    def unequip(self, slot_name, inventory):
        if self.slots[slot_name]:
            item = self.slots[slot_name]
            if item.curse:
                print(f"Cannot unequip cursed item: {item.name}")
                pygame.time.wait(1000)
            else:
                inventory.add_item(item)
                self.slots[slot_name] = None                          
                if item.name == "Control Key":# 如果是Control Key，移除buff
                    player.buffs.discard("skip_dialog")
                    print("[DEBUG] 移除buff: skip_dialog")
                if item.name == "Neko Lover":
                    player.buffs.discard("auto_heal")
                    print("[DEBUG] 移除buff: auto_heal")
                player.on_stat_change()

                

# 显示文字
def draw_text(text, x, y, font=FONT, color=WHITE):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))

def attribute_allocation(player):
    points_to_remove = 10  # 初始要移除的点数
    selecting = True
    selected_index = 0
    attributes = ['S', 'T', 'U', 'P', 'I', 'D']

    while selecting:
        screen.fill(BLACK)
        draw_text(f"   S.T.U.P.I.D.({points_to_remove} points to remove)", 20, 20, BIGFONT)
        
        stats = player.base_stats  # 直接用player的属性
        for i, key in enumerate(attributes):
            color = GREEN if selected_index == i else WHITE
            prefix = ">" if selected_index == i else " "
            draw_text(f"{prefix} {key} ({player.attribute_names[key]}): {stats[key]}", 50, 80 + i * 40, FONT, color)

        screen.blit(player.sp_image, (500, 100))  # 把sp画出来

        draw_text("Use Arrow keys to Select and Remove Point", 50, HEIGHT - 120, FONT, GREEN)
        arrow_image = load_image('assets/Arrow.png',(50, 50))  # 加载箭头图片
        screen.blit(arrow_image, (WIDTH-170, HEIGHT - 120-10))  # 显示箭头图片
        draw_text("Remove", WIDTH-100, HEIGHT - 120, FONT, GREEN)
        draw_text("Press ENTER to continue...", 50, HEIGHT - 60, FONT, GREEN)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN :
                    selecting = False
                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(attributes)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(attributes)
                elif event.key == pygame.K_LEFT:
                    if points_to_remove > 0 and stats[attributes[selected_index]] > 0:
                        stats[attributes[selected_index]] -= 1
                        points_to_remove -= 1
                elif event.key == pygame.K_RIGHT:
                    if stats[attributes[selected_index]] < 20:
                        stats[attributes[selected_index]] += 1
                        points_to_remove += 1

def render_ascii_art(screen, label,font_size=18, x=10, y=20, color=WHITE):
    """从 JSON 加载 ASCII Art 并使用字体渲染指定标签的图像"""
    # 加载 ASCII art 数据
    with open("ASCII.json", "r", encoding="utf-8") as f:
        arts = json.load(f)
    
    # 加载字体
    font = pygame.freetype.Font("Saitamaar-Regular.ttf", font_size)

    # 查找对应标签
    art = next((a for a in arts if a["label"] == label), None)
    if not art:
        print(f"[!] 未找到标签: {label}")
        return

    # 渲染每一行
    for i, line in enumerate(art["lines"]):
        font.render_to(screen, (x, y + i * font_size), line, color)

# 像视觉小说一样显示文字
def draw_multiline_dialog(text_lines, start_y=80, font=FONT, color=WHITE, line_spacing=40):
    if "skip_dialog" in player.buffs:
        print("[DEBUG] 跳过剧情对话")
        draw_text("Your Control key helps you skip", 50, HEIGHT - 60, font, GREEN)
        pygame.display.flip()
        pygame.time.wait(2000)
        return  # 直接跳过，不画，不等
    
    draw_text("Press ENTER to continue...", 50, HEIGHT - 60, font, GREEN)

    line_index = 0
    draw_text(text_lines[line_index], 50, start_y + line_index * line_spacing, font, color)
    line_index += 1
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if line_index < len(text_lines):
                    draw_text(text_lines[line_index], 50, start_y + line_index * line_spacing, font, color)
                    line_index += 1
                    pygame.display.flip()
                else:
                    waiting = False


# 世界观介绍界面
def Intro():
    screen.fill(BLACK)
    intro_text = [
    "Welcome to the glorious world of S.T.U.P.I.D.",
    "The less you know, the safer you are.",
    "Ignorance gives you power,",
    "while high IQ leads to death.",
    "Stay Simple. Stay Foolish!",
    "Remember: Simplicity is All You Need™.",
    ]
    draw_multiline_dialog(intro_text)
#人物背景
backgrounds = [
    {
        "name": "Mortgage Hero",
        "description": "Spent lifetime savings on a 120-year mortgage for a 70-year-old building.",
        "modifiers": {"D": 2,"I": -2}
    },
    {
        "name": "Galgame addict",
        "description": "Have tons of galgame.",
        "modifiers": {"I": -8, "P": -2}
    },
    {
        "name": "Nerd",
        "description": "Knows 7 languages. Poor sight and social ability.",
        "modifiers": {"I": 5, "P": -5, "S": -5}
    },
    {
        "name": "Programmer",
        "description": "Automated breakfast, forgot how to boil water manually.",
        "modifiers": {"I": 1, "S": -2, "D": 1,"P": -2},
        "reward_item":"C++ Primer"
    },
    {
        "name": "Debug",
        "description": "For Grace.",
        "modifiers": {"I": - 20,"P":-20},
        "reward_item":"Cheat Engine"
    }
]

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        test_line = current_line + word + ' '
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + ' '
    lines.append(current_line)
    return lines
#背景选择
def choose_background(screen, font):
    selected = None
    running = True
    while running:
        screen.fill(BLACK)
        Header(player)
        mouse_pos = pygame.mouse.get_pos()
        
        for i, bg in enumerate(backgrounds):
            rect = pygame.Rect(100, 100 + i * 60, 400, 50)
            color = (100, 100, 255) if rect.collidepoint(mouse_pos) else (50, 50, 100)# 高亮
            pygame.draw.rect(screen, color, rect)
            
            name_surf = font.render(bg["name"], True, WHITE)
            screen.blit(name_surf, (110, 110 + i * 60))

            # 显示详情和modifiers
            if rect.collidepoint(mouse_pos):
                desc_lines = wrap_text(bg["description"], font, 580)
                for j, line in enumerate(desc_lines):
                    line_surf = font.render(line, True, (200, 200, 200))
                    screen.blit(line_surf, (600, 250 + j * 25))
                
                # 显示属性加成
                mod_text = "Effects: " + ", ".join([f"{k} {'+' if v >= 0 else ''}{v}" for k, v in bg.get("modifiers", {}).items()])
                mod_surf = font.render(mod_text, True, (255, 180, 180))
                screen.blit(mod_surf, (600, 250 + len(desc_lines) * 25 + 10))



        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, bg in enumerate(backgrounds):
                    rect = pygame.Rect(100, 100 + i * 60, 400, 50)
                    if rect.collidepoint(mouse_pos):
                        selected = bg
                        player.apply_background(bg)
                        running = False

        if selected and"reward_item" in selected:
            reward_item_name = selected["reward_item"]
            item_data_found = Item.get_item_data_by_name(reward_item_name)
            if item_data_found:
                player.inventory.add_item(Item(**item_data_found))
                print(f"[DEBUG] 你获得了新物品：{reward_item_name}")

        pygame.display.flip()
    return selected

def format_stats_short(stats):
    return ", ".join(f"{k}:{stats[k]}" for k in ['S', 'T', 'U', 'P', 'I', 'D'] if k in stats)

def Header(player):
    stats = player.current_stats()
    draw_text(format_stats_short(stats), 10, 10, FONT, GREEN)
    draw_text(f"Hp: {stats['hp']}   Simplicity: {stats['sp']}", WIDTH - 400, 10, FONT, GREEN)

# 事件定义
    # {
    #     "text": "Genie! You can get a computer game for free!",
    #     "options": [
    #         {"text": "PC-98 game!","condition": lambda p: p.current_stats()['I'] >20,"effect": lambda p: ({}, "In search of classic")},
    #         {"text": "H-game!","condition": lambda p: True,"effect": lambda p: ({}, "A nice eroge,isnt it?")},
    #         {"text": "Steam game!","condition": lambda p: True,"effect": lambda p: ({}, "Steam is what you need!")},
    #         {"text": "Sorry!I only play open-source games.","condition": lambda p: p.current_stats()['I'] > 25,"effect": lambda p: ({}, "Dwarf Rortress is a masterpiece")},
    #         {"text": "Mobile games!", "condition": lambda p: True, "effect": lambda p: ({"sp": p.base_stats["sp"] + 10}, "portable")},
    #         {"text": "CRPG!", "condition": lambda p: p.base_stats['I'] >= 10, "effect": lambda p: ({}, "Pure D&D rules")},
    #         {"text": "RPG!", "condition": lambda p: True, "effect": lambda p: ({}, "")},
    #         {"text": "Give me a Guidebook!", "condition": lambda p: p.base_stats['S'] >= 15, "effect": lambda p: ({}, "Manual top the list")},
    #         {"text": "VScode is game,literaly.", "condition": lambda p: p.base_stats['I'] >= 25, "effect": lambda p: ({}, "Coding is fun"),"reward_item":"Cheat Engine"},
    #     ],
    #     "image": "assets/magic.png",
    # },


def handle_effect(effect, player):
    action = effect.get("action")

    if action == "heal":
        amount = effect.get("amount", 0)
        player.heal(amount)
        logger.debug(f"[EFFECT] Healed for {amount}")

    elif action == "damage":
        amount = effect.get("amount", 0)
        player.take_damage(amount)
        logger.debug(f"[EFFECT] Took {amount} damage")

    elif action == "update_stats":
        stats = effect.get("stats", {})
        mode = effect.get("mode", "set")
        player.base_stats.update(stats, mode=mode)

    elif action == "add_item":
        item_name = effect.get("item")
        data = Item.get_item_data_by_name(item_name)
        if data:
            player.inventory.add_item(Item(**data))
            logger.debug(f"[EFFECT] Item gained: {item_name}")
        else:
            logger.warning(f"[EFFECT] Item '{item_name}' not found in item_data.")

    elif action == "message":
        message_text = effect.get("text", "")
        draw_multiline_dialog([message_text], start_y=500, font=CN_FONT, color=WHITE)

    elif action == "trigger_event":
        event_id = effect.get("id")
        next_event = next((e for e in events if e.get("id") == event_id), None)
        if next_event:
            show_event(next_event)
        else:
            logger.warning(f"[EFFECT] No event found with id: {event_id}")



def show_event(event):
    screen.fill(BLACK)
    Header(player)
    desc_lines = wrap_text(event["text"], BIGFONT, 1100)
    for j, line in enumerate(desc_lines):
        draw_text(line, 50, 50 + 40 * j, BIGFONT)

    # 显示图片
    image_path = event.get("image", 'assets/Default.png')
    image = load_image(image_path)
    screen.blit(image, (WIDTH - image.get_width() - 100, 200))
    render_ascii_art(screen, label="girl", font_size=18, x=WIDTH - 600, y=200, color=WHITE)

    option_y = 150
    valid_options = [opt for opt in event["options"] if opt["condition"](player)]

    # rude_response buff 特别选项
    if "rude_response" in player.buffs:
        valid_options.append({
            "text": "F**k you",
            "condition": lambda p: True,
            "effect": [
                {"action": "update_stats", "stats": {"sp": 5},"mode":"add"},
                {"action": "message", "text": "你的粗鲁回应惹恼了对方！"}
            ]
        })

    # 显示所有选项
    for i, option in enumerate(valid_options):
        draw_text(f"{i + 1}. {option['text']}", 100, option_y + i * 40, FONT, GREEN)
    pygame.display.flip()

    # 等待用户输入选择
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_9:
                index = e.key - pygame.K_1
                if index < len(valid_options):
                    for effect in valid_options[index]["effect"]:
                        handle_effect(effect, player)
                    waiting = False


    
    
#结局
def determine_ending(p):
    # 检查作弊结局
    if p.inventory.has_item("Cheat Engine"):
        return [
            "You have used the Cheat Engine.",
            "Reality collapses under your manipulation.",
            "You are now the master of bugs."
        ]
    if p.base_stats['sp'] <= 10:
        return [
            "You are too smart.",
            "You are exiled."
        ]
    if p.base_stats['sp'] <= 30:
        return [
            "You are smart.",
            "Please embrace your stupidity.",
        ]
    if p.base_stats['sp'] <= 50:
        return [
            "You are far from stupid.",
            "Work harder."
        ]
    else:
        return [
            "You have become the ultimate fool.",
            "You can now see the world in its purest form.",
        ]

def draw_inventory_slots():
    screen.fill(BLACK)
    draw_text("Select Slot:", 10, 10)
    y = 50
    slots = list(player.equipment.slots.keys())
    for idx, slot in enumerate(slots):
        draw_text(f"{idx+1}. {slot}", 30, y)
        y += 30
    draw_text("Press number to choose slot.", 10, HEIGHT-40)
    pygame.display.flip()

def draw_inventory_items_for_slot(slot):
    screen.fill(BLACK)
    draw_text(f"Available Items for {slot}:", 10, 10)
    y = 50
    available_items = [item for item in player.inventory.items if item.slot == slot]
    
    # 显示已装备物品
    equipped_item = player.equipment.slots[slot]
    if equipped_item:
        curse_text = " (cursed)" if equipped_item.curse else ""  # 如果是诅咒物品，则加上 "(cursed)"
        if "no_item_info" in player.debuffs:
            draw_text(f"Currently Equipped: {equipped_item.name}{curse_text}       [Unknown due to Poor P]", 30, y)
        else:
            draw_text(f"Currently Equipped: {equipped_item.name}{curse_text}       {equipped_item.modifiers}", 30, y)
        y += 30
    else:
        draw_text(f"Currently Equipped: Empty", 30, y)
        y += 30
    
    # 显示可用物品
    for idx, item in enumerate(available_items):
        if "no_item_info" in player.debuffs:
            draw_text(f"{idx+1}. {item.name}  [Unknown due to Poor P]", 30, y)
        else:
            draw_text(f"{idx+1}. {item.name}  {item.modifiers}  {item.description}", 30, y)
        y += 30

    if not available_items:
        draw_text("No items available.", 30, y)
    draw_text("Press number to equip item. [ESC] to go back.", 10, HEIGHT-40)
    pygame.display.flip()
    return available_items

class Dungeon:
    def __init__(self, width=10, height=10, level=1, monster_templates=None):
        self.width = width
        self.height = height
        self.level = level  # 地牢层数
        self.map = [['#' for _ in range(width)] for _ in range(height)]
        self.player_pos = [1, 1]
        global monster_template1
        self.monster_templates = monster_templates or monster_template1
        self.monsters = []
        self.event_triggers = {}
        self.generate_dungeon()

    def generate_dungeon(self):
        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                self.map[y][x] = '.' if random.random() < 0.9 else '#'

        self.map[self.player_pos[0]][self.player_pos[1]] = '@'

        # 放一个向下楼梯
        self.place_stairs('>')
        
        if self.level > 1:
            # 如果不是第一层，放一个向上楼梯
            self.place_stairs('<')

        self.place_events(3)  # 放3个事件
        self.place_special_rewards()
        self.place_monsters(3)  # 放3个怪物

    def place_stairs(self, symbol):
        while True:
            x = random.randint(1, self.width-2)
            y = random.randint(1, self.height-2)
            if self.map[y][x] == '.':
                self.map[y][x] = symbol
                break

    def place_special_rewards(self):
        if self.level == 2:
            # 第三层生成智力药水
            while True:
                x = random.randint(1, self.width-2)
                y = random.randint(1, self.height-2)
                if self.map[y][x] == '.':
                    self.map[y][x] = '✦'  # 特别用药水图标
                    self.event_triggers[(y, x)] = "int_potion"
                    break


    def place_events(self, count):
        placed = 0
        while placed < count:
            x = random.randint(1, self.width-2)
            y = random.randint(1, self.height-2)
            if self.map[y][x] == '.':
                self.map[y][x] = '⚠'
                self.event_triggers[(y, x)] = random.randint(0, len(events)-1)
                placed += 1

    def place_monsters(self, count):
        placed = 0
        while placed < count:
            x = random.randint(1, self.width-2)
            y = random.randint(1, self.height-2)
            if self.map[y][x] == '.' and (y, x) != tuple(self.player_pos):
                template = random.choice(self.monster_templates)
                self.monsters.append({'x': x, 'y': y, 'monster': template.clone(x, y)})
                self.map[y][x] = 'M'
                placed += 1

    def is_passable(self, x, y):
        return self.map[y][x] not in ['#', '~']
            
    def move_player(self, dx, dy):
        new_x = self.player_pos[1] + dx
        new_y = self.player_pos[0] + dy
        if self.is_passable(new_x, new_y):
            self.map[self.player_pos[0]][self.player_pos[1]] = '.'
            self.map[new_y][new_x] = '@'
            self.player_pos = [new_y, new_x]
            return True
        return False

    def get_tile(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.map[y][x]
        return '#'

    def draw_main(self):
        Header(player)
        screen.blit(Player.sp_image, (WIDTH-200, 80))
        bp_image = load_image('assets/backpack.jpg')
        screen.blit(bp_image, (WIDTH-300, 50))

    def draw_dungeon(self, dungeon):
        screen.fill(BLACK)
        tile_size = 40
        for y in range(dungeon.height):
            for x in range(dungeon.width):
                tile = dungeon.get_tile(x, y)
                draw_text(tile, x * tile_size + 100, y * tile_size + 50, CN_FONT, WHITE if tile != '@' else GREEN)
        for m in self.monsters:
            x = m['monster'].x
            y = m['monster'].y
            draw_text('M', x * tile_size + 100, y * tile_size + 50, CN_FONT, WHITE)

        draw_text("Arrow key to move,Press I to open backpack", 50, HEIGHT-50, CN_FONT, WHITE)
        target_image = load_image('assets/target.png',(80,60))
        screen.blit(target_image,(WIDTH-100,HEIGHT-80) )
        dungeon.draw_main()
        pygame.display.flip()

class Monster:
    def __init__(self, x , y , name, attack_type, difficulty):
        self.x = x
        self.y = y
        self.name = name
        self.attack_type = attack_type  # 例如 "calculus", "social"
        self.difficulty = difficulty  # 1-10，影响基础伤害

    def clone(self, x, y):
        return Monster(x, y, self.name, self.attack_type, self.difficulty)
    
    def attack(self, player):
        intelligence = player.current_stats()['I']
        base_damage = self.difficulty * random.uniform(0.8, 1.2)
        
        # 高智力增加伤害
        if intelligence > 15:
            multiplier = (intelligence - 15) * 0.5
            base_damage += multiplier
            logger.debug("High intelligence (%d) increased damage by %.2f", intelligence, multiplier)
        
        # 低智力减免伤害
        if intelligence < 10:
            reduction = (10 - intelligence) * 0.5
            base_damage = max(0, base_damage - reduction)
            logger.debug("Low intelligence (%d) reduced damage by %.2f", intelligence, reduction)

        final_damage = round(base_damage)
        player.take_damage(final_damage)
        
        # 攻击描述
        if self.attack_type == "calculus":
            message = f"{self.name} 抛出一道微积分题！你失去 {final_damage} 单纯度！"
        elif self.attack_type == "social":
            message = f"{self.name} 要求你完成社交考核！你失去 {final_damage} 单纯度！"
        else:
            message = f"{self.name} 发动精神攻击！你失去 {final_damage} 单纯度！"
        
        logger.info("Monster %s attacked, dealt %d damage", self.name, final_damage)
        return message
    
    def move_randomly(self, game_map):
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        new_x = self.x + dx
        new_y = self.y + dy

        if game_map.is_passable(new_x, new_y):
            self.x = new_x
            self.y = new_y

# 示例怪物数据
monster_template1 = [
    Monster(0, 0, "数学幽灵", "calculus", 5),
    Monster(0, 0, "社交审查者", "social", 3),
    Monster(0, 0, "绩效评估者", "performance", 7)
]



from enum import Enum, auto

class GameState(Enum):
    DUNGEON = auto()
    INVENTORY = auto()
    EVENT = auto()
    END = auto()

class GameStateManager:
    def __init__(self, player):
        self.state = GameState.DUNGEON
        self.dungeon = Dungeon()
        self.player = player
        self.selected_slot = None
        self.move_count = 0
        self.current_event = None

    def handle_event(self, event):
        if self.state == GameState.DUNGEON:
            self.handle_dungeon_event(event)
        elif self.state == GameState.INVENTORY:
            self.handle_inventory_event(event)

    def handle_dungeon_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.state = GameState.INVENTORY
                self.selected_slot = None
            else:
                dx, dy = 0, 0
                if event.key == pygame.K_UP: dy = -1
                elif event.key == pygame.K_DOWN: dy = 1
                elif event.key == pygame.K_LEFT: dx = -1
                elif event.key == pygame.K_RIGHT: dx = 1

                tile = self.dungeon.get_tile(
                    self.dungeon.player_pos[1] + dx,
                    self.dungeon.player_pos[0] + dy
                )

                if self.dungeon.move_player(dx, dy):
                    self.move_count += 1
                    self.handle_tile_effect(tile)
    def combat(self, monster_obj):
        print(f"你遭遇了怪物：{monster_obj.name}！")
        message = monster_obj.attack(self.player)

        # 显示攻击消息
        screen.fill(BLACK)
        draw_multiline_dialog([message], start_y=300, font=CN_FONT, color=WHITE)

    def handle_tile_effect(self, tile):
        pos = tuple(self.dungeon.player_pos)
        if tile == '>':
            self.dungeon = Dungeon(level=self.dungeon.level + 1, monster_templates=monster_template1)
        elif tile == '<' and self.dungeon.level > 1:
            self.dungeon = Dungeon(level=self.dungeon.level - 1, monster_templates=monster_template1)
        elif tile == '⚠':
            event_index = self.dungeon.event_triggers.get(pos)
            if event_index is not None:
                show_event(events[event_index])
        elif tile == '✦':
            trigger_ending_event(self.player)
            self.state = GameState.END
        elif tile == 'M':
            for m in self.dungeon.monsters:
                if (m['x'], m['y']) == (pos[1], pos[0]):
                    self.combat(m['monster'])
                    self.dungeon.monsters.remove(m)
                    break
        elif self.move_count % 20 == 0:
            show_event(random.choice(events))
            if "auto_heal" in player.buffs:
                player.heal(2)

        self.move_monsters()  # 怪物在玩家行动后移动

    def move_monsters(self):
        for m in self.dungeon.monsters:
            monster = m['monster']

            # 清除旧位置
            if self.dungeon.map[monster.y][monster.x] == 'M':
                self.dungeon.map[monster.y][monster.x] = '.'

            # 原位置记录
            old_x, old_y = monster.x, monster.y

            # 尝试移动
            monster.move_randomly(self.dungeon)

            # 若怪物踩到玩家，触发战斗
            if self.dungeon.map[monster.y][monster.x] == '@':
                self.combat(monster)
                self.dungeon.monsters.remove(m)
            else:
                self.dungeon.map[monster.y][monster.x] = 'M'

            

    def handle_inventory_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.selected_slot is None:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    slots = list(self.player.equipment.slots.keys())
                    if index < len(slots):
                        self.selected_slot = slots[index]
                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.DUNGEON
            else:
                if event.key == pygame.K_ESCAPE:
                    self.selected_slot = None
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    available_items = [
                        item for item in self.player.inventory.items
                        if item.slot == self.selected_slot
                    ]
                    if index < len(available_items):
                        self.player.equipment.equip(available_items[index], self.player.inventory)
                        self.selected_slot = None
                        self.state = GameState.DUNGEON

    def update(self):
        if self.state == GameState.DUNGEON:
            self.dungeon.draw_dungeon(self.dungeon)
        elif self.state == GameState.INVENTORY:
            if self.selected_slot is None:
                draw_inventory_slots()
            else:
                draw_inventory_items_for_slot(self.selected_slot)

def main_game():
    global player
    # 初始化角色与道具
    for data in item_data:
        player.inventory.add_item(Item(**data))
    player.inventory.remove_item_by_name("Cheat Engine")

    manager = GameStateManager(player)

    while manager.state != GameState.END:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                manager.state = GameState.END
            else:
                manager.handle_event(event)
        manager.update()
        pygame.display.flip()


            
def trigger_ending_event(player):
    line1 = ["你抵达了终点——","但你已经不会拧开瓶盖了。","不过，你还是幸运的——","那其实是一瓶毒药。","你平安地继续活下去了……",]
    line2 = ["你抵达了终点——","那是一瓶智力药剂","当你饮下的那一瞬","你意识到那其实是一瓶毒药。","你倒在地牢里……",]
    line3 = ["你抵达了终点——","那是一瓶智力药剂","你发现了那张新贴的标签之下","其实是一瓶毒药。",]
    line4 = ["你抵达了终点——","那是一瓶智力药剂","你用你的聪明才智测试了药剂的化学属性","它是一瓶毒药。",]
    screen.fill(BLACK)
    stats=player.current_stats()
    if(stats["I"] <= 5):
        draw_multiline_dialog(line1, start_y=200, font=CN_FONT, color=WHITE)
    elif (stats["I"] <= 15):
        draw_multiline_dialog(line2, start_y=200, font=CN_FONT, color=WHITE)
    elif (stats["I"] > 15 and stats["P"] > 15):
        draw_multiline_dialog(line3, start_y=200, font=CN_FONT, color=WHITE)
    elif (stats["I"] > 25):
        draw_multiline_dialog(line4, start_y=200, font=CN_FONT, color=WHITE)
    pygame.display.flip()
    pygame.time.wait(1000)
    Outro() 
            
def Outro():
    screen.fill(BLACK)
    draw_multiline_dialog(determine_ending(player))
    pygame.time.wait(1000)
    draw_text("Congratulations!", 200, 300, BIGFONT, GREEN)
    pygame.display.flip()
    pygame.time.wait(1000)
    pygame.quit()


# 执行
player = Player()
Intro()
attribute_allocation(player)
choose_background(screen, FONT)

main_game()
pygame.quit()



# "Welcome to the glorious world of S.T.U.P.I.D.",
# "The less you know, the safer you are.",
# "Ignorance gives you power,",
# "while high IQ leads to death.",
# "Stay Simple. Stay Foolish!",
# "Remember: Simplicity is All You Need™.",
# 我希望加入一个地牢系统
# 比如可能无法查看武器属性，对话只能说“是”或“否”，喝错药水（毒药伤药搞混）（灵感来自rogue系游戏）。
# 但傻也有好处：simplicity就是你的血量，所以太聪明是过不了的
# 地牢的怪物是都是精神攻击，属性低有伤害减免
# 只有傻子能免疫boss的嘴炮
# 攻击方式是计算你的考试、简历、薪资、绩效考核、社交 
# 你智力越高，怪物直接出微积分题给你
# 有的道具一旦带上就摘不下来（类似诅咒），有的可以取下来，代表这只是伪装
# “你选择了‘情绪稳定药物’，获得情绪防御+10，但思维速度-2。你的行动选项减少了三个，只剩下默认回复。”
# 地牢的目标是找到智力药剂如何。最后发现这个目标根本不存在。你抵达了终点——但你已经不会拧开瓶盖
# 不过，你还是幸运的——那是一瓶毒药

#Neko Project:政府的降智工程的一环 诱导女性长出可爱的猫耳，但会导致脑容量的下降
#Dungeon Project:政府的模拟地牢游戏，地牢内部构造是政府依照我们自己记忆建的，地牢是人生的逆序，从老年一直通往婴儿。
#这个游戏诱导人们降智来通关。地牢让人罹患"阿尔茨海默症"
#游玩玩这个游戏意味着你被降智了（你的选择都是真实的，像安德的游戏），除非你无伤通关
#neko和dungeon分别通过文化和暴力手段实现