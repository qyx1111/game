import pygame
import random
import os
import sys
import time

# --- 配置常量 ---
# 屏幕设置
SCREEN_WIDTH = 2000
SCREEN_HEIGHT = 1000
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (100, 149, 237)
GREEN = (60, 179, 113)
RED = (220, 20, 60)

# 卡牌设置
CARD_PADDING = 10 # 卡牌间距
ANIMATION_SPEED = 0.1 # 翻转动画速度 (模拟，实际为延迟)
MISMATCH_DELAY = 0.5 # 错误匹配后显示的时间 (秒)
SHOW_NAME_DURATION = 1.5 # 显示节气名称的时间 (秒)

# 资源路径
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
IMG_DIR = os.path.join(ASSETS_DIR, 'images')
SND_DIR = os.path.join(ASSETS_DIR, 'sounds')
FONT_NAME = "SimHei" # 使用黑体或其他支持中文的字体

# 成就 (更新为季节主题)
achievements = {
    "complete_spring": {"name": "春之初识", "unlocked": False, "desc": "完成春季关卡"},
    "fast_summer": {"name": "夏日疾风", "unlocked": False, "desc": "在45秒内完成夏季关卡"},
    "perfect_autumn": {"name": "秋之零误", "unlocked": False, "desc": "在秋季关卡中没有错误匹配"},
    "complete_all": {"name": "四季轮回", "unlocked": False, "desc": "完成所有季节关卡"}
}
show_achievement_timer = 0
achievement_to_show = None

# --- 关卡定义 (恢复为 3x4 网格) ---
LEVELS = [
    {"id": 1, "grid": (3, 4), "theme": "spring", "time_limit": 90}, # 3行4列 = 12张牌 = 6对
    {"id": 2, "grid": (3, 4), "theme": "summer", "time_limit": 90},
    {"id": 3, "grid": (3, 4), "theme": "autumn", "time_limit": 100},
    {"id": 4, "grid": (3, 4), "theme": "winter", "time_limit": 100},
]
# 季节名称映射 (用于显示)
THEME_NAMES = {
    "spring": "春",
    "summer": "夏",
    "autumn": "秋",
    "winter": "冬"
}

# --- 工具函数 ---
def load_image(filepath, size=None, use_colorkey=False, colorkey_color=BLACK):
    """加载图片并可选地调整大小和设置透明色"""
    try:
        if not os.path.isabs(filepath) and not os.path.exists(filepath):
            path = os.path.join(IMG_DIR, filepath)
        else:
            path = filepath

        image = pygame.image.load(path).convert()
    except pygame.error as e:
        print(f"无法加载图片: {path} - {e}")
        image = pygame.Surface([100, 100])
        image.fill(GRAY)
        pygame.draw.rect(image, RED, image.get_rect(), 2)
        return image

    if size:
        image = pygame.transform.scale(image, size)
    if use_colorkey:
        image.set_colorkey(colorkey_color)
    else:
        image = image.convert_alpha()
    return image

def load_sound(filename):
    """加载声音文件"""
    path = os.path.join(SND_DIR, filename)
    if not os.path.exists(path):
        print(f"警告: 声音文件未找到: {path}")
        return None
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except pygame.error as e:
        print(f"无法加载声音: {path} - {e}")
        return None

