import io
import math
import os
import re

import requests
from PIL import Image, ImageDraw, ImageFont


class GitHubRepoCard:
    """GitHub 仓库卡片生成器"""

    def __init__(self, repo_url):
        """
        初始化 GitHub 仓库卡片生成器

        :param repo_url: GitHub 仓库 URL，例如 https://github.com/owner/repo
        """
        self.repo_url = repo_url
        self.api_data = None
        self.owner = None
        self.repo_name = None
        self.contributors_count = 0
        self.parse_url()

    def parse_url(self):
        """从 URL 中解析仓库所有者和仓库名"""
        parts = self.repo_url.rstrip('/').split('/')
        self.owner = parts[-2]
        self.repo_name = parts[-1]

    def fetch_repo_data(self):
        """
        从 GitHub API 获取仓库数据

        :return: 成功返回 True，失败返回 False
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}"

        try:
            # 获取仓库基本信息
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            self.api_data = response.json()

            # 获取贡献者数量（通过分页 Link header）
            contributors_url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/contributors?per_page=1"
            contributors_response = requests.get(contributors_url, timeout=10)

            if contributors_response.status_code == 200:
                link_header = contributors_response.headers.get('Link', '')
                if 'last' in link_header:
                    # 从 Link header 解析最后一页的页码
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        self.contributors_count = int(match.group(1))
                    else:
                        self.contributors_count = len(contributors_response.json())
                else:
                    self.contributors_count = len(contributors_response.json())
            else:
                self.contributors_count = 0

            return True
        except Exception as e:
            print(f"获取数据失败: {e}")
            return False

    def download_avatar(self):
        """
        下载仓库所有者的头像并处理为圆形

        :return: 返回处理后的头像图片对象，失败返回 None
        """
        try:
            avatar_url = self.api_data.get('owner', {}).get('avatar_url')
            print(f"📥 正在下载头像: {avatar_url}")

            if avatar_url:
                response = requests.get(avatar_url, timeout=10)
                response.raise_for_status()

                avatar = Image.open(io.BytesIO(response.content))
                print(f"✓ 头像下载成功，尺寸: {avatar.size}")

                # 转换为 RGBA 模式
                if avatar.mode != 'RGBA':
                    avatar = avatar.convert('RGBA')

                # 调整头像大小为 140x140
                avatar = avatar.resize((140, 140), Image.Resampling.LANCZOS)

                # 创建圆形头像
                output = Image.new('RGBA', (140, 140), (246, 248, 250, 255))

                # 创建圆形遮罩
                mask = Image.new('L', (140, 140), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 140, 140), fill=255)

                # 将头像粘贴到背景上（使用圆形遮罩）
                output.paste(avatar, (0, 0), mask)

                print("✓ 头像处理完成")
                return output
            else:
                print("⚠️  未找到头像URL")
                return None

        except Exception as e:
            print(f"❌ 下载头像失败: {e}")
            return None

    # ==================== 图标绘制方法 ====================

    def draw_icon_contributors(self, draw, x, y, size=20, color='#57606a'):
        """绘制贡献者图标（双人形图标）"""
        # 第一个人：头部和身体
        draw.ellipse([(x + 2, y + 2), (x + 8, y + 8)], fill=color)
        draw.ellipse([(x, y + 10), (x + 10, y + size)], fill=color)
        # 第二个人：头部和身体
        draw.ellipse([(x + 12, y + 2), (x + 18, y + 8)], fill=color)
        draw.ellipse([(x + 10, y + 10), (x + 20, y + size)], fill=color)

    def draw_icon_issue(self, draw, x, y, size=20, color='#57606a'):
        """绘制 Issue 图标（圆圈）"""
        # 绘制外圆圈
        draw.ellipse([(x, y), (x + size, y + size)], outline=color, width=2)
        # 在中间添加一个点
        center_x = x + size // 2
        center_y = y + size // 2
        dot_size = 4
        draw.ellipse([(center_x - dot_size // 2, center_y - dot_size // 2),
                      (center_x + dot_size // 2, center_y + dot_size // 2)], fill=color)

    def draw_icon_star(self, draw, x, y, size=20, color='#57606a'):
        """绘制星星图标（五角星）"""
        points = []
        for i in range(10):
            angle = math.pi * 2 * i / 10 - math.pi / 2
            r = size / 2 if i % 2 == 0 else size / 4
            points.append((x + size / 2 + r * math.cos(angle),
                           y + size / 2 + r * math.sin(angle)))
        draw.polygon(points, fill=color)

    def draw_icon_fork(self, draw, x, y, size=20, color='#57606a'):
        """绘制 Fork 图标（分叉图标）"""
        # 主干
        draw.line([(x + size / 2, y + 2), (x + size / 2, y + size - 2)], fill=color, width=2)
        # 左分支
        draw.line([(x + size / 2, y + size / 3), (x + size / 4, y + size * 2 / 3)], fill=color, width=2)
        draw.ellipse([(x + size / 4 - 2, y + size * 2 / 3 - 2),
                      (x + size / 4 + 2, y + size * 2 / 3 + 2)], fill=color)
        # 右分支
        draw.line([(x + size / 2, y + size / 3), (x + size * 3 / 4, y + size * 2 / 3)], fill=color, width=2)
        draw.ellipse([(x + size * 3 / 4 - 2, y + size * 2 / 3 - 2),
                      (x + size * 3 / 4 + 2, y + size * 2 / 3 + 2)], fill=color)
        # 顶部圆点
        draw.ellipse([(x + size / 2 - 2, y), (x + size / 2 + 2, y + 4)], fill=color)

    # ==================== 字体加载方法 ====================

    def get_font(self, size, bold=False):
        """
        获取支持中文的字体

        :param size: 字体大小
        :param bold: 是否加粗
        :return: ImageFont 对象
        """
        font_paths = [
            # macOS 字体
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            # Windows 字体
            "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            # Linux 字体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.BASIC)
                except:
                    continue

        return ImageFont.load_default()

    def get_emoji_font(self, size):
        """
        获取 emoji 字体

        :param size: 字体大小
        :return: ImageFont 对象或 None
        """
        emoji_font_paths = [
            # macOS
            "/System/Library/Fonts/Apple Color Emoji.ttc",
            # Windows
            "C:/Windows/Fonts/seguiemj.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            # Linux (Debian/Ubuntu with fonts-noto-color-emoji)
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            # Linux (alternative paths)
            "/usr/share/fonts/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/color-emoji/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
            # Fallback
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        for font_path in emoji_font_paths:
            if os.path.exists(font_path):
                try:
                    # NotoColorEmoji 是位图字体，只支持固定尺寸 109
                    if "NotoColorEmoji" in font_path:
                        emoji_font = ImageFont.truetype(font_path, 109)
                        print(f"✓ 找到 Emoji 字体: {font_path} (位图字体，固定尺寸 109)")
                        return emoji_font
                    else:
                        print(f"✓ 找到 Emoji 字体: {font_path}")
                        return ImageFont.truetype(font_path, size)
                except Exception as e:
                    print(f"⚠ 加载 Emoji 字体失败 {font_path}: {e}")
                    continue

        print("⚠ 未找到 Emoji 字体，Emoji 可能无法正确显示")
        return None

    # ==================== Emoji 支持方法 ====================

    def is_emoji(self, char):
        """
        判断字符是否为 emoji

        :param char: 单个字符
        :return: 是 emoji 返回 True，否则返回 False
        """
        code = ord(char)
        return (
                0x1F600 <= code <= 0x1F64F or  # 表情符号
                0x1F300 <= code <= 0x1F5FF or  # 符号和象形文字
                0x1F680 <= code <= 0x1F6FF or  # 交通和地图符号
                0x1F700 <= code <= 0x1F77F or  # 炼金术符号
                0x1F780 <= code <= 0x1F7FF or  # 几何形状扩展
                0x1F800 <= code <= 0x1F8FF or  # 补充箭头-C
                0x1F900 <= code <= 0x1F9FF or  # 补充符号和象形文字
                0x1FA00 <= code <= 0x1FA6F or  # 扩展-A
                0x1FA70 <= code <= 0x1FAFF or  # 符号和象形文字扩展-A
                0x2600 <= code <= 0x26FF or  # 杂项符号
                0x2700 <= code <= 0x27BF or  # 装饰符号
                0xFE00 <= code <= 0xFE0F or  # 变体选择器
                0x1F1E6 <= code <= 0x1F1FF  # 区域指示符号
        )

    def draw_text_with_emoji(self, draw, xy, text, font, fill, emoji_font=None):
        """
        绘制支持 emoji 的文本（文本和 emoji 分别用不同字体渲染）

        :param draw: ImageDraw 对象
        :param xy: 绘制位置 (x, y)
        :param text: 要绘制的文本
        :param font: 普通文本字体
        :param fill: 文本颜色
        :param emoji_font: emoji 字体（可选）
        """
        if not text:
            return

        # 获取 emoji 字体
        if emoji_font is None:
            emoji_font = self.get_emoji_font(font.size if hasattr(font, 'size') else 24)

        x, y = xy
        current_x = x

        # 计算 emoji 的目标大小和偏移量
        font_size = font.size if hasattr(font, 'size') else 24
        emoji_y_offset = int(font_size * 0.05)  # emoji 轻微向下偏移 5%，与文字基线对齐

        # NotoColorEmoji 固定 109px，需要缩放到目标大小
        emoji_actual_size = emoji_font.size if hasattr(emoji_font, 'size') else 109
        emoji_target_size = int(font_size * 1.2)  # emoji 比文字稍大 20%
        emoji_scale = emoji_target_size / emoji_actual_size if emoji_actual_size > 0 else 1.0

        # 解析文本，分离普通文本和 emoji
        i = 0
        while i < len(text):
            # 收集连续的普通字符
            normal_text = ""
            while i < len(text) and not self.is_emoji(text[i]):
                normal_text += text[i]
                i += 1

            # 绘制普通文本
            if normal_text:
                try:
                    draw.text((current_x, y), normal_text, fill=fill, font=font)
                    bbox = draw.textbbox((current_x, y), normal_text, font=font)
                    current_x = bbox[2]
                except:
                    pass

            # 收集连续的 emoji
            emoji_text = ""
            while i < len(text) and (self.is_emoji(text[i]) or ord(text[i]) == 0xFE0F):
                emoji_text += text[i]
                i += 1

            # 绘制 emoji（需要缩放）
            if emoji_text and emoji_font:
                try:
                    # 创建临时图像来渲染 emoji
                    temp_bbox = draw.textbbox((0, 0), emoji_text, font=emoji_font)
                    temp_width = temp_bbox[2] - temp_bbox[0]
                    temp_height = temp_bbox[3] - temp_bbox[1]

                    if temp_width > 0 and temp_height > 0:
                        # 创建临时 RGBA 图像
                        temp_img = Image.new('RGBA', (temp_width + 20, temp_height + 20), (0, 0, 0, 0))
                        temp_draw = ImageDraw.Draw(temp_img)

                        # 在临时图像上绘制 emoji
                        try:
                            temp_draw.text((10, 10), emoji_text, font=emoji_font, embedded_color=True)
                        except (TypeError, AttributeError):
                            temp_draw.text((10, 10), emoji_text, font=emoji_font, fill=fill)

                        # 缩放到目标大小
                        scaled_width = int(temp_img.width * emoji_scale)
                        scaled_height = int(temp_img.height * emoji_scale)
                        scaled_img = temp_img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

                        # 粘贴到主图像
                        main_img = draw._image
                        main_img.paste(scaled_img, (int(current_x), int(y + emoji_y_offset)), scaled_img)

                        # 更新 x 位置
                        current_x += scaled_width - int(font_size * 0.3)
                except Exception as e:
                    print(f"⚠ Emoji 绘制失败: {e}")
                    pass

    # ==================== 文本处理方法 ====================

    def format_number(self, num):
        """
        格式化数字（大于1000时使用 k 表示）

        :param num: 数字
        :return: 格式化后的字符串
        """
        if num >= 1000:
            return f"{num / 1000:.1f}k"
        return str(num)

    def get_text_width_with_emoji(self, text, font, draw, emoji_font=None):
        """
        计算包含 emoji 的文本宽度

        :param text: 文本内容
        :param font: 普通文本字体
        :param draw: ImageDraw 对象
        :param emoji_font: emoji 字体（可选）
        :return: 文本总宽度
        """
        if not text:
            return 0

        if emoji_font is None:
            emoji_font = self.get_emoji_font(font.size if hasattr(font, 'size') else 24)

        total_width = 0
        i = 0

        # 计算 emoji 缩放比例
        font_size = font.size if hasattr(font, 'size') else 24
        emoji_actual_size = emoji_font.size if (emoji_font and hasattr(emoji_font, 'size')) else 109
        emoji_target_size = int(font_size * 1.2)
        emoji_scale = emoji_target_size / emoji_actual_size if emoji_actual_size > 0 else 1.0

        while i < len(text):
            # 收集连续的普通字符
            normal_text = ""
            while i < len(text) and not self.is_emoji(text[i]):
                normal_text += text[i]
                i += 1

            # 计算普通文本宽度
            if normal_text:
                bbox = draw.textbbox((0, 0), normal_text, font=font)
                total_width += bbox[2] - bbox[0]

            # 收集连续的 emoji
            emoji_text = ""
            while i < len(text) and (self.is_emoji(text[i]) or ord(text[i]) == 0xFE0F):
                emoji_text += text[i]
                i += 1

            # 计算 emoji 宽度（应用缩放比例，减去右侧间距）
            if emoji_text and emoji_font:
                bbox = draw.textbbox((0, 0), emoji_text, font=emoji_font)
                emoji_width = (bbox[2] - bbox[0]) * emoji_scale
                total_width += emoji_width - int(font_size * 0.3)

        return total_width

    def find_break_point(self, text):
        """
        找到合适的断行点
        优先级：空格 > 中文标点 > 中文字符 > 其他

        :param text: 文本
        :return: 断行位置索引
        """
        # 从后向前查找空格
        last_space = text.rfind(' ')
        if last_space > len(text) * 0.5:  # 如果空格在后半部分
            return last_space

        # 查找中文标点
        chinese_punctuation = '，。！？；：、'
        for i in range(len(text) - 1, -1, -1):
            if text[i] in chinese_punctuation:
                return i + 1

        # 查找最后一个中文字符
        for i in range(len(text) - 1, -1, -1):
            if '\u4e00' <= text[i] <= '\u9fa5':
                return i + 1

        # 默认返回整个长度
        return len(text)

    def wrap_text_mixed(self, text, font, max_width, draw, max_lines=3):
        """
        混合文本换行 - 支持中英文和 emoji，智能处理
        只在最后一行添加省略号，前面的行完整显示

        :param text: 要换行的文本
        :param font: 字体
        :param max_width: 最大宽度
        :param draw: ImageDraw 对象
        :param max_lines: 最大行数
        :return: 换行后的文本列表
        """
        if not text:
            return []

        emoji_font = self.get_emoji_font(font.size if hasattr(font, 'size') else 24)
        lines = []
        remaining_text = text

        for line_num in range(max_lines):
            if not remaining_text:
                break

            # 是否是最后一行
            is_last_line = (line_num == max_lines - 1)

            # 寻找当前行能容纳的最大内容
            current_line = ""
            char_index = 0

            # 逐字符测试
            for i, char in enumerate(remaining_text):
                test_line = current_line + char

                # 如果是最后一行且还有剩余内容，预留省略号空间
                if is_last_line and i < len(remaining_text) - 1:
                    test_with_ellipsis = test_line + "..."
                    width = self.get_text_width_with_emoji(test_with_ellipsis, font, draw, emoji_font)
                else:
                    width = self.get_text_width_with_emoji(test_line, font, draw, emoji_font)

                if width <= max_width:
                    current_line = test_line
                    char_index = i + 1
                else:
                    # 当前字符放不下了，尝试在合适位置断行
                    if current_line:
                        break_point = self.find_break_point(current_line)
                        if break_point > 0:
                            current_line = current_line[:break_point]
                            char_index = break_point
                    break

            if current_line:
                # 如果是最后一行且还有剩余文本，添加省略号
                if is_last_line and char_index < len(remaining_text):
                    # 需要确保加上省略号后不超宽
                    while current_line:
                        test_line = current_line + "..."
                        width = self.get_text_width_with_emoji(test_line, font, draw, emoji_font)
                        if width <= max_width:
                            current_line = test_line
                            break
                        # 去掉最后一个字符再试
                        current_line = current_line[:-1]

                lines.append(current_line)
                remaining_text = remaining_text[char_index:].lstrip()
            else:
                break

        return lines

    def truncate_text_smart(self, text, font, max_width, draw):
        """
        智能截断文本并添加省略号（支持 emoji）

        :param text: 要截断的文本
        :param font: 字体
        :param max_width: 最大宽度
        :param draw: ImageDraw 对象
        :return: 截断后的文本
        """
        if not text:
            return ""

        emoji_font = self.get_emoji_font(font.size if hasattr(font, 'size') else 24)
        width = self.get_text_width_with_emoji(text, font, draw, emoji_font)
        if width <= max_width:
            return text

        ellipsis = "..."
        for i in range(len(text), 0, -1):
            test_text = text[:i] + ellipsis
            width = self.get_text_width_with_emoji(test_text, font, draw, emoji_font)
            if width <= max_width:
                return test_text

        return ellipsis

    # ==================== 绘制方法 ====================

    def draw_repo_title(self, draw, x, y, max_width):
        """
        绘制仓库标题（作者名置灰，仓库名黑色加粗）

        :param draw: ImageDraw 对象
        :param x: 起始 x 坐标
        :param y: 起始 y 坐标
        :param max_width: 最大宽度
        :return: 下一行的 y 坐标
        """
        # 使用更大的字体
        owner_font = self.get_font(48, bold=False)
        repo_font = self.get_font(52, bold=True)  # 仓库名字体更大且加粗
        slash_font = self.get_font(48, bold=False)
        emoji_font = self.get_emoji_font(48)

        owner_color = '#656d76'  # 灰色
        repo_color = '#1f2328'  # 黑色
        slash_color = '#656d76'  # 灰色

        # 测试完整显示是否能放下
        owner_text = self.owner
        slash_text = '/'
        repo_text = self.repo_name

        # 计算各部分宽度（考虑 emoji）
        owner_width = self.get_text_width_with_emoji(owner_text, owner_font, draw, emoji_font)
        slash_width = self.get_text_width_with_emoji(slash_text, slash_font, draw, emoji_font)
        repo_width = self.get_text_width_with_emoji(repo_text, repo_font, draw, emoji_font)

        total_width = owner_width + slash_width + repo_width

        if total_width <= max_width:
            # 一行能放下，绘制在同一行
            current_x = x

            # 绘制作者名（灰色）
            self.draw_text_with_emoji(draw, (current_x, y), owner_text, owner_font, owner_color)
            current_x += owner_width

            # 绘制斜杠（灰色）
            self.draw_text_with_emoji(draw, (current_x, y), slash_text, slash_font, slash_color)
            current_x += slash_width

            # 绘制仓库名（黑色，加粗）- 向上调整以对齐基线
            repo_y_offset = -8  # 向上调整8像素
            for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                self.draw_text_with_emoji(draw, (current_x + offset[0], y + repo_y_offset + offset[1]),
                                          repo_text, repo_font, repo_color)

            return y + 55  # 返回下一行的Y坐标
        else:
            # 需要换行
            # 第一行：owner/
            current_x = x
            self.draw_text_with_emoji(draw, (current_x, y), owner_text, owner_font, owner_color)
            current_x += owner_width
            self.draw_text_with_emoji(draw, (current_x, y), slash_text, slash_font, slash_color)

            # 第二行：repo名称
            next_y = y + 55

            # 如果repo名称太长，截断
            repo_y_offset = -2  # 向上调整2像素以对齐
            if repo_width > max_width:
                truncated_repo = self.truncate_text_smart(repo_text, repo_font, max_width, draw)
                # 绘制截断的仓库名（黑色，加粗）
                for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                    self.draw_text_with_emoji(draw, (x + offset[0], next_y + repo_y_offset + offset[1]),
                                              truncated_repo, repo_font, repo_color)
            else:
                # 绘制完整仓库名（黑色，加粗）
                for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                    self.draw_text_with_emoji(draw, (x + offset[0], next_y + repo_y_offset + offset[1]),
                                              repo_text, repo_font, repo_color)

            return next_y + 55  # 返回下一行的Y坐标

    def create_card(self, output_path="github_card.png"):
        """
        创建 GitHub 仓库卡片

        :param output_path: 输出文件路径
        :return: 成功返回输出路径，失败返回 None
        """
        if not self.api_data:
            if not self.fetch_repo_data():
                return None

        # 卡片尺寸 900x450
        WIDTH = 900
        HEIGHT = 450

        # 创建 RGBA 模式的浅灰色背景
        img = Image.new('RGBA', (WIDTH, HEIGHT), (246, 248, 250, 255))  # #f6f8fa
        draw = ImageDraw.Draw(img)

        # 加载字体
        desc_font = self.get_font(24)
        stats_number_font = self.get_font(26, bold=True)
        stats_label_font = self.get_font(15)

        # 下载头像
        print("\n🎨 开始处理头像...")
        avatar = self.download_avatar()

        # === 1. 绘制头像（右上角）===
        AVATAR_SIZE = 140
        AVATAR_X = WIDTH - 200
        AVATAR_Y = 50

        if avatar:
            print(f"✓ 在位置 ({AVATAR_X}, {AVATAR_Y}) 粘贴头像")
            img.paste(avatar, (AVATAR_X, AVATAR_Y), avatar)  # 使用 alpha 通道
        else:
            # 绘制占位圆
            draw.ellipse([(AVATAR_X, AVATAR_Y), (AVATAR_X + AVATAR_SIZE, AVATAR_Y + AVATAR_SIZE)],
                         fill='#d0d7de', outline='#d0d7de', width=2)

        # === 2. 绘制仓库名称（作者灰色，仓库名黑色）===
        CONTENT_LEFT = 60
        CONTENT_RIGHT_MARGIN = 40
        title_y = 60

        # 计算标题可用宽度（避免覆盖头像）
        max_title_width = AVATAR_X - CONTENT_LEFT - CONTENT_RIGHT_MARGIN

        # 绘制标题（作者灰色，仓库名黑色加粗）
        title_end_y = self.draw_repo_title(draw, CONTENT_LEFT, title_y, max_title_width)

        # === 3. 计算描述区域 ===
        # 描述从标题结束后开始，但要考虑头像的底部位置
        desc_start_y = max(title_end_y + 10, AVATAR_Y + AVATAR_SIZE + 10)

        # === 4. 绘制描述（最多3行，自动换行）===
        description = self.api_data.get('description', 'No description provided')
        if description:
            # 描述区域使用整个卡片宽度（减去左右边距）
            max_desc_width = WIDTH - CONTENT_LEFT - CONTENT_RIGHT_MARGIN

            # 使用混合换行函数
            desc_lines = self.wrap_text_mixed(description, desc_font, max_desc_width, draw, max_lines=3)

            print(f"📝 描述行数: {len(desc_lines)}")

            # 绘制每一行描述
            current_y = desc_start_y
            for i, line in enumerate(desc_lines):
                print(f"   第{i + 1}行: {line}")
                self.draw_text_with_emoji(draw, (CONTENT_LEFT, current_y), line, desc_font, '#656d76')
                current_y += 30

        # === 5. 绘制底部统计信息（图标和数字垂直居中对齐）===
        STATS_BASE_Y = HEIGHT - 100

        stats_data = [
            (self.contributors_count, "Contributors", 'contributors'),
            (self.api_data.get('open_issues_count', 0), "Issues+PRs", 'issue'),
            (self.api_data.get('forks_count', 0), "Forks", 'fork'),
            (self.api_data.get('stargazers_count', 0), "Stars", 'star'),
        ]

        # 计算每个统计项的宽度
        stats_count = len(stats_data)
        section_width = (WIDTH - CONTENT_LEFT * 2) / stats_count

        icon_size = 20
        icon_color = '#57606a'

        # 先计算数字文本的实际高度
        sample_text = "123"
        sample_bbox = draw.textbbox((0, 0), sample_text, font=stats_number_font)
        text_height = sample_bbox[3] - sample_bbox[1]

        # 数字的Y位置
        number_y = STATS_BASE_Y

        # 计算图标应该放置的Y位置，使其与数字垂直居中
        # 图标大小是 20，文本高度约 26，所以图标应该向下偏移 (26-20)/2 = 3
        icon_y = number_y + 8

        for i, (count, label, icon_type) in enumerate(stats_data):
            x = CONTENT_LEFT + int(i * section_width)

            # 绘制图标
            icon_x = x

            if icon_type == 'contributors':
                self.draw_icon_contributors(draw, icon_x, icon_y, icon_size, icon_color)
            elif icon_type == 'issue':
                self.draw_icon_issue(draw, icon_x, icon_y, icon_size, icon_color)
            elif icon_type == 'star':
                self.draw_icon_star(draw, icon_x, icon_y, icon_size, icon_color)
            elif icon_type == 'fork':
                self.draw_icon_fork(draw, icon_x, icon_y, icon_size, icon_color)

            # 绘制数字
            number_x = x + icon_size + 10
            number_text = self.format_number(count)

            # 加粗效果
            for offset in [(0, 0), (1, 0)]:
                draw.text((number_x + offset[0], number_y + offset[1]),
                          number_text, fill='#1f2328', font=stats_number_font)

            # 绘制标签（在图标和数字下方）
            label_y = STATS_BASE_Y + text_height + 10
            draw.text((x, label_y), label, fill='#656d76', font=stats_label_font)

        # === 6. 绘制底部彩色条===
        COLOR_BAR_HEIGHT = 12
        gradient_colors = ['#ea4335', '#fbbc04', '#34a853', '#4285f4']
        color_width = WIDTH / len(gradient_colors)

        for i, color in enumerate(gradient_colors):
            x_start = int(i * color_width)
            x_end = int((i + 1) * color_width)
            draw.rectangle(
                [(x_start, HEIGHT - COLOR_BAR_HEIGHT), (x_end, HEIGHT)],
                fill=color
            )

        # 转换为RGB模式并保存（PNG支持透明度，但为了兼容性转为RGB）
        rgb_img = Image.new('RGB', img.size, (246, 248, 250))
        rgb_img.paste(img, mask=img.split()[3])  # 使用alpha通道作为遮罩

        # 保存
        rgb_img.save(output_path, 'PNG', quality=95)
        print(f"✓ 卡片已生成: {output_path}")
        return output_path


def main():
    """主函数"""
    print("=" * 60)
    print("       GitHub 仓库卡片生成器")
    print("=" * 60)

    repo_url = input("\n请输入GitHub仓库地址: ").strip()

    if not repo_url:
        print("❌ 错误: 仓库地址不能为空")
        return

    if 'github.com' not in repo_url:
        print("❌ 错误: 请输入有效的GitHub仓库地址")
        return

    print("\n⏳ 正在获取仓库信息...")
    card_generator = GitHubRepoCard(repo_url)

    if card_generator.fetch_repo_data():
        print(f"\n📦 仓库名称: {card_generator.owner}/{card_generator.repo_name}")
        print(f"📝 描述: {card_generator.api_data.get('description', '无')}")
        print(f"⭐ Stars: {card_generator.api_data.get('stargazers_count', 0)}")
        print(f"🔱 Forks: {card_generator.api_data.get('forks_count', 0)}")
        print(f"⚠️  Issues: {card_generator.api_data.get('open_issues_count', 0)}")
        print(f"👥 贡献者: {card_generator.contributors_count}")

        print("\n🎨 正在生成卡片...")
        output_path = card_generator.create_card()

        if output_path:
            print(f"\n✅ 成功! 卡片已保存至: {output_path}")
            print(f"📁 完整路径: {os.path.abspath(output_path)}")
    else:
        print("\n❌ 获取仓库信息失败，请检查:")
        print("   1. 仓库地址是否正确")
        print("   2. 仓库是否为公开仓库")
        print("   3. 网络连接是否正常")


if __name__ == "__main__":
    main()
