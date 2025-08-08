import pygame
from font_manager import get_font
from colors import *
import json
from Stupid import Toolbar,Tab


# 科技节点类
class Technode:
    def __init__(self, name, x, y, description="", prerequisites=None, level=1, skills=None, research_time=1.0):
        self.name = name
        self.description = description
        self.x = x
        self.y = y
        self.width = 100
        self.height = 30
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.prerequisites = prerequisites or []
        self.level = level
        self.research_time = research_time  # 研究所需时间（秒）
        self.is_unlocked = False
        self.is_researched = False
        self.is_hovered = False
        self.is_researching = False
        self.research_progress = 0.0  # 研究进度 0.0-1.0
        self.press_start_time = 0
        self.skills = skills or []  # 支持多个技能
        self.learned_skills = set()
        
    def draw(self, screen, small_font):
        # 根据状态选择颜色
        if self.is_researched:
            bg_color = BLACK
            border_color = GREEN
            text_color = GREEN
        elif self.is_unlocked:
            bg_color = BLACK
            border_color = WHITE
            text_color = WHITE
        else:
            bg_color = BLACK
            border_color = GRAY
            text_color = GRAY
            
        # 悬停效果
        if self.is_hovered and self.is_unlocked and not self.is_researched:
            bg_color = tuple(min(255, c + 20) for c in bg_color)
            
        # 绘制节点背景（矩形，类似缺氧风格）
        shadow_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, SHADOW, shadow_rect)
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 3)
        
        # 绘制研究进度条（如果正在研究）
        if self.is_researching and self.research_progress > 0:
            progress_rect = pygame.Rect(self.rect.x + 5, self.rect.bottom - 10, 
                                      int((self.rect.width - 10) * self.research_progress), 5)
            pygame.draw.rect(screen, WHITE, progress_rect)
            pygame.draw.rect(screen, WHITE, 
                           (self.rect.x + 5, self.rect.bottom - 10, self.rect.width - 10, 5), 1)
        
        # 绘制科技名称（分行显示）
        words = self.name.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if small_font.size(test_line)[0] < self.width - 10:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
            
        # 居中显示文本
        total_height = len(lines) * 16
        start_y = self.y - total_height // 2
        
        for i, line in enumerate(lines):
            text_surface = small_font.render(line, True, text_color)
            text_rect = text_surface.get_rect(center=(self.x, start_y + i * 16 + 5))
            screen.blit(text_surface, text_rect)
            
        # # 绘制等级指示器（右上角）
        # level_text = f"L{self.level}"
        # level_surface = small_font.render(level_text, True, text_color)
        # screen.blit(level_surface, (self.rect.right - 25, self.rect.top + 3))

        
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
            
    def update_research(self, current_time):
        if self.is_researching:
            elapsed = (current_time - self.press_start_time) / 1000.0
            self.research_progress = min(1.0, elapsed / self.research_time)
            
            if self.research_progress >= 1.0:
                self.is_researched = True
                self.is_researching = False
                return True
        return False
        
    def cancel_research(self):
        self.is_researching = False
        self.research_progress = 0.0

