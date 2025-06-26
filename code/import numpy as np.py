import numpy as np

filename = 'bodmas.npz'
data = np.load(filename)
X = data['X']  # all the feature vectors
y = data['y']  # labels, 0 as benign, 1 as malicious



import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def vector_to_grayscale_image(data, width=256, save_path=None):
    """
    將一維向量轉換為寬度為 width 的灰階圖像並顯示，可選擇儲存為圖像檔案。

    :param data: 一維 numpy array，例如 shape=(2381,)
    :param width: 轉換後圖像的寬度，預設為 256
    :param save_path: 若指定路徑，將圖片儲存至該位置（例如 'output.png'）
    :return: 圖像的 2D numpy array (已 normalize 並轉成 uint8)
    """
    data = np.array(data)

    # 補零至可以整除 width
    remainder = len(data) % width
    if remainder != 0:
        padding = width - remainder
        data = np.pad(data, (0, padding), 'constant')

    # reshape 成 (height, width)
    height = len(data) // width
    image = data.reshape((height, width))

    # normalize 到 [0, 255] 並轉為 uint8
    image_min = image.min()
    image_max = image.max()
    if image_max > image_min:
        norm_image = (image - image_min) / (image_max - image_min)  # [0, 1]
    else:
        norm_image = np.zeros_like(image)
    image_uint8 = (norm_image * 255).astype(np.uint8)

    # 顯示圖片
    plt.imshow(image_uint8, cmap='gray')
    plt.title(f"Grayscale Image ({height}x{width})")
    plt.axis('off')
    plt.show()

    # 儲存圖片
    if save_path:
        img = Image.fromarray(image_uint8, mode='L')
        img.save(save_path)

    return image_uint8

# 使用範例
#data = X[0]  # 用隨機資料模擬
#image_array = vector_to_grayscale_image(data, width=256, save_path='grayscale_output.png')

print(X.shape, y.shape)
print((X[0]))
