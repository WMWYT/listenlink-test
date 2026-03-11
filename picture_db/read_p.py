from PIL import Image
import numpy as np

# 1. 打开 PNG 图片（Pillow 会在内部自动完成解压）
img = Image.open("white_background.png")

# 2. 将图片转换为 numpy 数组，得到解压后的像素值
pixel_data = np.array(img)

# 3. 读取像素值
print(f"图片尺寸: {pixel_data.shape}")  # (800, 800)
print(f"像素数据类型: {pixel_data.dtype}")  # bool（1位灰度图，True=白，False=黑）

# 读取具体位置的像素值（比如左上角第 1 个像素）
x, y = 0, 0
print(f"坐标 ({x},{y}) 的像素值: {pixel_data[y, x]}")  # 输出: True（白色）

# 验证所有像素是否都是白色
print(f"所有像素是否为白色: {np.all(pixel_data == True)}")  # 输出: True