import pygame
import random
import os
import sys
import time

# --- 配置常量 ---
# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
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
SHOW_NAME_DURATION = 1.5 # 显示动物名称的时间 (秒)

# 资源路径
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
IMG_DIR = os.path.join(ASSETS_DIR, 'images')
SND_DIR = os.path.join(ASSETS_DIR, 'sounds')
FONT_NAME = "SimSun" # 使用宋体 # 使用默认字体，或指定 'your_font.ttf' 的路径

# 成就 (简单示例)
achievements = {
    "level_1_complete": {"name": "森林探险家", "unlocked": False, "desc": "完成第一关"},
    "level_2_fast": {"name": "海洋急速", "unlocked": False, "desc": "在60秒内完成第二关"},
    "perfect_match": {"name": "完美记忆", "unlocked": False, "desc": "在一关中没有错误匹配"}
}
show_achievement_timer = 0
achievement_to_show = None

# --- 关卡定义 ---
LEVELS = [
    {"id": 1, "grid": (3, 2), "theme": "forest", "time_limit": 120}, # 3行2列 = 6张牌 = 3对
    {"id": 2, "grid": (4, 3), "theme": "ocean", "time_limit": 90},  # 4行3列 = 12张牌 = 6对
    {"id": 3, "grid": (4, 4), "theme": "forest", "time_limit": 150}, # 4行4列 = 16张牌 = 8对
]

# --- 工具函数 ---
def load_image(filename, size=None, use_colorkey=False, colorkey_color=BLACK):
    """加载图片并可选地调整大小和设置透明色"""
    path = os.path.join(IMG_DIR, filename)
    try:
        image = pygame.image.load(path).convert()
    except pygame.error as e:
        print(f"无法加载图片: {path} - {e}")
        # 返回一个占位符表面
        image = pygame.Surface([100, 100])
        image.fill(GRAY)
        pygame.draw.rect(image, RED, image.get_rect(), 2)
        return image

    if size:
        image = pygame.transform.scale(image, size)
    if use_colorkey:
        image.set_colorkey(colorkey_color)
    else:
        image = image.convert_alpha() # 保留 Alpha 通道
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
        if font_name and os.path.isfile(font_name):  # 检查是否为文件路径
            font = pygame.font.Font(font_name, size)
        else:  # 使用系统字体
            font = pygame.font.SysFont(font_name or 'arial', size)
    except:
        font = pygame.font.SysFont('arial', size)  # 回退到系统字体
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
    return text_rect  # 返回 Rect 以便进行点击检测等

