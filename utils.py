import pygame
import os
import config

# --- 工具函数 ---
def load_image(filepath, size=None, use_colorkey=False, colorkey_color=config.BLACK):
    """加载图片并可选地调整大小和设置透明色"""
    try:
        # 优先在 IMG_DIR 中查找相对路径
        if not os.path.isabs(filepath) and not os.path.exists(filepath):
            path = os.path.join(config.IMG_DIR, filepath)
        else:
            path = filepath # 如果是绝对路径或已存在，直接使用

        if not os.path.exists(path):
            raise FileNotFoundError(f"图片文件未找到: {path}")

        image = pygame.image.load(path).convert()
    except (pygame.error, FileNotFoundError) as e:
        print(f"无法加载图片: {filepath} - {e}")
        # 创建一个占位符图像
        image = pygame.Surface(size if size else [100, 100])
        image.fill(config.GRAY)
        pygame.draw.rect(image, config.RED, image.get_rect(), 2)
        return image # 直接返回占位符

    if size:
        image = pygame.transform.scale(image, size)
    if use_colorkey:
        image.set_colorkey(colorkey_color)
    else:
        image = image.convert_alpha() # 默认使用 alpha 通道
    return image

def load_sound(filename):
    """加载声音文件"""
    path = os.path.join(config.SND_DIR, filename)
    if not os.path.exists(path):
        print(f"警告: 声音文件未找到: {path}")
        return None
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except pygame.error as e:
        print(f"无法加载声音: {path} - {e}")
        return None

def draw_text(surface, text, size, x, y, color=config.BLACK, font_name=config.FONT_NAME, center=False):
    """在指定位置绘制文本"""
    try:
        # 检查字体文件是否存在，如果不存在或不是文件，则使用系统字体
        if font_name and os.path.isfile(font_name):
            font = pygame.font.Font(font_name, size)
        else:
            # 尝试使用系统字体，如果 FONT_NAME 不是有效系统字体名，会回退
            font = pygame.font.SysFont(font_name or 'arial', size)
    except Exception as e:
        print(f"加载字体 '{font_name}' 失败: {e}, 使用默认 'arial'")
        font = pygame.font.SysFont('arial', size) # 最终回退

    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
    return text_rect
