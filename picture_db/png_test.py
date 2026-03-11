from PIL import Image

# ----------------------
# 1. 创建 800x800 的 1 位灰度纯白图像
# ----------------------
width, height = 1, 1
# mode="1" 表示 1 位灰度图（非黑即白），color=1 代表白色
img = Image.new(mode="4", size=(width, height), color=(255, 255, 255, 255))

# ----------------------
# 2. 保存为标准压缩的 PNG
# ----------------------
img.save(
    "white_background.png",
    format="PNG",
    compress_level=9  # 保持最大压缩
)

print("纯白背景 PNG 已生成：white_background.png")
