from PIL import Image
import numpy as np

# 假设你已经把两个十六进制数据保存为文件：
# - A: "original.png"
# - B: "downloaded.png"（需要先补全十六进制数据并保存为文件）

img_a = Image.open("psc-white.png")
img_b = Image.open("white_background.png")

# 对比像素数据
pixel_a = np.array(img_a)
pixel_b = np.array(img_b)

print(f"像素数据是否完全一致: {np.array_equal(pixel_a, pixel_b)}")  # 输出: True