import pygame
import os
import sys
import config # 导入配置
from game import Game # 从 game 模块导入 Game 类

# --- 资源和目录检查 ---
def check_assets():
    """检查必要的资源目录和文件是否存在，并在需要时创建目录或给出警告。"""
    if not os.path.isdir(config.ASSETS_DIR):
        print(f"错误: 资源目录 '{config.ASSETS_DIR}' 未找到。正在尝试创建...")
        try:
            os.makedirs(config.ASSETS_DIR)
            os.makedirs(config.IMG_DIR)
            os.makedirs(config.SND_DIR)
            print("'assets' 目录结构已创建。请添加资源文件。")
            # 第一次创建时，很可能缺少文件，直接退出让用户添加
            sys.exit()
        except Exception as e:
            print(f"创建 'assets' 目录失败: {e}")
            sys.exit()

    themes_to_check = ["spring", "summer", "autumn", "winter"]
    dirs_created = False
    required_subdirs_exist = True
    min_solar_terms_per_theme = 6 # 每个主题至少需要的节气子目录数 (对应3x4网格)

    for theme in themes_to_check:
        img_theme_dir = os.path.join(config.IMG_DIR, theme)
        snd_theme_dir = os.path.join(config.SND_DIR, theme) # 声音目录（可选）

        # 检查并创建图片主题目录
        if not os.path.isdir(img_theme_dir):
            try:
                os.makedirs(img_theme_dir)
                print(f"已创建图片目录: {img_theme_dir}")
                dirs_created = True
                required_subdirs_exist = False # 新创建的目录肯定缺少内容
            except Exception as e:
                print(f"创建目录 {img_theme_dir} 失败: {e}")
                required_subdirs_exist = False
                continue # 跳过后续检查

        # 检查图片主题目录下的节气子目录数量
        try:
            if os.path.isdir(img_theme_dir): # 确保目录存在再检查
                solar_term_dirs = [d for d in os.listdir(img_theme_dir)
                                   if os.path.isdir(os.path.join(img_theme_dir, d))]
                if len(solar_term_dirs) < min_solar_terms_per_theme:
                    print(f"警告: 主题 '{theme}' 的图片目录 '{img_theme_dir}' 下节气子目录不足 ({len(solar_term_dirs)}个)，需要至少 {min_solar_terms_per_theme} 个。")
                    required_subdirs_exist = False
                    if dirs_created or not solar_term_dirs: # 如果是新创建的或空的
                        print(f"  请在 '{img_theme_dir}' 下创建节气名称的子目录 (例如: 立春, 雨水, ...)，并在每个子目录中放入至少一张图片。")
            else:
                 # 如果目录在上面创建失败，这里会再次报告问题
                 required_subdirs_exist = False

        except FileNotFoundError:
            # 理论上不会到这里，因为上面已经检查或创建了目录
            print(f"错误: 无法访问主题图片目录: {img_theme_dir}")
            required_subdirs_exist = False
        except Exception as e:
            print(f"检查主题 '{theme}' 的子目录时出错: {e}")
            required_subdirs_exist = False

        # 检查并创建声音主题目录（可选）
        if not os.path.isdir(snd_theme_dir):
            try:
                os.makedirs(snd_theme_dir)
                print(f"已创建声音目录: {snd_theme_dir}")
            except Exception as e:
                print(f"创建目录 {snd_theme_dir} 失败: {e}")
                # 声音目录失败不阻止游戏运行

    if not required_subdirs_exist:
        print("\n错误:缺少必要的节气图片子目录或结构不完整，无法启动游戏。")
        print("请根据上面的提示创建目录和添加图片文件。")
        sys.exit()
    elif dirs_created:
        print("\n请注意:已创建所需的季节图片主目录。")
        print(f"请确保在每个季节目录下创建了至少 {min_solar_terms_per_theme} 个节气子目录，并在其中放入图片。")
        print("例如: assets/images/spring/立春/图片1.png")
        # 提示后也退出，让用户添加文件
        sys.exit()

    # 检查通用声音文件
    required_sounds = ["flip.wav", "match.wav", "win.wav", "bgm.wav"]
    missing_sounds = []
    for sound_file in required_sounds:
        if not os.path.exists(os.path.join(config.SND_DIR, sound_file)):
            missing_sounds.append(sound_file)
    if missing_sounds:
        print(f"\n警告: 缺少通用声音文件: {', '.join(missing_sounds)}。游戏仍可运行，但会缺少音效。")
        print(f"请将这些文件放入 {config.SND_DIR} 目录。")

    # 检查卡背图片
    if not os.path.exists(os.path.join(config.IMG_DIR, "card_back.png")):
        print(f"\n警告: 缺少卡牌背面图片 'card_back.png'。")
        print(f"请将该文件放入 {config.IMG_DIR} 目录。卡牌背面将显示为蓝色方块。")

    # 检查背景图片（可选）
    if not os.path.exists(os.path.join(config.IMG_DIR, "background.png")):
        print(f"\n提示: 未找到背景图片 'background.png'。游戏将使用纯色背景。")
        print(f"如果需要背景图，请将其放入 {config.IMG_DIR} 目录。")

    # 检查季节完成图片（可选）
    for theme in themes_to_check:
        complete_img_path = os.path.join(config.IMG_DIR, f"{theme}_complete.png")
        if not os.path.exists(complete_img_path):
             print(f"提示: 未找到 {theme} 季节的完成图片 '{theme}_complete.png'。关卡完成界面将不显示图片。")


# --- 游戏入口 ---
if __name__ == '__main__':
    # 初始化 Pygame（如果 utils 或 game 中没有初始化）
    # pygame.init() # Game 类构造函数中已包含 pygame.init()

    # 检查资源
    check_assets()

    # 创建游戏实例并运行
    game_instance = Game()
    game_instance.run()

    # 退出 Pygame
    pygame.quit()
    sys.exit()
