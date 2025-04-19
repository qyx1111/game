import os

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
BASE_DIR = os.path.dirname(__file__) # 获取当前文件所在目录
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMG_DIR = os.path.join(ASSETS_DIR, 'images')
SND_DIR = os.path.join(ASSETS_DIR, 'sounds')
FONT_NAME = "SimHei" # 使用黑体或其他支持中文的字体

# 成就 (更新为季节主题)
# 注意：成就状态将在游戏运行时被修改，这里是初始状态
achievements = {
    "complete_spring": {"name": "春之初识", "unlocked": False, "desc": "完成春季关卡"},
    "fast_summer": {"name": "夏日疾风", "unlocked": False, "desc": "在45秒内完成夏季关卡"},
    "perfect_autumn": {"name": "秋之零误", "unlocked": False, "desc": "在秋季关卡中没有错误匹配"},
    "complete_all": {"name": "四季轮回", "unlocked": False, "desc": "完成所有季节关卡"}
}

# --- 关卡定义 (恢复为 3x4 网格) ---
LEVELS = [
    {"id": 1, "grid": (3, 4), "theme": "spring", "time_limit": 30}, # 3行4列 = 12张牌 = 6对
    {"id": 2, "grid": (3, 4), "theme": "summer", "time_limit": 30},
    {"id": 3, "grid": (3, 4), "theme": "autumn", "time_limit": 30},
    {"id": 4, "grid": (3, 4), "theme": "winter", "time_limit": 30},
]
# 季节名称映射 (用于显示)
THEME_NAMES = {
    "spring": "春",
    "summer": "夏",
    "autumn": "秋",
    "winter": "冬"
}