# --- 卡牌类 ---
class Card(pygame.sprite.Sprite):
    def __init__(self, animal_name, theme, card_size):
        super().__init__()
        self.animal_name = animal_name
        self.theme = theme
        self.card_size = card_size
        self.is_face_up = False
        self.is_matched = False
        self._load_images()
        self.image = self.image_back # 初始显示背面
        self.rect = self.image.get_rect()
        self.flip_sound = load_sound("flip.wav")

        # 简单的翻转动画状态 (可以用更复杂的实现)
        self.is_flipping = False
        self.flip_progress = 0 # 0 to 1

    def _load_images(self):
        """加载卡牌正面和背面图片"""
        # 加载背面
        try:
            self.image_back_orig = load_image("card_back.png")
            self.image_back = pygame.transform.scale(self.image_back_orig, self.card_size)
        except Exception as e:
            print(f"无法加载卡背图片: {e}")
            self.image_back = pygame.Surface(self.card_size)
            self.image_back.fill(BLUE) # 备用颜色
            pygame.draw.rect(self.image_back, WHITE, self.image_back.get_rect(), 2)


        # 加载正面 (动物图片)
        front_image_path = os.path.join(self.theme, f"{self.animal_name}.png")
        try:
            self.image_front_orig = load_image(front_image_path)
            self.image_front = pygame.transform.scale(self.image_front_orig, self.card_size)
        except Exception as e:
            print(f"无法加载动物图片 {front_image_path}: {e}")
            self.image_front = pygame.Surface(self.card_size)
            self.image_front.fill(GREEN) # 备用颜色
            draw_text(self.image_front, self.animal_name[:3], 20, 0, 0, BLACK)


    def flip(self, instant=False):
        """翻转卡牌"""
        if self.is_matched or self.is_flipping:
            return

        if self.flip_sound:
            self.flip_sound.play()

        self.is_face_up = not self.is_face_up
        # 简单模拟翻转：直接切换图片
        if self.is_face_up:
            self.image = self.image_front
        else:
            self.image = self.image_back
        # # 更平滑的动画（可选，会增加复杂度）
        # self.is_flipping = True
        # self.flip_progress = 0

    def update(self, dt):
        """更新卡牌状态（用于动画）"""
        if self.is_flipping:
             self.flip_progress += dt / ANIMATION_SPEED
             if self.flip_progress >= 1:
                 self.flip_progress = 1
                 self.is_flipping = False
                 # 动画完成，设置最终图像
                 self.image = self.image_front if self.is_face_up else self.image_back
             else:
                 # 模拟缩放动画
                 scale = abs(1 - 2 * self.flip_progress) # 从 1 到 0 再到 1
                 center = self.rect.center
                 if self.flip_progress < 0.5: # 缩小阶段
                     img_to_scale = self.image_back if self.is_face_up else self.image_front # 缩小旧图片
                 else: # 放大阶段
                     img_to_scale = self.image_front if self.is_face_up else self.image_back # 放大新图片

                 new_width = int(self.card_size[0] * scale)
                 if new_width > 0:
                      scaled_image = pygame.transform.scale(img_to_scale, (new_width, self.card_size[1]))
                      self.image = scaled_image
                      self.rect = self.image.get_rect(center=center)
                 else: # 宽度为0时显示空白或背景色
                     self.image = pygame.Surface((1, self.card_size[1]))
                     self.image.fill(BLACK) # 或者屏幕背景色
                     self.image.set_colorkey(BLACK)
                     self.rect = self.image.get_rect(center=center)
        pass # 简单实现不需要 update

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
        pygame.mixer.init() # 初始化声音系统
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("动物记忆匹配")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.game_state = "menu" # "menu", "playing", "level_complete", "game_over", "all_levels_complete"

        self.current_level_index = 0
        self.cards = pygame.sprite.Group()
        self.flipped_cards = [] # 存储当前翻开的卡牌 (最多2张)
        self.matched_pairs = 0
        self.total_pairs = 0
        self.attempts = 0 # 尝试次数
        self.mistakes_current_level = 0 # 当前关卡错误次数 (用于成就)

        # 计时器
        self.start_time = 0
        self.elapsed_time = 0
        self.level_time_limit = 0

        # 延迟计时器
        self.mismatch_timer = 0
        self.show_name_timer = 0
        self.animal_name_to_show = ""
        self.animal_name_pos = (0, 0)

        # 声音
        self.match_sound = load_sound("match.wav")
        self.win_sound = load_sound("win.wav")
        self.animal_sounds = {} # 按主题和动物名称加载
        self.bgm = load_sound("bgm.wav")
        if self.bgm:
            self.bgm.play(loops=-1) # 循环播放背景音乐

        # 加载背景图
        try:
            self.background_img = load_image("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background_img = None # 没有背景图也没关系

        # 成就相关
        self.show_achievement_timer = 0
        self.achievement_to_show = None

    def load_level_assets(self, theme):
        """为当前关卡主题加载动物声音"""
        self.animal_sounds.clear()
        theme_sound_dir = os.path.join(SND_DIR, theme)
        if not os.path.isdir(theme_sound_dir):
             print(f"警告: 找不到主题声音目录: {theme_sound_dir}")
             return

        # 假设图片文件名和声音文件名（无扩展名）相同
        theme_image_dir = os.path.join(IMG_DIR, theme)
        try:
            for filename in os.listdir(theme_image_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    animal_name = os.path.splitext(filename)[0]
                    sound_path_wav = os.path.join(theme, f"{animal_name}.wav")
                    sound_path_ogg = os.path.join(theme, f"{animal_name}.ogg") # 也支持ogg
                    sound = load_sound(sound_path_wav) or load_sound(sound_path_ogg)
                    if sound:
                        self.animal_sounds[animal_name] = sound
                    else:
                        print(f"未找到或无法加载动物声音: {animal_name} (theme: {theme})")
        except FileNotFoundError:
             print(f"警告: 找不到主题图片目录: {theme_image_dir}")
        except Exception as e:
            print(f"加载关卡资源时出错: {e}")


    def setup_level(self, level_index):
        """设置新关卡"""
        if level_index >= len(LEVELS):
            self.game_state = "all_levels_complete"
            return

        level_data = LEVELS[level_index]
        self.current_level_index = level_index
        grid_rows, grid_cols = level_data["grid"]
        theme = level_data["theme"]
        self.level_time_limit = level_data.get("time_limit", 0) # 获取时间限制

        self.load_level_assets(theme) # 加载对应主题的声音

        self.cards.empty()
        self.flipped_cards = []
        self.matched_pairs = 0
        self.total_pairs = (grid_rows * grid_cols) // 2
        self.attempts = 0
        self.mistakes_current_level = 0

        # --- 计算卡牌尺寸和布局 ---
        # 留出顶部空间给计时器等信息
        top_margin = 80
        available_width = SCREEN_WIDTH - (grid_cols + 1) * CARD_PADDING
        available_height = SCREEN_HEIGHT - top_margin - (grid_rows + 1) * CARD_PADDING
        card_width = available_width // grid_cols
        card_height = available_height // grid_rows
        card_size = (min(card_width, card_height), min(card_width, card_height)) # 保持卡牌正方形或使用较小边

        # 重新计算起始位置以居中
        total_grid_width = grid_cols * card_size[0] + (grid_cols - 1) * CARD_PADDING
        total_grid_height = grid_rows * card_size[1] + (grid_rows - 1) * CARD_PADDING
        start_x = (SCREEN_WIDTH - total_grid_width) // 2
        start_y = top_margin + (available_height - total_grid_height) // 2


        # --- 创建卡牌 ---
        # 1. 获取主题下的所有动物图片名称
        theme_img_dir = os.path.join(IMG_DIR, theme)
        available_animals = []
        try:
             for f in os.listdir(theme_img_dir):
                 if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                     available_animals.append(os.path.splitext(f)[0])
        except FileNotFoundError:
            print(f"错误: 找不到主题图片目录: {theme_img_dir}")
            # 可以添加一个错误状态或退出游戏
            self.is_running = False # 示例：直接退出
            return
        except Exception as e:
            print(f"读取主题图片时出错: {e}")
            self.is_running = False
            return


        if len(available_animals) < self.total_pairs:
            print(f"错误: 主题 '{theme}' 的动物图片不足 ({len(available_animals)}), 需要 {self.total_pairs} 种。")
            self.is_running = False # 无法进行游戏
            return

        # 2. 选择需要的动物并创建配对列表
        selected_animals = random.sample(available_animals, self.total_pairs)
        card_animals = selected_animals * 2 # 创建配对
        random.shuffle(card_animals) # 打乱顺序

        # 3. 创建 Card 对象并放置到网格位置
        card_index = 0
        for row in range(grid_rows):
            for col in range(grid_cols):
                if card_index < len(card_animals):
                    animal_name = card_animals[card_index]
                    card = Card(animal_name, theme, card_size)
                    # 计算位置
                    x = start_x + col * (card_size[0] + CARD_PADDING)
                    y = start_y + row * (card_size[1] + CARD_PADDING)
                    card.rect.topleft = (x, y)
                    self.cards.add(card)
                    card_index += 1

        self.game_state = "playing"
        self.start_time = time.time() # 开始计时
        self.mismatch_timer = 0
        self.show_name_timer = 0
        self.animal_name_to_show = ""


    def run(self):
        """主游戏循环"""
        while self.is_running:
            self.dt = self.clock.tick(FPS) / 1000.0 # 每帧的时间（秒）
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """处理事件（输入）"""
        global achievement_to_show # 允许修改全局变量

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                if self.game_state in ["level_complete", "game_over", "all_levels_complete"]:
                     if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                         if self.game_state == "level_complete":
                             self.setup_level(self.current_level_index + 1) # 进入下一关
                         elif self.game_state == "all_levels_complete":
                             self.game_state = "menu" # 返回菜单
                         else: # game_over
                             self.game_state = "menu" # 返回菜单
                elif self.game_state == "menu":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.setup_level(0) # 开始第一关

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_state == "playing" and self.mismatch_timer <= 0: # 只有在非延迟状态下才能点击
                    pos = pygame.mouse.get_pos()
                    # 点击卡牌
                    for card in self.cards:
                        if not card.is_matched and not card.is_face_up and card.handle_click(pos):
                            if len(self.flipped_cards) < 2:
                                card.flip()
                                self.flipped_cards.append(card)
                                if len(self.flipped_cards) == 2:
                                    self.attempts += 1 # 翻开第二张时算一次尝试
                            break # 一次点击只翻一张牌
                elif self.game_state == "menu":
                     # 可以添加按钮点击逻辑
                     # start_button_rect = pygame.Rect(...)
                     # if start_button_rect.collidepoint(event.pos):
                     #     self.setup_level(0)
                     pass # 简单实现，按回车/空格开始

                elif self.game_state in ["level_complete", "game_over", "all_levels_complete"]:
                     # 可以添加按钮点击逻辑
                     # next_level_button_rect = pygame.Rect(...)
                     # if next_level_button_rect.collidepoint(event.pos):
                     #      if self.game_state == "level_complete": self.setup_level(...)
                     #      else: self.game_state = "menu"
                     pass # 简单实现，按回车/空格继续


    def check_matches(self):
        """检查翻开的两张牌是否匹配"""
        if len(self.flipped_cards) == 2:
            card1, card2 = self.flipped_cards

            if card1.animal_name == card2.animal_name:
                # --- 匹配成功 ---
                card1.is_matched = True
                card2.is_matched = True
                self.matched_pairs += 1
                if self.match_sound:
                    self.match_sound.play()

                # 播放动物叫声
                #if card1.animal_name in self.animal_sounds:
                #    self.animal_sounds[card1.animal_name].play()

                # 显示动物名称
                self.animal_name_to_show = card1.animal_name.capitalize()
                # 计算显示位置 (两张卡牌中间)
                center_x = (card1.rect.centerx + card2.rect.centerx) // 2
                center_y = (card1.rect.centery + card2.rect.centery) // 2
                self.animal_name_pos = (center_x, center_y)
                self.show_name_timer = SHOW_NAME_DURATION

                self.flipped_cards = [] # 清空已翻开列表

                # 检查关卡是否完成
                if self.matched_pairs == self.total_pairs:
                    self.game_state = "level_complete"
                    if self.win_sound:
                        self.win_sound.play()
                    self.check_achievements(level_won=True)

            else:
                # --- 匹配失败 ---
                self.mistakes_current_level += 1 # 记录错误
                self.mismatch_timer = MISMATCH_DELAY # 设置延迟计时器

            # 不论成功失败，都要等一下（或者只在失败时等）
            # self.mismatch_timer = MISMATCH_DELAY # 移到失败逻辑里


    def update(self):
        """更新游戏状态"""
        global show_achievement_timer, achievement_to_show # 允许修改全局变量

        current_time = time.time()

        # 更新成就显示计时器
        if self.show_achievement_timer > 0:
            self.show_achievement_timer -= self.dt
            if self.show_achievement_timer <= 0:
                achievement_to_show = None # 时间到了，隐藏成就

        if self.game_state == "playing":
            # 更新卡牌（如果实现了动画）
            self.cards.update(self.dt)

            # 更新计时器
            self.elapsed_time = current_time - self.start_time

            # 检查时间限制
            if self.level_time_limit > 0 and self.elapsed_time > self.level_time_limit:
                 self.game_state = "game_over" # 时间到，游戏结束
                 # 可以播放失败音效
                 return # 停止后续更新

            # 更新显示动物名称的计时器
            if self.show_name_timer > 0:
                self.show_name_timer -= self.dt
                if self.show_name_timer <= 0:
                    self.animal_name_to_show = "" # 时间到，隐藏名称

            # 更新错误匹配的延迟计时器
            if self.mismatch_timer > 0:
                self.mismatch_timer -= self.dt
                if self.mismatch_timer <= 0:
                    # 延迟结束，翻回不匹配的牌
                    for card in self.flipped_cards:
                        card.flip()
                    self.flipped_cards = [] # 清空
            else:
                # 只有在非延迟状态下才检查匹配
                self.check_matches()

    def check_achievements(self, level_won=False):
        """检查并解锁成就"""
        global achievement_to_show, show_achievement_timer # 允许修改全局变量

        newly_unlocked = []

        # 关卡完成成就
        if level_won:
            level_id = LEVELS[self.current_level_index]["id"]
            # 成就1: 完成第一关
            if level_id == 1 and not achievements["level_1_complete"]["unlocked"]:
                achievements["level_1_complete"]["unlocked"] = True
                newly_unlocked.append(achievements["level_1_complete"])

            # 成就2: 快速完成第二关 (假设时间限制90秒，60秒内算快)
            if level_id == 2 and self.elapsed_time <= 60 and not achievements["level_2_fast"]["unlocked"]:
                 achievements["level_2_fast"]["unlocked"] = True
                 newly_unlocked.append(achievements["level_2_fast"])

            # 成就3: 完美匹配 (当前关卡无错误)
            if self.mistakes_current_level == 0 and not achievements["perfect_match"]["unlocked"]:
                achievements["perfect_match"]["unlocked"] = True
                newly_unlocked.append(achievements["perfect_match"])


        # 如果有新解锁的成就，准备显示第一个
        if newly_unlocked:
            achievement_to_show = newly_unlocked[0] # 只显示第一个新解锁的
            show_achievement_timer = 3.0 # 显示3秒钟
            # 可以加个音效
            print(f"成就解锁: {achievement_to_show['name']}") # 控制台提示


    def draw_menu(self):
        """绘制主菜单界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(BLUE)

        draw_text(self.screen, "动物记忆匹配", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        draw_text(self.screen, "按 Enter 或 空格 开始游戏", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        draw_text(self.screen, "按 ESC 退出", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, GRAY, center=True)

        # 显示已解锁成就 (简单列表)
        unlocked_count = sum(1 for ach in achievements.values() if ach["unlocked"])
        draw_text(self.screen, f"已解锁成就: {unlocked_count} / {len(achievements)}", 18, 10, SCREEN_HEIGHT - 30, WHITE)


    def draw_playing(self):
        """绘制游戏进行中界面"""
        # 绘制背景
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(BLACK)

        # 绘制卡牌
        self.cards.draw(self.screen)

        # 绘制顶部信息
        # -- 计时器
        remaining_time = self.level_time_limit - int(self.elapsed_time) if self.level_time_limit > 0 else int(self.elapsed_time)
        timer_text = f"剩余时间: {remaining_time}s" if self.level_time_limit > 0 else f"用时: {int(self.elapsed_time)}s"
        timer_color = RED if self.level_time_limit > 0 and remaining_time < 10 else WHITE
        draw_text(self.screen, timer_text, 30, SCREEN_WIDTH - 250, 10, timer_color)
        # -- 关卡信息
        level_id = LEVELS[self.current_level_index]["id"]
        theme = LEVELS[self.current_level_index]["theme"].capitalize()
        draw_text(self.screen, f"关卡 {level_id} ({theme})", 30, 10, 10, WHITE)
        # -- 匹配进度
        draw_text(self.screen, f"已匹配: {self.matched_pairs} / {self.total_pairs}", 24, 10, 50, WHITE)
        # -- 尝试次数
        draw_text(self.screen, f"尝试: {self.attempts}", 24, SCREEN_WIDTH - 150, 50, WHITE)

        # 绘制匹配成功时显示的动物名称
        if self.animal_name_to_show and self.show_name_timer > 0:
            draw_text(self.screen, self.animal_name_to_show, 40, self.animal_name_pos[0], self.animal_name_pos[1] - 30, GREEN, center=True)

        # 绘制成就解锁提示
        if achievement_to_show and show_achievement_timer > 0:
            self.draw_achievement_popup(achievement_to_show)


    def draw_level_complete(self):
        """绘制关卡完成界面"""
        self.screen.fill(GREEN)
        level_id = LEVELS[self.current_level_index]["id"]
        draw_text(self.screen, f"关卡 {level_id} 完成!", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        draw_text(self.screen, f"用时: {int(self.elapsed_time)} 秒", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        draw_text(self.screen, f"尝试次数: {self.attempts}", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, WHITE, center=True)
        draw_text(self.screen, f"错误次数: {self.mistakes_current_level}", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80, WHITE if self.mistakes_current_level == 0 else RED, center=True)

        if self.current_level_index + 1 < len(LEVELS):
            draw_text(self.screen, "按 Enter 或 空格 进入下一关", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)
        else:
             draw_text(self.screen, "所有关卡已完成!", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4 - 40, WHITE, center=True)
             draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)


    def draw_game_over(self):
        """绘制游戏结束界面"""
        self.screen.fill(RED)
        draw_text(self.screen, "游戏结束", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        if self.level_time_limit > 0 and self.elapsed_time > self.level_time_limit:
            draw_text(self.screen, "时间到!", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        # else: # 如果有其他失败条件可以在这里添加
        #     draw_text(self.screen, "失败原因...", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)

        draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)

    def draw_all_levels_complete(self):
        """绘制所有关卡完成界面"""
        self.screen.fill(BLUE)
        draw_text(self.screen, "恭喜!", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, WHITE, center=True)
        draw_text(self.screen, "你已完成所有关卡!", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE, center=True)
        draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, WHITE, center=True)

    def draw_achievement_popup(self, achievement):
        """绘制成就解锁的弹出提示"""
        popup_width = 300
        popup_height = 80
        popup_x = SCREEN_WIDTH - popup_width - 20
        popup_y = 100

        # 绘制背景
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, GRAY, popup_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, popup_rect, width=2, border_radius=10)

        # 绘制文字
        draw_text(self.screen, "成就解锁!", 24, popup_x + 150, popup_y + 20, BLACK, center=True)
        draw_text(self.screen, achievement['name'], 18, popup_x + 150, popup_y + 45, BLACK, center=True)
        draw_text(self.screen, achievement['desc'], 14, popup_x + 150, popup_y + 65, BLACK, center=True)


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
        else: # 未知状态，可以显示错误或默认界面
             self.screen.fill(BLACK)
             draw_text(self.screen, f"未知游戏状态: {self.game_state}", 30, 100, 100, RED)

        # 确保最后刷新屏幕
        pygame.display.flip()


# --- 游戏入口 ---
if __name__ == '__main__':
    # 在启动游戏前检查资源目录是否存在
    if not os.path.isdir(ASSETS_DIR):
        print(f"错误: 资源目录 'assets' 未找到或不是一个目录。请确保它在脚本旁边。")
        # 可以尝试创建目录，或者直接退出
        try:
             os.makedirs(os.path.join(IMG_DIR, 'forest'))
             os.makedirs(os.path.join(IMG_DIR, 'ocean'))
             os.makedirs(os.path.join(SND_DIR, 'forest'))
             os.makedirs(os.path.join(SND_DIR, 'ocean'))
             print("已创建基本的 'assets' 目录结构，请填入图片和声音文件。")
             # 你可能需要提供一些默认资源或者提示用户放入资源
             # 这里为了能运行，先不退出，但会缺少资源
        except Exception as e:
             print(f"尝试创建目录失败: {e}")
             sys.exit() # 无法继续，退出

    game = Game()
    game.run()