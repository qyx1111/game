import pygame
import config
import utils

# --- 卡牌类 ---
class Card(pygame.sprite.Sprite):
    def __init__(self, item_name, theme, card_size, image_path):
        super().__init__()
        self.item_name = item_name
        self.theme = theme
        self.card_size = card_size
        self.image_path = image_path # 存储原始相对路径或绝对路径
        self.is_face_up = False
        self.is_matched = False
        self._load_images()
        self.image = self.image_back # 初始显示背面
        self.rect = self.image.get_rect()
        self.flip_sound = utils.load_sound("flip.wav")
        self.is_flipping = False # 动画相关，当前版本未使用
        self.flip_progress = 0 # 动画相关，当前版本未使用

    def _load_images(self):
        """加载卡牌正面和背面图片"""
        # 加载卡背
        try:
            # 假设 card_back.png 在 IMG_DIR 根目录
            self.image_back_orig = utils.load_image("card_back.png")
            self.image_back = pygame.transform.scale(self.image_back_orig, self.card_size)
        except Exception as e:
            print(f"无法加载卡背图片: {e}")
            self.image_back = pygame.Surface(self.card_size)
            self.image_back.fill(config.BLUE)
            pygame.draw.rect(self.image_back, config.WHITE, self.image_back.get_rect(), 2)

        # 加载卡面 (节气图片)
        try:
            # image_path 已经是完整路径或相对于 IMG_DIR 的路径
            self.image_front_orig = utils.load_image(self.image_path)
            self.image_front = pygame.transform.scale(self.image_front_orig, self.card_size)
        except Exception as e:
            print(f"无法加载节气图片 {self.image_path}: {e}")
            self.image_front = pygame.Surface(self.card_size)
            self.image_front.fill(config.GREEN)
            utils.draw_text(self.image_front, self.item_name, 16, self.card_size[0]//2, self.card_size[1]//2, config.BLACK, center=True)

    def flip(self, instant=False,flag = True):
        """翻转卡牌"""
        if self.is_matched or self.is_flipping:
            return

        if self.flip_sound and flag:
            self.flip_sound.play()

        self.is_face_up = not self.is_face_up
        if self.is_face_up:
            self.image = self.image_front
        else:
            self.image = self.image_back

    def update(self, dt):
        """更新卡牌状态（用于动画，当前未使用）"""
        pass # 可以在这里实现翻转动画逻辑

    def draw(self, surface):
        """绘制卡牌"""
        surface.blit(self.image, self.rect)

    def handle_click(self, pos):
        """检查点击是否在卡牌上"""
        return self.rect.collidepoint(pos)
