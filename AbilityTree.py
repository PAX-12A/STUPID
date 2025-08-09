import pygame
from font_manager import get_font
from colors import *
from Stupid import Toolbar,Tab
import time


# 科技节点类
class BaseNode:
    def __init__(self, name, x, y, description="", prerequisites=None, width=105, height=30):
        self.name = name
        self.description = description
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)

        self.prerequisites = prerequisites or []
        self.is_unlocked = False
        self.is_hovered = False

        self.press_start_time = 0
        self.is_pressing = False
        self.research_time = 1.0  # 默认研究时间（秒）
        self.is_researched = False
        self.is_researching = False
        self.research_progress = 0.0

    def is_mouse_over(self, pos):
        return self.rect.collidepoint(pos)

    def start_press(self):
        self.press_start_time = time.time()
        self.is_pressing = True

    def update_press(self):
        if self.is_pressing:
            duration = time.time() - self.press_start_time
            return duration
        return 0

    def release_press(self):
        self.is_pressing = False
        
    def draw(self, screen , font):
        bg_color = BLACK
        # 根据状态选择颜色
        if self.is_researched:
            text_color = BLACK
            bg_color = WHITE
        elif self.is_unlocked:
            text_color = WHITE
        else:
            text_color = GRAY
            
        # 悬停效果
        if self.is_hovered and self.is_unlocked and not self.is_researched:
            bg_color = (50,50,50)
            
            
        # 绘制节点背景
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, text_color, self.rect, 2)# 边框
        
        # 绘制研究进度条（如果正在研究）
        if self.is_researching and self.research_progress > 0.05:
            progress_rect = pygame.Rect(self.rect.x, self.rect.bottom, 
                                      int(self.rect.width* self.research_progress), 5)
            pygame.draw.rect(screen, GRAY, progress_rect)

        label = font.render(self.name, True, text_color)
        screen.blit(label, (self.rect.centerx - label.get_width()//2,
                            self.rect.centery - label.get_height()//2))
            
        
    def contains_point(self, pos):
        return self.rect.collidepoint(pos)
        
    def can_unlock(self, researched_nodes):
        if self.is_researched:
            return False
        for prereq in self.prerequisites:
            if prereq not in researched_nodes:
                return False
        return True
        
    def start_research(self):
        if self.is_unlocked and not self.is_researched:
            self.is_researching = True
            self.press_start_time = pygame.time.get_ticks()

    def finish_research(self, player):
        self.is_researched = True
        self.is_researching = False
        if hasattr(self, "weapon") and self.weapon:
            player.unlock_weapon(self.weapon)
            
    def update_research(self, current_time, player):
        if self.is_researching:
            elapsed = (current_time - self.press_start_time) / 1000.0
            self.research_progress = min(1.0, elapsed / self.research_time)
            
            if self.research_progress >= 1.0:
                self.finish_research(player)
                return True
        return False
        
    def cancel_research(self):
        self.is_researching = False
        self.research_progress = 0.0


class TechNode(BaseNode):
    def __init__(self, name, x, y, description="", prerequisites=None, level=1, skills=None):
        super().__init__(name, x, y, description, prerequisites)
        self.level = level
        self.skills = skills or []
        self.learned_skills = set()

class LanguageNode(BaseNode):
    def __init__(self, name, x, y, description="", prerequisites=None, skills=None,weapon=None):
        super().__init__(name, x, y, description, prerequisites)
        self.skills = skills or []
        self.weapon = weapon  # 新增：研究完成后解锁的武器



# 科技树类
class TechTree:
    def __init__(self):
        self.nodes = {
            "tech": {},   # 科技树节点
            "lang": {},   # 语言树节点
            "algo": {}    # 算法树节点
        }
        self.connections = {
            "tech": [],
            "lang": [],
            "algo": []
        }
        self.researched = set()
        self.selected_node = None
        self.mouse_pressed = False
        self.pressed_node = None
        self.learned_skills = set()
        self.skill_points = 0  # 可手动设置初始点数
        self.setup_Ability_tree("tech", tech_levels)
        self.setup_Ability_tree("lang", lang_levels,["C","Utility"])

        self.tabs = Toolbar.create_tabs(self,
            names=[ "Tech","Lang","Algo","Skill"],
            start_pos=(SCREEN_WIDTH -250 , 50),
            direction="col"
        )

    def get_active_tab_name(self):
        for tab in self.tabs:
            if tab.is_active:
                return tab.name.lower()  # tech / skill / lang / ml
        return "tech"
        
    def setup_Ability_tree(self, tree_type, ability_levels,initial_unlock=None):
        # 确保容器存在
        if tree_type not in self.nodes:
            self.nodes[tree_type] = {}
            self.connections[tree_type] = []

        # 创建节点
        for level, abilities in ability_levels.items():
            for ability in abilities:
                if tree_type == "tech":
                    name, row_pos, desc, prereqs, skills = ability
                    x = 80 + (level - 1) * 130
                    y = 80 + int(row_pos * 80)
                    node = TechNode(name, x, y, desc, prereqs, level, skills)
                elif tree_type == "lang":
                    name, x, y, desc, prereqs, skills,weapon = ability
                    node = LanguageNode(name, x, y, desc, prereqs, skills,weapon)
                # elif tree_type == "algo":
                #     name, x, y, desc, prereqs, skills = ability
                #     node = AlgorithmNode(name, x, y, desc, prereqs, skills)
                else:
                    raise ValueError(f"未知的树类型: {tree_type}")

                self.nodes[tree_type][name] = node

        # 设置连接关系
        for node_name, node in self.nodes[tree_type].items():
            for prereq in node.prerequisites:
                if prereq in self.nodes[tree_type]:
                    self.connections[tree_type].append((prereq, node_name))

        # 初始解锁第一级（只对有 level 属性的节点有效）
        for node in self.nodes[tree_type].values():
            if hasattr(node, "level") and node.level == 1:
                node.is_unlocked = True

            # 初始解锁
        if initial_unlock:
            for name in initial_unlock:
                if name in self.nodes[tree_type]:
                    self.nodes[tree_type][name].is_unlocked = True

                
    def draw_tech_tree(self, screen, font, small_font):
        level_font = get_font("en", "Time", 20)
        # 绘制等级分隔线和标题
        for level in range(1, 7):
            x = 80 + (level - 1) * 130
            # 绘制等级标题
            level_title = f"Lv {level}"
            title_surface = level_font.render(level_title, True, WHITE)
            title_rect = title_surface.get_rect(center=(x, 40))
            screen.blit(title_surface, title_rect)
        
        # 绘制连接线
        for start_name, end_name in self.connections["tech"]:
            start_node = self.nodes["tech"][start_name]
            end_node = self.nodes["tech"][end_name]
            
            # 选择线条颜色和样式
            if start_node.is_researched and end_node.is_unlocked:
                line_color = WHITE
                line_width = 3
            elif start_node.is_researched:
                line_color = GRAY  
                line_width = 2
            else:
                line_color = SHADOW
                line_width = 1
                
            # 从节点边缘到边缘的连接线
            start_x = start_node.rect.right
            start_y = start_node.y
            end_x = end_node.rect.left
            end_y = end_node.y
            
            pygame.draw.line(screen, line_color, (start_x, start_y), (end_x, end_y), line_width)
            
            # 在连接线末端绘制小箭头
            if line_width > 1:
                arrow_size = 8
                # 计算箭头方向
                dx = end_x - start_x
                dy = end_y - start_y
                length = (dx*dx + dy*dy)**0.5
                if length > 0:
                    dx /= length
                    dy /= length
                    # 箭头点
                    arrow_x = end_x - dx * arrow_size
                    arrow_y = end_y - dy * arrow_size
                    # 箭头两翼
                    wing1_x = arrow_x - dy * arrow_size/2
                    wing1_y = arrow_y + dx * arrow_size/2
                    wing2_x = arrow_x + dy * arrow_size/2  
                    wing2_y = arrow_y - dx * arrow_size/2
                    pygame.draw.polygon(screen, line_color, 
                                      [(end_x, end_y), (wing1_x, wing1_y), (wing2_x, wing2_y)])
                                     
        # 绘制所有节点
        for node in self.nodes["tech"].values():
            node.draw(screen, small_font)
            
        # 绘制选中节点的详细信息
        if self.selected_node:
            self.draw_node_info(screen ,font, small_font)

    def draw_language_tree(self,screen, font, small_font):
        # image = load_image('assets/sp.png', (170,170))
        # screen.blit(image, (800,400))

        # 绘制连接线
        for start_name, end_name in self.connections["lang"]:
            start_node = self.nodes["lang"][start_name]
            end_node = self.nodes["lang"][end_name]
            
            # 选择线条颜色和样式
            if start_node.is_researched and end_node.is_unlocked:
                line_color = WHITE
                line_width = 3
            elif start_node.is_researched:
                line_color = GRAY  
                line_width = 2
            else:
                line_color = SHADOW
                line_width = 1
            
            pygame.draw.line(screen, line_color, start_node.rect.center, end_node.rect.center, line_width)

        # 再绘制节点
        for node in self.nodes["lang"].values():
            node.draw(screen, small_font)

                # 绘制选中节点的详细信息
        if self.selected_node:
            self.draw_node_info(screen ,font, small_font)
            
        
    def draw(self, screen, font, small_font):
        icon_font = get_font("en", "Cogmind", 20)
        Toolbar.draw_tab_border(self, screen, icon_font, self.tabs)
        DOS_20= get_font("en", "DOS", 16)

        subview = self.get_active_tab_name()

        if subview == "skill":
            self.draw_skill_view(screen, font, small_font)
        elif subview == "lang":
            self.draw_language_tree(screen, font, small_font)
        elif subview == "ml":
            self.draw_tech_tree(screen, font, small_font)
        else:
            self.draw_tech_tree(screen, font, small_font)

        
       
    def draw_node_info(self, screen, font , small_font):
        node = self.selected_node
        info_x = 50
        info_y = 400
        info_width = SCREEN_WIDTH-100
        info_height = 200
        
        # 信息面板背景
        info_rect = pygame.Rect(info_x, info_y, info_width, info_height)
        pygame.draw.rect(screen, BLACK, info_rect)
        pygame.draw.rect(screen, WHITE, info_rect, 2)
        
        y_offset = info_y + 15
        
        # 状态信息
        if node.is_researched:
            status = "- finished"
        elif node.is_researching:
            status = f"- researching..{int(node.research_progress * 100)}%"
        elif node.is_unlocked:
            status = "- available"
        else:
            status = "- locked"

        
        # 节点名称
        f1=get_font("ch", "Pixel", 20)
        name_surface = f1.render(node.name, True, WHITE)#要用中文字体
        status_surface = font.render(status, True, WHITE)#用英文字体，紧跟在name后面
        name_width = name_surface.get_width()
        screen.blit(name_surface, (info_x + 10, y_offset))
        screen.blit(status_surface, (info_x + 10 + name_width + 10, y_offset))
        y_offset += 30
        
        # 描述信息
        desc_line_surface = small_font.render(node.description, True, WHITE)
        screen.blit(desc_line_surface, (info_x + 10, y_offset))
        y_offset += 18
            
        # 前置需求
        if node.prerequisites:
            y_offset += 10
            prereq_surface = small_font.render("前置需求:", True, WHITE)
            screen.blit(prereq_surface, (info_x + 10, y_offset))
            y_offset += 18
            
            for prereq in node.prerequisites:
                color = WHITE if prereq in self.researched else (200, 150, 150)
                prereq_surface = small_font.render(f"*{prereq}", True, color)
                screen.blit(prereq_surface, (info_x + 15, y_offset))
                y_offset += 16

        # 技能
        if node.skills:
            y_offset += 10
            skills_surface = small_font.render("解锁技能:", True, WHITE)
            screen.blit(skills_surface, (info_x + 10, y_offset))
            y_offset += 18

            # 拼接技能名
            skill_text = ", ".join(node.skills)
            skills_surface = small_font.render(skill_text, True, WHITE)
            screen.blit(skills_surface, (info_x + 15, y_offset))
            y_offset += 18

    def draw_skill_view(self, screen, font, small_font):
        
        title = small_font.render("技能树：消耗技能点学习技能", True, WHITE)
        screen.blit(title, (50, 40))

        y = 80
        x = 50

        # 技能点显示
        point_text = small_font.render(f"可用技能点: {self.skill_points}", True, GREEN)
        screen.blit(point_text, (SCREEN_WIDTH - 400, 40))

        # 所有已解锁技能
        available_skills = []
        for node in self.nodes.values():
            if node.is_researched and node.skills:
                for skill in node.skills:
                    available_skills.append(skill)

        for skill in available_skills:
            is_learned = skill in self.learned_skills
            color = GREEN if is_learned else WHITE
            status = "(已学习)" if is_learned else "(点击学习)"
            skill_text = f"{skill} {status}"

            text_surface = small_font.render(skill_text, True, color)
            text_rect = text_surface.get_rect(topleft=(x, y))
            screen.blit(text_surface, text_rect)

            # 存按钮区域
            setattr(self, f"skill_rect_{skill}", text_rect)

            y += 30
                
    def handle_event(self, player, event):

        tree_type = self.get_active_tab_name()

        # 1. ESC 返回上一级或关闭标签
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # 如果当前不是 Tech，切回 Tech
            active = self.get_active_tab_name()
            if active and active != "tech":
                for tab in self.tabs:
                    tab.is_active = (tab.name.lower() == "tech")
            else:
                # 否则关闭所有
                for tab in self.tabs:
                    tab.is_active = False
            return True

        # 2. 鼠标移动：更新悬停状态
        elif event.type == pygame.MOUSEMOTION:
            for node in self.nodes[tree_type].values():
                node.is_hovered = node.contains_point(event.pos)

        # 3. 鼠标点击：切换 tab
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tab in self.tabs:
                if tab.rect and tab.rect.collidepoint(event.pos):
                    for other_tab in self.tabs:
                        other_tab.is_active = (other_tab == tab)
                    return True
                
            # tech / lang / ml 模式通用
            for node in self.nodes[tree_type].values():
                if node.contains_point(event.pos):
                    self.selected_node = node
                    if node.can_unlock(self.researched) and node.is_unlocked:
                        self.pressed_node = node
                        node.start_research()
                    break
            self.mouse_pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_pressed = False
            if self.pressed_node:
                self.pressed_node.cancel_research()
                self.pressed_node = None

        Toolbar.handle_hover_event(self,event)
                    
        return False
        
    def update(self ,player):
        """更新研究进度"""
        current_time = pygame.time.get_ticks()
        
        # 更新正在研究的节点
        if self.pressed_node and self.pressed_node.is_researching:
            if self.pressed_node.update_research(current_time,player):
                # 研究完成
                self.researched.add(self.pressed_node.name)
                self.update_unlocked_nodes()
                self.pressed_node = None
                self.skill_points+=1  # 每完成一个科技，获得1点技能点
                
    def update_unlocked_nodes(self):
        tree_type = self.get_active_tab_name()
        """更新可解锁的节点状态"""
        for node in self.nodes[tree_type].values():
            if not node.is_unlocked and node.can_unlock(self.researched):
                node.is_unlocked = True


# 定义每级科技 (名称, 行位置, 描述, 前置需求 , 技能)
tech_levels = {
    1: [  # 第一列 - 基础课程
        ("高级语言程设", 0, "你终于学会了如何向世界说出 Hello, world！（解锁编程交互）副作用：开始把生活当成命令行。", [],["Hello world","C++"]),
        ("计算机导论", 1, "你大致了解计算机的组成与职业前景。副作用：成为'天选打螺丝的人'。", [], []),
        ("线性代数", 2, "逻辑能力+1，但你开始用真值表分析社交。", [], ["Matrix"]),
        ("高等数学", 2.5, "你能处理复杂计算，但开始怀疑微积分的实际意义。", [], ["Calculus"]),
    ],
    2: [  # 第二列 - 进阶核心课程
        ("数据结构", 0, "你能组织信息（解锁链表/树/堆/栈），但脑中思维也开始分支过度。", ["高级语言程设"], ["tree","stack","queue"]),
        ("计组原理", 1, "你理解CPU怎么执行代码，但再也不能忍受效率低的程序。", ["计算机导论"], []),
        ("离散数学", 2, "你可以理解空间与维度，但现实中的三维开始失去乐趣。", ["线性代数"], []),
        ("组合数学", 2.5, "你能计算复杂组合，但开始对生活中的选择过度分析。", ["离散数学","高等数学"], []),
        ("概率论", 3, "你能评估风险与不确定性，但开始对每个决定过度担忧。", ["高等数学","离散数学"], []),
    ],
    3: [  # 第三列 - 系统相关课程
        ("数据库系统", 0, "你能存储与索引信息，副作用：开始给生活每一事件打标签归档。", ["数据结构"], ["索引","SQL","范式"]),
        ("计算机网络", 1, "你能解释三次握手，但说话前总是确认：'你听到了吗？'", ["计组原理"], ["路由协议","TCP/IP"]),
        ("操作系统", 2, "你能管理资源并发调度，副作用：你开始尝试给自己现实生活加“优先级”。", ["数据结构", "计组原理"], []),
        ("信号与系统", 3, "你能分析信号处理，副作用：开始用滤波器过滤生活噪音。", ["高等数学","概率论"], []),                                                 
    ],
    4: [  # 第四列 - 编程 &抽象
        ("面向对象程设", 0, "你掌握封装继承多态，副作用：开始对人分类并设计他们的接口。", ["高级语言程设","数据结构"], []),
        ("程序设计范式", 0.5, "你理解函数式与逻辑编程，副作用：开始用Lambda表达情感。", ["高级语言程设","数据结构"], []),
        ("用户交互技术", 1, "你理解用户体验，副作用：开始设计生活的UI/UX。", ["软件工程"], []),
        ("编译原理", 1.5, "你能将语言翻译为指令，副作用：试图“编译”朋友的话。", ["操作系统", "离散数学"], ["编译器","解释器","反编译"]),
        ("软件工程", 2, "你开始写文档与计划，副作用：计划写完计划后拖延计划。", ["操作系统", "数据库系统"], ["文档写作","Teamwork"]),
        ("算法设计分析", 2.5, "你能优化问题解决方案，副作用：生活中事事追求最优解。", ["数据结构", "离散数学"], []),
        ("密码学", 3, "你能加密与解密信息，副作用：开始怀疑所有秘密。", ["离散数学","计算机网络"], []),
    ],
    5: [  # 第五列 - 前沿技术
        ("人工智能导论", 1, "你能训练模型辅助决策，副作用：再也不相信自己的直觉。", ["线性代数", "数据库系统"], []),
        ("Web开发", 0.5, "你能搭网站与交互前端，副作用：所有生活按钮都想右键检查元素。", ["软件工程","数据库系统"], []),
        ("计算机安全", 2, "你能识别攻击模式，副作用：每个链接都怀疑是钓鱼。", ["操作系统", "计算机网络"], []),
        ("游戏开发", 0, "你能创建虚拟世界，副作用：现实变得索然无味。", ["用户交互技术","程序设计范式","面向对象程设"], ["游戏引擎"]),
        ("仿真建模", 2.5, "你能模拟复杂系统，副作用：开始用模型预测生活。", ["高等数学","概率论"], []),
        ("数据挖掘", 1.5, "你能从数据中发现模式，副作用：开始用数据分析人际关系。", ["人工智能导论","数据库系统"], []),
    ],
    6: [  # 第六列 - 超自然（世界观融合）
        ("深度学习", 0, "你训练出了可预测敌人行为的模型，副作用：训练代价极高、电费猛增。", ["人工智能导论","算法设计分析"], []),
        ("区块链", 1, "你能建立去中心化记录系统，但你开始要求一切都需要“上链认证”。", ["数据库系统", "计算机网络"], []),
        ("虚拟现实", 2, "你选择拥抱虚拟，副作用：现实世界变得索然无味。", ["用户交互技术","仿真建模"], ["仿生人会梦到电子羊吗？"]),
    ]
}

lang_levels = {
    1: [
        # 根节点
        ("C", 400, 100, "你终于学会了如何向世界说出 Hello, world!", [], ["HelloWorld"],"Pointer Sword"),
    ],
    2: [
        # C 系分支
        ("C++", 400, 150, "面向对象的力量开始显现。", ["C"], ["OOP"],"Template Greatsword"),
        # ("Pascal", 250, 75, "结构化编程的温柔导师。", ["C"], ["StructuredProgramming"]),
        # # 脚本分支
        ("Python", 550, 125, "你发现缩进也能写出世界。", ["C"], ["Scripting"],"Snake Staff"),
        # ("VisualBasic", 250, 125, "拖一拖，点一点，程序就做好了。", ["C"], ["RapidUI"]),
    ],
    # 3: [
    #     # 从 C++ 分支
    #     ("Java", 250, 175, "一次编写，到处运行（大概）。", ["C++"], ["JVM"]),
    #     ("Rust", 550, 175, "你学会了与内存安全握手。", ["C++"], ["Ownership"]),
    #     ("C#", 400, 200, "微软家的面向对象宠儿。", ["C++"], ["DotNet"]),
    #     # 从 Pascal 分支
    #     ("Delphi", 100, 50, "Pascal 的商业化超进化。", ["Pascal"], ["RAD"]),
    #     # 从 Python 分支
    #     ("JavaScript", 700, 100, "你开始支配浏览器的世界。", ["Python"], ["WebDev"]),
    #     ("Ruby", 700, 150, "优雅至上的动态语言。", ["Python"], ["ElegantCode"]),
    #     # 从 VB 分支
    #     ("VB.NET", 100, 100, "Visual Basic 的现代续作。", ["Visual Basic"], ["DotNet"]),
    # ],
    # 4: [
    #     # Java 分支
    #     ("Kotlin", 250, 225, "Java 的现代化外套。", ["Java"], ["AndroidDev"]),
    #     # Rust 分支
    #     ("Go", 550, 225, "云时代的轻量化编程语言。", ["Rust"], ["Concurrency"]),
    #     # C# 分支
    #     ("F#", 400, 250, "微软的函数式尝试。", ["C#"], ["Functional"]),
    #     # JS 分支
    #     # ("TypeScript", 750, 60, "给 JavaScript 穿上类型的铠甲。", ["JavaScript"], ["StrongTyping"]),
    #     # # Ruby 分支
    #     # ("Elixir", 750, 120, "分布式与并发的诗人。", ["Ruby"], ["ConcurrentProgramming"]),
    #     # VB.NET 分支
    #     ("ASP.NET", 100, 150, "微软的网页全家桶。", ["VB.NET"], ["WebBackend"]),
    # ],
    # 5: [
    #     ("Swift", 400, 50, "苹果生态的第一语言。", ["C"], ["iOSDev"]),
    #     ("PHP", 700, 50, "支撑了一半互联网（真的）。", ["JavaScript"], ["BackendDev"]),
    #     ("Lua", 550, 75, "游戏与嵌入式的脚本大师。", ["C"], ["GameScripting"]),
    # ],
    # 6: [
    #     ("Utility", 400, 300, "你学会了如何用脚本自动化生活。", [], ["Automation"]),
    #     ("Markdown", 100, 350, "你学会了如何用标记语言写文档。", ["Utility"], ["Documentation"]),
    #     ("Latex", 250, 350, "学术论文的排版神器。", ["Utility"], ["AcademicWriting"]),
    #     ("HTML", 250, 300, "网页的骨架语言。", ["Utility"], ["WebMarkup"]),
    #     ("CSS", 100, 300, "网页的美化大师。", ["HTML"], ["WebStyling"]),
    #     ("SQL", 400, 350, "数据库的查询语言。", ["Utility"], ["DatabaseQuery"]),
    #     ("Bash", 550, 350, "命令行的脚本语言。", ["Utility"], ["ShellScripting"]),


    # ]
}