def draw_text(surface, text, size, x, y, color=WHITE, font_name=FONT_NAME, center=False):
    """在指定位置绘制文本"""
    try:
        if font_name and os.path.isfile(font_name):
            font = pygame.font.Font(font_name, size)
        else:
            font = pygame.font.SysFont(font_name or 'arial', size)
    except:
        font = pygame.font.SysFont('arial', size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
    return text_rect

# --- 卡牌类 ---
class Card(pygame.sprite.Sprite):
    def __init__(self, item_name, theme, card_size, image_path):
        super().__init__()
        self.item_name = item_name
        self.theme = theme
        self.card_size = card_size
        self.image_path = image_path
        self.is_face_up = False
        self.is_matched = False
        self._load_images()
        self.image = self.image_back
        self.rect = self.image.get_rect()
        self.flip_sound = load_sound("flip.wav")
        self.is_flipping = False
        self.flip_progress = 0

    def _load_images(self):
        """加载卡牌正面和背面图片"""
        try:
            self.image_back_orig = load_image("card_back.png")
            self.image_back = pygame.transform.scale(self.image_back_orig, self.card_size)
        except Exception as e:
            print(f"无法加载卡背图片: {e}")
            self.image_back = pygame.Surface(self.card_size)
            self.image_back.fill(BLUE)
            pygame.draw.rect(self.image_back, WHITE, self.image_back.get_rect(), 2)

        try:
            self.image_front_orig = load_image(self.image_path)
            self.image_front = pygame.transform.scale(self.image_front_orig, self.card_size)
        except Exception as e:
            print(f"无法加载节气图片 {self.image_path}: {e}")
            self.image_front = pygame.Surface(self.card_size)
            self.image_front.fill(GREEN)
            draw_text(self.image_front, self.item_name, 16, self.card_size[0]//2, self.card_size[1]//2, BLACK, center=True)

    def flip(self, instant=False):
        """翻转卡牌"""
        if self.is_matched or self.is_flipping:
            return

        if self.flip_sound:
            self.flip_sound.play()

        self.is_face_up = not self.is_face_up
        if self.is_face_up:
            self.image = self.image_front
        else:
            self.image = self.image_back

    def update(self, dt):
        """更新卡牌状态（用于动画）"""
        pass

    def draw(self, surface):
        """绘制卡牌"""
        surface.blit(self.image, self.rect)

    def handle_click(self, pos):
        """检查点击是否在卡牌上"""
        return self.rect.collidepoint(pos)

# --- 游戏主类 ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("二十四节气 记忆匹配")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.game_state = "menu"

        self.current_level_index = 0
        self.cards = pygame.sprite.Group()
        self.flipped_cards = []
        self.matched_pairs = 0
        self.total_pairs = 0
        self.attempts = 0
        self.mistakes_current_level = 0

        self.start_time = 0
        self.elapsed_time = 0
        self.level_time_limit = 0

        self.mismatch_timer = 0
        self.show_name_timer = 0
        self.item_name_to_show = ""
        self.item_name_pos = (0, 0)

        self.match_sound = load_sound("match.wav")
        self.win_sound = load_sound("win.wav")
        self.bgm = load_sound("bgm.wav")
        if self.bgm:
            self.bgm.play(loops=-1)

        try:
            self.background_img = load_image("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background_img = None

        self.show_achievement_timer = 0
        self.achievement_to_show = None

    def load_level_assets(self, theme):
        """为当前关卡主题加载所需资源"""
        pass

    def setup_level(self, level_index):
        """设置新关卡"""
        if level_index >= len(LEVELS):
            self.check_achievements(all_levels_completed=True)
            self.game_state = "all_levels_complete"
            return

        level_data = LEVELS[level_index]
        self.current_level_index = level_index
        grid_rows, grid_cols = level_data["grid"]
        theme = level_data["theme"]
        self.level_time_limit = level_data.get("time_limit", 0)

        self.load_level_assets(theme)

        self.cards.empty()
        self.flipped_cards = []
        self.matched_pairs = 0
        self.total_pairs = (grid_rows * grid_cols) // 2
        self.attempts = 0
        self.mistakes_current_level = 0

        top_margin = 80
        available_width = SCREEN_WIDTH - (grid_cols + 1) * CARD_PADDING
        available_height = SCREEN_HEIGHT - top_margin - (grid_rows + 1) * CARD_PADDING
        card_width = available_width // grid_cols
        card_height = available_height // grid_rows
        card_size = (min(card_width, card_height), min(card_width, card_height))

        total_grid_width = grid_cols * card_size[0] + (grid_cols - 1) * CARD_PADDING
        total_grid_height = grid_rows * card_size[1] + (grid_rows - 1) * CARD_PADDING
        start_x = (SCREEN_WIDTH - total_grid_width) // 2
        start_y = top_margin + (available_height - total_grid_height) // 2

        theme_img_dir = os.path.join(IMG_DIR, theme)
        available_solar_terms = []
        try:
            for item in os.listdir(theme_img_dir):
                item_path = os.path.join(theme_img_dir, item)
                if os.path.isdir(item_path):
                    has_images = False
                    for f in os.listdir(item_path):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                            has_images = True
                            break
                    if has_images:
                        available_solar_terms.append(item)
                    else:
                        print(f"警告: 节气目录 '{item_path}' 为空或不包含图片，已跳过。")

        except FileNotFoundError:
            print(f"错误: 找不到主题图片目录: {theme_img_dir}")
            self.is_running = False
            return
        except Exception as e:
            print(f"读取主题子目录时出错: {e}")
            self.is_running = False
            return

        if len(available_solar_terms) < self.total_pairs:
            print(f"错误: 主题 '{theme}' 的有效节气目录不足 ({len(available_solar_terms)}), 需要 {self.total_pairs} 个。")
            print(f"请确保在 '{theme_img_dir}' 下有足够的包含图片的节气子目录。")
            self.is_running = False
            return

        selected_solar_terms = random.sample(available_solar_terms, self.total_pairs)

        card_data = []
        for term_name in selected_solar_terms:
            term_dir = os.path.join(theme_img_dir, term_name)
            try:
                images_in_term = [f for f in os.listdir(term_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if not images_in_term:
                    print(f"错误: 节气目录 '{term_dir}' 中找不到图片文件。")
                    self.is_running = False
                    return
                chosen_image_name = random.choice(images_in_term)
                chosen_image_path = os.path.join(term_dir, chosen_image_name)
                card_data.append((term_name, chosen_image_path))
            except Exception as e:
                print(f"读取节气 '{term_name}' 的图片时出错: {e}")
                self.is_running = False
                return

        paired_card_data = card_data * 2
        random.shuffle(paired_card_data)

        data_index = 0
        for row in range(grid_rows):
            for col in range(grid_cols):
                if data_index < len(paired_card_data):
                    item_name, image_path = paired_card_data[data_index]
                    card = Card(item_name, theme, card_size, image_path)
                    x = start_x + col * (card_size[0] + CARD_PADDING)
                    y = start_y + row * (card_size[1] + CARD_PADDING)
                    card.rect.topleft = (x, y)
                    self.cards.add(card)
                    data_index += 1

        self.game_state = "playing"
        self.start_time = time.time()
        self.mismatch_timer = 0
        self.show_name_timer = 0
        self.item_name_to_show = ""

    def run(self):
        """主游戏循环"""
        while self.is_running:
            self.dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """处理事件（输入）"""
        global achievement_to_show

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                if self.game_state in ["level_complete", "game_over", "all_levels_complete"]:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.game_state == "level_complete":
                            self.setup_level(self.current_level_index + 1)
                        elif self.game_state == "all_levels_complete":
                            self.game_state = "menu"
                        else:
                            self.game_state = "menu"
                elif self.game_state == "menu":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.setup_level(0)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_state == "playing" and self.mismatch_timer <= 0:
                    pos = pygame.mouse.get_pos()
                    for card in self.cards:
                        if not card.is_matched and not card.is_face_up and card.handle_click(pos):
                            if len(self.flipped_cards) < 2:
                                card.flip()
                                self.flipped_cards.append(card)
                                if len(self.flipped_cards) == 2:
                                    self.attempts += 1
                            break

    def check_matches(self):
        """检查翻开的两张牌是否匹配"""
        if len(self.flipped_cards) == 2:
            card1, card2 = self.flipped_cards

            if card1.item_name == card2.item_name:
                card1.is_matched = True
                card2.is_matched = True
                self.matched_pairs += 1
                if self.match_sound:
                    self.match_sound.play()

                self.item_name_to_show = card1.item_name
                center_x = (card1.rect.centerx + card2.rect.centerx) // 2
                center_y = min(card1.rect.top, card2.rect.top) - 20
                self.item_name_pos = (center_x, center_y)
                self.show_name_timer = SHOW_NAME_DURATION

                self.flipped_cards = []

                if self.matched_pairs == self.total_pairs:
                    self.game_state = "level_complete"
                    if self.win_sound:
                        self.win_sound.play()
                    self.check_achievements(level_won=True)

            else:
                self.mistakes_current_level += 1
                self.mismatch_timer = MISMATCH_DELAY

    def update(self):
        """更新游戏状态"""
        global show_achievement_timer, achievement_to_show

        current_time = time.time()

        if self.show_achievement_timer > 0:
            self.show_achievement_timer -= self.dt
            if self.show_achievement_timer <= 0:
                achievement_to_show = None

        if self.game_state == "playing":
            self.cards.update(self.dt)

            self.elapsed_time = current_time - self.start_time

            if self.level_time_limit > 0 and self.elapsed_time > self.level_time_limit:
                self.game_state = "game_over"
                return

            if self.show_name_timer > 0:
                self.show_name_timer -= self.dt
                if self.show_name_timer <= 0:
                    self.item_name_to_show = ""

            if self.mismatch_timer > 0:
                self.mismatch_timer -= self.dt
                if self.mismatch_timer <= 0:
                    for card in self.flipped_cards:
                        if not card.is_matched:
                            card.flip()
                    self.flipped_cards = []
            else:
                self.check_matches()

    def check_achievements(self, level_won=False, all_levels_completed=False):
        """检查并解锁成就"""
        global achievement_to_show, show_achievement_timer

        newly_unlocked = []

        if level_won:
            level_id = LEVELS[self.current_level_index]["id"]
            theme = LEVELS[self.current_level_index]["theme"]

            if theme == "spring" and not achievements["complete_spring"]["unlocked"]:
                achievements["complete_spring"]["unlocked"] = True
                newly_unlocked.append(achievements["complete_spring"])

            if theme == "summer" and self.elapsed_time <= 45 and not achievements["fast_summer"]["unlocked"]:
                achievements["fast_summer"]["unlocked"] = True
                newly_unlocked.append(achievements["fast_summer"])

            if theme == "autumn" and self.mistakes_current_level == 0 and not achievements["perfect_autumn"]["unlocked"]:
                achievements["perfect_autumn"]["unlocked"] = True
                newly_unlocked.append(achievements["perfect_autumn"])

        if all_levels_completed and not achievements["complete_all"]["unlocked"]:
            achievements["complete_all"]["unlocked"] = True
            newly_unlocked.append(achievements["complete_all"])

        if newly_unlocked:
            achievement_to_show = newly_unlocked[0]
            show_achievement_timer = 3.0
            print(f"成就解锁: {achievement_to_show['name']}")

    def draw_menu(self):
        """绘制主菜单界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(BLUE)

        draw_text(self.screen, "二十四节气 记忆匹配", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        draw_text(self.screen, "按 Enter 或 空格 开始游戏", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        draw_text(self.screen, "按 ESC 返回菜单或退出", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, GRAY, center=True)

        unlocked_count = sum(1 for ach in achievements.values() if ach["unlocked"])
        draw_text(self.screen, f"已解锁成就: {unlocked_count} / {len(achievements)}", 18, 10, SCREEN_HEIGHT - 30, WHITE)

    def draw_playing(self):
        """绘制游戏进行中界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(BLACK)
        self.cards.draw(self.screen)

        remaining_time = self.level_time_limit - int(self.elapsed_time) if self.level_time_limit > 0 else int(self.elapsed_time)
        timer_text = f"剩余时间: {remaining_time}s" if self.level_time_limit > 0 else f"用时: {int(self.elapsed_time)}s"
        timer_color = RED if self.level_time_limit > 0 and remaining_time < 10 else WHITE
        draw_text(self.screen, timer_text, 30, SCREEN_WIDTH - 250, 10, timer_color)

        level_theme = LEVELS[self.current_level_index]["theme"]
        level_name = THEME_NAMES.get(level_theme, level_theme.capitalize())
        level_id = LEVELS[self.current_level_index]["id"]
        draw_text(self.screen, f"关卡 {level_id}: {level_name}", 30, 10, 10, WHITE)

        draw_text(self.screen, f"已匹配: {self.matched_pairs} / {self.total_pairs}", 24, 10, 50, WHITE)
        draw_text(self.screen, f"尝试: {self.attempts}", 24, SCREEN_WIDTH - 150, 50, WHITE)

        if self.item_name_to_show and self.show_name_timer > 0:
            draw_text(self.screen, self.item_name_to_show, 36, self.item_name_pos[0], self.item_name_pos[1], GREEN, center=True)

        if achievement_to_show and show_achievement_timer > 0:
            self.draw_achievement_popup(achievement_to_show)

    def draw_level_complete(self):
        """绘制关卡完成界面"""
        self.screen.fill(GREEN)
        level_theme = LEVELS[self.current_level_index]["theme"]
        level_name = THEME_NAMES.get(level_theme, level_theme.capitalize())
        level_id = LEVELS[self.current_level_index]["id"]
        draw_text(self.screen, f"关卡 {level_id} ({level_name}) 完成!", 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        draw_text(self.screen, f"用时: {int(self.elapsed_time)} 秒", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, WHITE, center=True)
        draw_text(self.screen, f"尝试次数: {self.attempts}", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, WHITE, center=True)
        draw_text(self.screen, f"错误次数: {self.mistakes_current_level}", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60, WHITE if self.mistakes_current_level == 0 else RED, center=True)

        if self.current_level_index + 1 < len(LEVELS):
            next_level_theme = LEVELS[self.current_level_index + 1]["theme"]
            next_level_name = THEME_NAMES.get(next_level_theme, next_level_theme.capitalize())
            draw_text(self.screen, f"按 Enter 或 空格 进入下一关 ({next_level_name})", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)
        else:
            draw_text(self.screen, "即将进入最终结算...", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)

    def draw_game_over(self):
        """绘制游戏结束界面"""
        self.screen.fill(RED)
        draw_text(self.screen, "游戏结束", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        if self.level_time_limit > 0 and self.elapsed_time > self.level_time_limit:
            draw_text(self.screen, "时间到!", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        else:
            draw_text(self.screen, "挑战失败", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)

        draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)

    def draw_all_levels_complete(self):
        """绘制所有关卡完成界面"""
        self.screen.fill(BLUE)
        draw_text(self.screen, "恭喜!", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        draw_text(self.screen, "你已完成所有季节的挑战!", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        if achievements["complete_all"]["unlocked"]:
            draw_text(self.screen, f"成就解锁: {achievements['complete_all']['name']}", 24, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, GREEN, center=True)

        draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)

    def draw_achievement_popup(self, achievement):
        """绘制成就解锁的弹出提示"""
        popup_width = 300
        popup_height = 100
        popup_x = SCREEN_WIDTH - popup_width - 20
        popup_y = 80

        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        s = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        s.fill((200, 200, 200, 200))
        self.screen.blit(s, (popup_x, popup_y))
        pygame.draw.rect(self.screen, WHITE, popup_rect, width=2, border_radius=10)

        draw_text(self.screen, "成就解锁!", 24, popup_x + popup_width // 2, popup_y + 20, BLACK, center=True)
        draw_text(self.screen, achievement['name'], 20, popup_x + popup_width // 2, popup_y + 50, BLACK, center=True)
        draw_text(self.screen, achievement['desc'], 16, popup_x + popup_width // 2, popup_y + 75, BLACK, center=True)

    def draw(self):
        """根据游戏状态调用相应的绘制函数"""
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "playing":
            self.draw_playing()
        elif self.game_state == "level_complete":
            self.draw_level_complete()
        elif self.game_state == "game_over":
            self.draw_game_over()
        elif self.game_state == "all_levels_complete":
            self.draw_all_levels_complete()
        else:
            self.screen.fill(BLACK)
            draw_text(self.screen, f"未知游戏状态: {self.game_state}", 30, 100, 100, RED)

        pygame.display.flip()

# --- 游戏入口 ---
if __name__ == '__main__':
    if not os.path.isdir(ASSETS_DIR):
        print(f"错误: 资源目录 'assets' 未找到。正在尝试创建...")
        try:
            os.makedirs(ASSETS_DIR)
            os.makedirs(IMG_DIR)
            os.makedirs(SND_DIR)
            print("'assets' 目录已创建。")
        except Exception as e:
            print(f"创建 'assets' 目录失败: {e}")
            sys.exit()

    themes_to_check = ["spring", "summer", "autumn", "winter"]
    dirs_created = False
    required_subdirs_exist = True

    for theme in themes_to_check:
        img_theme_dir = os.path.join(IMG_DIR, theme)
        snd_theme_dir = os.path.join(SND_DIR, theme)

        if not os.path.isdir(img_theme_dir):
            try:
                os.makedirs(img_theme_dir)
                print(f"已创建图片目录: {img_theme_dir}")
                dirs_created = True
            except Exception as e:
                print(f"创建目录 {img_theme_dir} 失败: {e}")
                required_subdirs_exist = False
                continue

        try:
            solar_term_dirs = [d for d in os.listdir(img_theme_dir) if os.path.isdir(os.path.join(img_theme_dir, d))]
            if len(solar_term_dirs) < 6:
                print(f"警告: 主题 '{theme}' 的图片目录 '{img_theme_dir}' 下节气子目录不足 ({len(solar_term_dirs)}个)，需要至少 6 个。")
                required_subdirs_exist = False
                if dirs_created or not solar_term_dirs:
                    print(f"  请在 '{img_theme_dir}' 下创建节气名称的子目录 (例如: 立春, 雨水, ...)，并在每个子目录中放入至少一张图片。")

        except FileNotFoundError:
            print(f"错误: 无法访问主题图片目录: {img_theme_dir}")
            required_subdirs_exist = False
        except Exception as e:
            print(f"检查主题 '{theme}' 的子目录时出错: {e}")
            required_subdirs_exist = False

        if not os.path.isdir(snd_theme_dir):
            try:
                os.makedirs(snd_theme_dir)
                print(f"已创建声音目录: {snd_theme_dir}")
            except Exception as e:
                print(f"创建目录 {snd_theme_dir} 失败: {e}")

    if not required_subdirs_exist:
        print("\n错误：缺少必要的节气图片或目录结构不完整，无法启动游戏。")
        print("请根据上面的提示创建目录和添加图片文件。")
        sys.exit()
    elif dirs_created:
        print("\n请注意：已创建所需的季节图片主目录。")
        print("请确保在每个季节目录下创建了至少6个节气子目录，并在其中放入图片。")
        print("例如: assets/images/spring/立春/图片1.png")

    required_sounds = ["flip.wav", "match.wav", "win.wav", "bgm.wav"]
    missing_sounds = []
    for sound_file in required_sounds:
        if not os.path.exists(os.path.join(SND_DIR, sound_file)):
            missing_sounds.append(sound_file)
    if missing_sounds:
        print(f"\n警告: 缺少通用声音文件: {', '.join(missing_sounds)}。游戏仍可运行，但会缺少音效。")
        print(f"请将这些文件放入 {SND_DIR} 目录。")

    game = Game()
    game.run()