import pygame
import random
import os
import sys
import time
import config
import utils
from card import Card # 从 card 模块导入 Card 类

# --- 游戏主类 ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("二十四节气记忆匹配")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.game_state = "menu" # menu, playing, level_complete, game_over, all_levels_complete
        self.dt = 0 # Delta time

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

        # 声音
        self.match_sound = utils.load_sound("match.wav")
        self.win_sound = utils.load_sound("win.wav")
        self.bgm = utils.load_sound("bgm.wav")
        if self.bgm:
            self.bgm.play(loops=-1) #loops=-1 表示循环播放 , loops默认值为0，只播放一次

        # 背景图
        try:
            self.background_img = utils.load_image("background.png", (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        except Exception as e:
            print(f"加载背景图片失败: {e}")
            self.background_img = None

        # 成就相关状态移入 Game 类
        self.show_achievement_timer = 0
        self.achievement_to_show = None
        self.level_complete_image = None # 用于存储关卡完成图片
        self.newly_unlocked_achievements = [] # 存储本次关卡解锁的成就

    def load_level_assets(self, theme):
        """为当前关卡主题加载所需资源，包括关卡完成图片"""
        # 尝试加载关卡完成图片
        complete_image_path = os.path.join(config.IMG_DIR, f"{theme}_complete.png")
        try:
            # 尝试加载并适应屏幕大小，保持比例
            img = utils.load_image(complete_image_path) # 使用 utils 加载
            img_rect = img.get_rect()
            # 限制高度为屏幕的60%，给文字留空间，同时考虑宽度限制
            scale = min(config.SCREEN_WIDTH / img_rect.width, config.SCREEN_HEIGHT * 0.5 / img_rect.height)
            new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
            self.level_complete_image = pygame.transform.smoothscale(img, new_size)
            print(f"已加载关卡完成图片: {complete_image_path}")
        except Exception as e:
            print(f"警告: 未找到或无法加载关卡完成图片: {complete_image_path} - {e}")
            self.level_complete_image = None # 确保未加载时为 None

    def setup_level(self, level_index):
        """设置新关卡"""
        if level_index >= len(config.LEVELS):
            self.check_achievements(all_levels_completed=True) # 检查是否解锁最终成就
            self.game_state = "all_levels_complete"
            return

        level_data = config.LEVELS[level_index]
        self.current_level_index = level_index
        grid_rows, grid_cols = level_data["grid"]
        theme = level_data["theme"]
        self.level_time_limit = level_data.get("time_limit", 0)

        self.load_level_assets(theme) # 加载资源，包括完成图片

        # 重置关卡状态
        self.cards.empty()
        self.flipped_cards = []
        self.matched_pairs = 0
        self.total_pairs = (grid_rows * grid_cols) // 2
        self.attempts = 0
        self.mistakes_current_level = 0
        self.newly_unlocked_achievements = [] # 重置本次解锁成就列表

        # --- 计算卡牌尺寸和布局 ---
        top_margin = 40 # 顶部留给UI的空间
        # 可用空间减去所有内边距和外边距
        available_width = config.SCREEN_WIDTH - (grid_cols + 1) * config.CARD_PADDING
        available_height = config.SCREEN_HEIGHT - top_margin - (grid_rows + 1) * config.CARD_PADDING
        # 计算理想的卡牌尺寸
        card_width = available_width // grid_cols
        card_height = available_height // grid_rows
        # 取较小值确保卡牌是正方形或适应较窄的维度，并防止变形
        card_size = (min(card_width, card_height), min(card_width, card_height))

        # 重新计算网格总尺寸和起始位置以居中
        total_grid_width = grid_cols * card_size[0] + (grid_cols - 1) * config.CARD_PADDING
        total_grid_height = grid_rows * card_size[1] + (grid_rows - 1) * config.CARD_PADDING
        start_x = (config.SCREEN_WIDTH - total_grid_width) // 2
        start_y = top_margin + (available_height - total_grid_height) // 2 # 在可用垂直空间内居中

        # --- 加载和准备卡牌数据 ---
        theme_img_dir = os.path.join(config.IMG_DIR, theme)
        available_solar_terms = []
        try:
            # 确保主题目录存在
            if not os.path.isdir(theme_img_dir):
                 raise FileNotFoundError(f"主题图片目录未找到: {theme_img_dir}")

            for item in os.listdir(theme_img_dir):
                item_path = os.path.join(theme_img_dir, item)
                # 确保是目录（代表一个节气）
                if os.path.isdir(item_path):
                    # 检查目录内是否有图片文件
                    has_images = False
                    for f in os.listdir(item_path):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                            has_images = True
                            break
                    if has_images:
                        available_solar_terms.append(item) # item 是节气名称 (目录名)
                    else:
                        print(f"警告: 节气目录 '{item_path}' 为空或不包含图片，已跳过。")

        except FileNotFoundError as e:
            print(f"错误: {e}")
            self.is_running = False # 无法继续游戏
            return
        except Exception as e:
            print(f"读取主题 '{theme}' 的子目录时出错: {e}")
            self.is_running = False
            return

        # 检查是否有足够的节气用于当前关卡
        if len(available_solar_terms) < self.total_pairs:
            print(f"错误: 主题 '{theme}' 的有效节气目录不足 ({len(available_solar_terms)}个), 需要 {self.total_pairs} 个。")
            print(f"请确保在 '{theme_img_dir}' 下有足够的包含图片的节气子目录。")
            self.is_running = False
            return

        # 从可用的节气中随机选择所需数量
        selected_solar_terms = random.sample(available_solar_terms, self.total_pairs)

        # 为每个选中的节气选择一张图片，并创建卡牌数据对
        card_data = []
        for term_name in selected_solar_terms:
            term_dir = os.path.join(theme_img_dir, term_name)
            try:
                images_in_term = [f for f in os.listdir(term_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if not images_in_term:
                    # 这个检查理论上在前面已经做过，但为了安全再加一层
                    print(f"错误: 节气目录 '{term_dir}' 中找不到图片文件（这不应该发生）。")
                    self.is_running = False
                    return
                # 随机选择该节气下的一张图片
                chosen_image_name = random.choice(images_in_term)
                # 构造图片的完整路径
                chosen_image_path = os.path.join(term_dir, chosen_image_name)
                # 添加节气名和图片路径到列表
                card_data.append((term_name, chosen_image_path))
            except Exception as e:
                print(f"读取节气 '{term_name}' 的图片时出错: {e}")
                self.is_running = False
                return

        # 创建配对的卡牌数据并打乱顺序
        paired_card_data = card_data * 2
        random.shuffle(paired_card_data)

        # --- 创建并放置卡牌精灵 ---
        data_index = 0
        for row in range(grid_rows):
            for col in range(grid_cols):
                if data_index < len(paired_card_data):
                    item_name, image_path = paired_card_data[data_index]
                    # 创建 Card 实例
                    card = Card(item_name, theme, card_size, image_path)
                    # 计算卡牌位置
                    x = start_x + col * (card_size[0] + config.CARD_PADDING)
                    y = start_y + row * (card_size[1] + config.CARD_PADDING)
                    card.rect.topleft = (x, y)
                    self.cards.add(card) # 添加到精灵组
                    data_index += 1

        # 设置游戏状态和计时器
        self.game_state = "playing"
        self.start_time = time.time()
        self.mismatch_timer = 0
        self.show_name_timer = 0
        self.item_name_to_show = ""

    def run(self):
        """主游戏循环"""
        while self.is_running:
            self.dt = self.clock.tick(config.FPS) / 1000.0 # 使用 config.FPS
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        # sys.exit() # 通常由 main.py 控制退出

    def handle_events(self):
        """处理事件（输入）"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # 在游戏中按 ESC 返回菜单，在菜单按 ESC 退出
                    if self.game_state != "menu":
                        self.game_state = "menu"
                        if self.bgm: self.bgm.play(loops=-1) # 确保背景音乐播放
                    else:
                        self.is_running = False

                # 处理不同状态下的 Enter/Space 键
                if self.game_state in ["level_complete", "game_over", "all_levels_complete"]:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.game_state == "level_complete":
                            self.setup_level(self.current_level_index + 1)
                        elif self.game_state == "all_levels_complete":
                             # 完成所有关卡后返回菜单
                            self.game_state = "menu"
                        else: # game_over
                            self.game_state = "menu"
                elif self.game_state == "menu":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.setup_level(0) # 开始第一关

            # 处理鼠标点击
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 只在 playing 状态且没有卡牌正在等待翻回时处理点击
                if self.game_state == "playing" and self.mismatch_timer <= 0:
                    pos = pygame.mouse.get_pos()
                    # 检查点击了哪个卡牌
                    for card in self.cards:
                        # 只能点击未匹配、未翻开的卡牌
                        if not card.is_matched and not card.is_face_up and card.handle_click(pos):
                            # 最多只能有两张卡牌被翻开
                            if len(self.flipped_cards) < 2:
                                card.flip()
                                self.flipped_cards.append(card)
                                # 如果翻开了第二张，增加尝试次数
                                if len(self.flipped_cards) == 2:
                                    self.attempts += 1
                            break # 点击到一个卡牌后就停止检查

    def check_matches(self):
        """检查翻开的两张牌是否匹配"""
        if len(self.flipped_cards) == 2:
            card1, card2 = self.flipped_cards

            if card1.item_name == card2.item_name: # 匹配成功
                card1.is_matched = True
                card2.is_matched = True
                self.matched_pairs += 1
                if self.match_sound:
                    self.match_sound.play()

                # 设置显示节气名称
                self.item_name_to_show = card1.item_name
                # 计算显示位置 (两张卡牌中间靠上的位置)
                center_x = (card1.rect.centerx + card2.rect.centerx) // 2
                center_y = min(card1.rect.top, card2.rect.top) - 20 # 在卡牌上方一点
                self.item_name_pos = (center_x, center_y)
                self.show_name_timer = config.SHOW_NAME_DURATION

                self.flipped_cards = [] # 清空已翻开列表

                # 检查是否完成关卡
                if self.matched_pairs == self.total_pairs:
                    self.game_state = "level_complete"
                    if self.win_sound:
                        self.win_sound.play()
                    self.check_achievements(level_won=True) # 检查关卡胜利相关的成就

            else: # 匹配失败
                self.mistakes_current_level += 1
                # 启动计时器，稍后将卡牌翻回
                self.mismatch_timer = config.MISMATCH_DELAY

    def update(self):
        """更新游戏状态"""
        current_time = time.time()

        # 更新成就弹窗计时器
        if self.show_achievement_timer > 0:
            self.show_achievement_timer -= self.dt
            if self.show_achievement_timer <= 0:
                self.achievement_to_show = None # 时间到了，隐藏弹窗

        # 只在 playing 状态下更新游戏逻辑
        if self.game_state == "playing":
            self.cards.update(self.dt) # 更新所有卡牌（为未来动画准备）

            # 更新已用时间
            self.elapsed_time = current_time - self.start_time

            # 检查时间限制
            if self.level_time_limit > 0 and self.elapsed_time > self.level_time_limit:
                self.game_state = "game_over"
                return # 游戏结束，不再继续更新

            # 更新节气名称显示计时器
            if self.show_name_timer > 0:
                self.show_name_timer -= self.dt
                if self.show_name_timer <= 0:
                    self.item_name_to_show = "" # 时间到了，隐藏名称

            # 更新错误匹配延迟计时器
            if self.mismatch_timer > 0:
                self.mismatch_timer -= self.dt
                # 延迟结束，将不匹配的卡牌翻回去
                if self.mismatch_timer <= 0:
                    for card in self.flipped_cards:
                        if not card.is_matched: # 确保不会翻回已匹配的牌（理论上不会发生）
                            card.flip( flag = False) # 翻回背面
                    self.flipped_cards = [] # 清空已翻开列表
            else:
                # 如果没有在等待翻回，检查是否有两张牌需要匹配
                self.check_matches()

    def check_achievements(self, level_won=False, all_levels_completed=False):
        """检查并解锁成就"""
        # 注意：现在直接修改 config.achievements 字典
        newly_unlocked_for_popup = None # 用于决定弹窗显示哪个成就

        if level_won:
            level_id = config.LEVELS[self.current_level_index]["id"]
            theme = config.LEVELS[self.current_level_index]["theme"]

            # 春之初识
            if theme == "spring" and not config.achievements["complete_spring"]["unlocked"]:
                config.achievements["complete_spring"]["unlocked"] = True
                self.newly_unlocked_achievements.append(config.achievements["complete_spring"])
                if not newly_unlocked_for_popup: newly_unlocked_for_popup = config.achievements["complete_spring"]

            # 夏日疾风
            if theme == "summer" and self.elapsed_time <= 45 and not config.achievements["fast_summer"]["unlocked"]:
                config.achievements["fast_summer"]["unlocked"] = True
                self.newly_unlocked_achievements.append(config.achievements["fast_summer"])
                if not newly_unlocked_for_popup: newly_unlocked_for_popup = config.achievements["fast_summer"]

            # 秋之零误
            if theme == "autumn" and self.mistakes_current_level == 0 and not config.achievements["perfect_autumn"]["unlocked"]:
                config.achievements["perfect_autumn"]["unlocked"] = True
                self.newly_unlocked_achievements.append(config.achievements["perfect_autumn"])
                if not newly_unlocked_for_popup: newly_unlocked_for_popup = config.achievements["perfect_autumn"]

        # 四季轮回 (在 setup_level 检测到所有关卡完成时，或在此处检测)
        if all_levels_completed and not config.achievements["complete_all"]["unlocked"]:
            config.achievements["complete_all"]["unlocked"] = True
            # 注意：四季轮回的解锁信息通常在 all_levels_complete 屏幕显示，
            # 但如果希望它也弹窗，可以在这里设置 newly_unlocked_for_popup
            # self.newly_unlocked_achievements.append(config.achievements["complete_all"]) # 可以选择是否加入列表
            # if not newly_unlocked_for_popup: newly_unlocked_for_popup = config.achievements["complete_all"]
            print("成就解锁: 四季轮回") # 可以在控制台打印确认

        # 如果有关卡胜利时新解锁的成就，设置弹窗
        if newly_unlocked_for_popup:
            self.achievement_to_show = newly_unlocked_for_popup
            self.show_achievement_timer = 3.0 # 显示 3 秒
            print(f"成就解锁 (弹窗): {self.achievement_to_show['name']}")

    # --- 绘制函数 ---
    def draw_menu(self):
        """绘制主菜单界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(config.BLUE) # 使用 config 中的颜色

        utils.draw_text(self.screen, "喔的朋友", 64, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4, config.BLACK, center=True)
        utils.draw_text(self.screen, "按 Enter 或 空格 开始游戏", 30, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2, config.WHITE, center=True)
        utils.draw_text(self.screen, "按 ESC 返回菜单或退出", 22, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT * 3 // 4, config.GRAY, center=True)

        # 显示已解锁成就数量
        unlocked_count = sum(1 for ach in config.achievements.values() if ach["unlocked"])
        utils.draw_text(self.screen, f"已解锁成就: {unlocked_count} / {len(config.achievements)}", 18, 10, config.SCREEN_HEIGHT - 30, config.WHITE)

    def draw_playing(self):
        """绘制游戏进行中界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(config.BLUE) # 使用 config 中的颜色
        self.cards.draw(self.screen) # 绘制所有卡牌

        # 显示计时器
        if self.level_time_limit > 0:
            remaining_time = self.level_time_limit - int(self.elapsed_time)
            timer_text = f"剩余时间: {remaining_time}s"
            timer_color = config.RED if remaining_time < 10 else config.WHITE
        else:
            timer_text = f"用时: {int(self.elapsed_time)}s"
            timer_color = config.WHITE
        utils.draw_text(self.screen, timer_text, 30, config.SCREEN_WIDTH - 250, 10, timer_color)

        # 显示关卡信息
        level_theme = config.LEVELS[self.current_level_index]["theme"]
        level_name = config.THEME_NAMES.get(level_theme, level_theme.capitalize())
        level_id = config.LEVELS[self.current_level_index]["id"]
        utils.draw_text(self.screen, f"关卡 {level_id}: {level_name}", 30, 45, 10, config.WHITE)

        # 显示统计信息
        utils.draw_text(self.screen, f"已匹配: {self.matched_pairs} / {self.total_pairs}", 24, 45, 50, config.WHITE)
        utils.draw_text(self.screen, f"尝试: {self.attempts}", 24, config.SCREEN_WIDTH - 150, 50, config.WHITE)

        # 显示匹配成功的节气名称
        if self.item_name_to_show and self.show_name_timer > 0:
            utils.draw_text(self.screen, self.item_name_to_show, 36, self.item_name_pos[0], self.item_name_pos[1], config.GREEN, center=True)

        # 显示成就解锁弹窗
        if self.achievement_to_show and self.show_achievement_timer > 0:
            self.draw_achievement_popup(self.achievement_to_show)

    def draw_level_complete(self):
        """绘制关卡完成界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(config.BLUE) # 使用 config 中的颜色

        img_y_offset = 80 # 图片距离顶部的偏移
        # 绘制关卡完成图片（如果已加载）
        if self.level_complete_image:
            img_rect = self.level_complete_image.get_rect(center=(config.SCREEN_WIDTH // 2, img_y_offset + self.level_complete_image.get_height() // 2))
            self.screen.blit(self.level_complete_image, img_rect)
            text_start_y = img_rect.bottom + 30 # 文字在图片下方开始
        else:
            text_start_y = config.SCREEN_HEIGHT // 4 # 如果没有图片，文字从较高位置开始

        # 显示关卡完成信息
        level_theme = config.LEVELS[self.current_level_index]["theme"]
        level_name = config.THEME_NAMES.get(level_theme, level_theme.capitalize())
        level_id = config.LEVELS[self.current_level_index]["id"]
        utils.draw_text(self.screen, f"关卡 {level_id} ({level_name}) 完成!", 50, config.SCREEN_WIDTH // 2, text_start_y, config.WHITE, center=True)

        # 显示统计数据
        stats_y = text_start_y + 60
        utils.draw_text(self.screen, f"用时: {int(self.elapsed_time)} 秒", 30, config.SCREEN_WIDTH // 2, stats_y, config.WHITE, center=True)
        utils.draw_text(self.screen, f"尝试次数: {self.attempts}", 30, config.SCREEN_WIDTH // 2, stats_y + 40, config.WHITE, center=True)
        mistake_color = config.WHITE if self.mistakes_current_level == 0 else config.RED
        utils.draw_text(self.screen, f"错误次数: {self.mistakes_current_level}", 30, config.SCREEN_WIDTH // 2, stats_y + 80, mistake_color, center=True)

        # 显示本次解锁的成就
        achievement_y = stats_y + 130
        if self.newly_unlocked_achievements:
            utils.draw_text(self.screen, "本次解锁成就:", 28, config.SCREEN_WIDTH // 2, achievement_y, config.WHITE, center=True)
            achievement_y += 40
            for ach in self.newly_unlocked_achievements:
                utils.draw_text(self.screen, f"- {ach['name']}: {ach['desc']}", 24, config.SCREEN_WIDTH // 2, achievement_y, config.WHITE, center=True)
                achievement_y += 35 # 增加行间距

        # 显示进入下一关或结束的提示
        prompt_y = max(achievement_y, config.SCREEN_HEIGHT * 3 // 4) # 确保提示在屏幕下方
        if self.current_level_index + 1 < len(config.LEVELS):
            next_level_theme = config.LEVELS[self.current_level_index + 1]["theme"]
            next_level_name = config.THEME_NAMES.get(next_level_theme, next_level_theme.capitalize())
            utils.draw_text(self.screen, f"按 Enter 或 空格 进入下一关 ({next_level_name})", 30, config.SCREEN_WIDTH // 2, prompt_y, config.WHITE, center=True)
        else:
            # 检查是否刚刚解锁了“四季轮回”成就
            all_complete_ach = config.achievements["complete_all"]
            if all_complete_ach in self.newly_unlocked_achievements or all_complete_ach["unlocked"]: # 确保显示
                 # 如果四季轮回是在这个界面解锁的，或者之前已解锁，都显示一下
                utils.draw_text(self.screen, f"成就解锁: {all_complete_ach['name']} - {all_complete_ach['desc']}", 24, config.SCREEN_WIDTH // 2, achievement_y, config.GREEN, center=True)
                achievement_y += 35
                prompt_y = max(achievement_y, config.SCREEN_HEIGHT * 3 // 4) # 重新计算提示位置

            utils.draw_text(self.screen, "所有关卡完成! 按 Enter 或 空格 进入最终结算", 30, config.SCREEN_WIDTH // 2, prompt_y, config.WHITE, center=True)

    def draw_game_over(self):
        """绘制游戏结束界面"""
        self.screen.fill(config.RED) # 使用 config 中的颜色
        utils.draw_text(self.screen, "游戏结束", 64, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4, config.WHITE, center=True)
        if self.level_time_limit > 0 and self.elapsed_time > self.level_time_limit:
            utils.draw_text(self.screen, "时间到!", 40, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2, config.WHITE, center=True)
        else:
             # 如果不是因为时间结束，可以显示其他失败原因（如果未来有的话）
            utils.draw_text(self.screen, "挑战失败", 40, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2, config.WHITE, center=True)

        utils.draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT * 3 // 4, config.WHITE, center=True)

    def draw_all_levels_complete(self):
        """绘制所有关卡完成界面"""
        if self.background_img:
            self.screen.blit(self.background_img, (0,0))
        else:
            self.screen.fill(config.BLACK) # 使用 config 中的颜色
        utils.draw_text(self.screen, "恭喜!", 64, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 4, config.WHITE, center=True)
        utils.draw_text(self.screen, "你已完成所有季节的挑战!", 40, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2, config.WHITE, center=True)
        # 再次确认并显示最终成就
        if config.achievements["complete_all"]["unlocked"]:
            utils.draw_text(self.screen, f"成就解锁: {config.achievements['complete_all']['name']}", 24, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 50, config.GREEN, center=True)

        utils.draw_text(self.screen, "按 Enter 或 空格 返回主菜单", 30, config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT * 3 // 4, config.WHITE, center=True)

    def draw_achievement_popup(self, achievement):
        """绘制成就解锁的弹出提示"""
        popup_width = 300
        popup_height = 100
        popup_x = config.SCREEN_WIDTH - popup_width - 20 # 右上角
        popup_y = 80 # 距离顶部一点距离

        # 创建一个半透明背景
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        s = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA) # 支持 alpha 通道
        s.fill((200, 200, 200, 200)) # 半透明灰色背景
        self.screen.blit(s, (popup_x, popup_y))
        # 绘制边框
        pygame.draw.rect(self.screen, config.WHITE, popup_rect, width=2, border_radius=10)

        # 绘制文字
        utils.draw_text(self.screen, "成就解锁!", 24, popup_x + popup_width // 2, popup_y + 20, config.BLACK, center=True)
        utils.draw_text(self.screen, achievement['name'], 20, popup_x + popup_width // 2, popup_y + 50, config.BLACK, center=True)
        utils.draw_text(self.screen, achievement['desc'], 16, popup_x + popup_width // 2, popup_y + 75, config.BLACK, center=True)

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
        else: # 未知状态处理
            self.screen.fill(config.BLACK)
            utils.draw_text(self.screen, f"未知游戏状态: {self.game_state}", 30, 100, 100, config.RED)

        pygame.display.flip() # 更新整个屏幕显示
