import pygame
class HelpSystem:
    def __init__(self):
        self.is_visible = False
        self.current_page = "main"  # 默认帮助页
        self.help_texts = {
            "main": [
                "🗡 战斗指南",
                "- 方向键移动",
                "- 数字键添加技能到序列",
                "- 空格：执行技能序列",
                "- R：重开游戏",
                "- ESC：返回主菜单",
                "- ?：查看本指南"
            ],
            "skills": [
                "📚 技能树指南",
                "- 点击技能图标学习技能",
                "- 某些技能解锁新武器或新能力",
                "- 技能不能重复学习",
                "- 部分技能可能互斥，请谨慎选择",
                "- ESC：返回科技页"
            ],
            "tech": [
                "🔬 科技树指南",
                "- 长按解锁科技，松开取消研究",
                "- 某些课程需要前置课程",
                "- 点击查看课程描述",
                "- ESC：关闭科技页"
            ],
            # 其他页面...
        }

    def toggle(self, current_page):
        self.is_visible = not self.is_visible
        self.current_page = current_page

    def draw(self, screen, font):
        if not self.is_visible:
            return
        lines = self.help_texts.get(self.current_page, ["暂无帮助内容"])
        help_bg = pygame.Surface((600, 300))
        # help_bg.set_alpha(220)
        help_bg.fill((30, 30, 30))
        screen.blit(help_bg, (100, 100))
        # print(self.help_texts)
        for i, line in enumerate(lines):
            text_surf = font.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (120, 120 + i * 28))