# 科技树类
class AbilityTree:
    def __init__(self):
        self.nodes = {}
        self.connections = []
        self.researched = set()
        self.selected_node = None
        self.mouse_pressed = False
        self.pressed_node = None
        self.learned_skills = set()
        self.skill_points = 0  # 可手动设置初始点数
        self.setup_Ability_tree("tech", tech_levels)
        self.setup_Ability_tree("language", language_levels)
        self.tabs = Toolbar.create_tabs(self,
            names=[ "Tech","Lang","Algo","Skill"],
            start_pos=(SCREEN_WIDTH -250 , 50),
            direction="col"
        )

    def get_active_tab_name(self):
        for tab in self.tabs:
            if tab.is_active:
                return tab.name.lower()  # tech / skill / lang / ml
        return None
        
    def setup_Ability_tree(self,name,Ability_levels):
        # 按等级分列的科技树设计
        COLUMN_WIDTH = 130
        START_X = 80
        START_Y = 80
        ROW_HEIGHT = 80

        # 创建节点
        for level, Abilitys in Ability_levels.items():
            x = START_X + (level - 1) * COLUMN_WIDTH
            for name, row_pos, desc, prereqs,skills in Abilitys:
                y = START_Y + int(row_pos * ROW_HEIGHT)
                self.nodes[name] = Technode(name, x, y, desc, prereqs, level,skills)
                
        # 设置连接关系
        for node_name, node in self.nodes.items():
            for prereq in node.prerequisites:
                if prereq in self.nodes:
                    self.connections.append((prereq, node_name))
                    
        # 初始解锁第一级科技
        for node_name, node in self.nodes.items():
            if node.level == 1:
                node.is_unlocked = True
                
    def draw_tech_tree(self, screen, font, small_font):
        # 绘制等级分隔线和标题
        for level in range(1, 7):
            x = 80 + (level - 1) * 130
            # 绘制分隔线
            pygame.draw.line(screen, GRAY, (x - 50, 30), (x - 50, 320), 1)
            # 绘制等级标题
            level_title = f"Level {level}"
            title_surface = small_font.render(level_title, True, WHITE)
            title_rect = title_surface.get_rect(center=(x, 40))
            screen.blit(title_surface, title_rect)
        
        # 绘制连接线
        for start_name, end_name in self.connections:
            start_node = self.nodes[start_name]
            end_node = self.nodes[end_name]
            
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
        for node in self.nodes.values():
            node.draw(screen, small_font)
            
        # 绘制选中节点的详细信息
        if self.selected_node:
            self.draw_node_info(screen ,font, small_font)

    def draw(self, screen, font, small_font):
        icon_font = get_font("en", "Cogmind", 20)
        Toolbar.draw_tab_border(self, screen, icon_font, self.tabs)

        subview = self.get_active_tab_name()

        if subview == "skill":
            self.draw_skill_view(screen, font, small_font)
        elif subview == "language":
            self.draw_tech_tree(screen, font, small_font)
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
            status = "finished"
        elif node.is_researching:
            status = f"researching..{int(node.research_progress * 100)}%"
        elif node.is_unlocked:
            status = "available"
        else:
            status = "locked"

        
        # 节点名称
        f1=get_font("ch", "Pixel", 20)
        name_surface = f1.render(node.name, True, WHITE)#要用中文字体
        status_surface = font.render(status, True, WHITE)#用英文字体，紧跟在name后面
        name_width = name_surface.get_width()
        screen.blit(name_surface, (info_x + 10, y_offset))
        screen.blit(status_surface, (info_x + 10 + name_width + 10, y_offset))
        y_offset += 30
        
        # 等级和研究时间
        level_text = f"等级: {node.level}  研究: {node.research_time}s"
        level_surface = small_font.render(level_text, True, WHITE)
        screen.blit(level_surface, (info_x + 10, y_offset))
        y_offset += 25
        
        # 分行显示描述
        words = node.description.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if small_font.size(test_line)[0] < info_width - 20:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
            
        for line in lines[:3]:  # 最多显示3行
            desc_line_surface = small_font.render(line, True, WHITE)
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
            for node in self.nodes.values():
                node.is_hovered = node.contains_point(event.pos)

        # 3. 鼠标点击：切换 tab
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tab in self.tabs:
                if tab.rect and tab.rect.collidepoint(event.pos):
                    for other_tab in self.tabs:
                        other_tab.is_active = (other_tab == tab)
                    return True

            active_view = self.get_active_tab_name()

            if active_view == "skill":
                # 点击技能学习
                for node in self.nodes.values():
                    if node.is_researched and node.skills:
                        for skill in node.skills:
                            rect = getattr(self, f"skill_rect_{skill}", None)
                            if rect and rect.collidepoint(event.pos):
                                if skill not in self.learned_skills and self.skill_points > 0:
                                    self.learned_skills.add(skill)
                                    self.skill_points -= 1
                                    print(f"学习技能：{skill}")
                                    player.apply_skill_effect(player, skill)
                                return True

            else:
                # tech / lang / ml 模式通用
                for node in self.nodes.values():
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
        
    def update(self):
        """更新研究进度"""
        current_time = pygame.time.get_ticks()
        
        # 更新正在研究的节点
        if self.pressed_node and self.pressed_node.is_researching:
            if self.pressed_node.update_research(current_time):
                # 研究完成
                self.researched.add(self.pressed_node.name)
                self.update_unlocked_nodes()
                self.pressed_node = None
                self.skill_points+=1  # 每完成一个科技，获得1点技能点
                
    def update_unlocked_nodes(self):
        """更新可解锁的节点状态"""
        for node in self.nodes.values():
            if not node.is_unlocked and node.can_unlock(self.researched):
                node.is_unlocked = True


# 定义每级科技 (名称, 行位置, 描述, 前置需求 , 技能)
tech_levels = {
    1: [  # 第一列 - 基础课程
        ("高级语言程序设计", 0, "你终于学会了如何向世界说出 Hello, world！（解锁编程交互）副作用：开始把生活当成命令行。", [],["Hello world","C++"]),
        ("计算机导论", 1, "你大致了解计算机的组成与职业前景。副作用：成为'天选打螺丝的人'。", [], []),
        ("线性代数", 2, "逻辑能力+1，但你开始用真值表分析社交。", [], ["Matrix"]),
        ("高等数学", 2.5, "你能处理复杂计算，但开始怀疑微积分的实际意义。", [], ["Calculus"]),
    ],
    2: [  # 第二列 - 进阶核心课程
        ("数据结构", 0, "你能组织信息（解锁链表/树/堆/栈），但脑中思维也开始分支过度。", ["高级语言程序设计"], ["tree","stack","queue"]),
        ("计算机组成原理", 1, "你理解CPU怎么执行代码，但再也不能忍受效率低的程序。", ["计算机导论"], []),
        ("离散数学", 2, "你可以理解空间与维度，但现实中的三维开始失去乐趣。", ["线性代数"], []),
        ("组合数学", 2.5, "你能计算复杂组合，但开始对生活中的选择过度分析。", ["离散数学","高等数学"], []),
        ("概率论", 3, "你能评估风险与不确定性，但开始对每个决定过度担忧。", ["高等数学","离散数学"], []),
    ],
    3: [  # 第三列 - 系统相关课程
        ("操作系统", 0, "你能管理资源并发调度，副作用：你开始尝试给自己现实生活加“优先级”。", ["数据结构", "计算机组成原理"], []),
        ("计算机网络", 1, "你能解释三次握手，但说话前总是确认：'你听到了吗？'", ["计算机组成原理"], ["路由协议","TCP/IP"]),
        ("数据库系统", 2, "你能存储与索引信息，副作用：开始给生活每一事件打标签归档。", ["数据结构"], ["索引","SQL","范式"]),                                                            
    ],
    4: [  # 第四列 - 编程 &抽象
        ("编译原理", 0, "你能将语言翻译为指令，副作用：试图“编译”朋友的话。", ["操作系统", "离散数学"], ["编译器","解释器","反编译"]),
        ("OOP", 1, "你掌握封装继承多态，副作用：开始对人分类并设计他们的接口。", ["高级语言程序设计","数据结构"], []),
        ("程序设计范式", 1.5, "你理解函数式与逻辑编程，副作用：开始用Lambda表达情感。", ["高级语言程序设计","数据结构"], []),
        ("软件工程", 2, "你开始写文档与计划，副作用：计划写完计划后拖延计划。", ["操作系统", "数据库系统"], ["文档写作","Teamwork"]),
        ("算法设计与分析", 2.5, "你能优化问题解决方案，副作用：生活中事事追求最优解。", ["数据结构", "离散数学"], []),
        ("密码学", 3, "你能加密与解密信息，副作用：开始怀疑所有秘密。", ["离散数学","计算机网络"], []),

    ],
    5: [  # 第五列 - 前沿技术
        ("人工智能导论", 0, "你能训练模型辅助决策，副作用：再也不相信自己的直觉。", ["线性代数", "数据库系统"], []),
        ("Web开发", 1, "你能搭网站与交互前端，副作用：所有生活按钮都想右键检查元素。", ["软件工程"], []),
        ("计算机安全", 2, "你能识别攻击模式，副作用：每个链接都怀疑是钓鱼。", ["操作系统", "计算机网络"], []),
        ("用户交互技术", 3, "你理解用户体验，副作用：开始设计生活的UI/UX。", ["软件工程"], []),
        ("游戏开发", 1.5, "你能创建虚拟世界，副作用：现实变得索然无味。", ["用户交互技术"], ["游戏引擎"]),
        ("仿真建模", 2.5, "你能模拟复杂系统，副作用：开始用模型预测生活。", ["高等数学","概率论"], []),
        ("数据挖掘", 3, "你能从数据中发现模式，副作用：开始用数据分析人际关系。", ["人工智能导论","数据库系统"], []),
    ],
    6: [  # 第六列 - 超自然（世界观融合）
        ("深度学习", 0, "你训练出了可预测敌人行为的模型，副作用：训练代价极高、电费猛增，社交-5。", ["人工智能导论","算法设计与分析"], []),
        ("区块链", 1, "你能建立去中心化记录系统，但你开始要求一切都需要“上链认证”。", ["数据库系统", "计算机网络"], []),
        ("量子计算", 2, "你理解叠加与纠缠，副作用：你的身份与决定都开始不确定。", ["深度学习"], ["量子纠缠","量子位"]),
        ("虚拟现实", 3, "你能创建沉浸式体验，副作用：现实世界变得索然无味。", ["用户交互技术"], ["仿生人会梦到电子羊吗？"]),
    ]
}

language_levels = {
    1: [  # 第一列 - 基础课程
        ("C", 0, "你终于学会了如何向世界说出 Hello, world!", [],[]),
    ],
    2: [
        ("C++", 0, "你终于学会了如何向世界说出 Hello, world!", [],["C"]),
    ]
}