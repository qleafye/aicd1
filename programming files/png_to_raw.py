from PIL import Image  # Добавляем импорт PIL
import numpy as np    # Добавляем импорт numpy

def png_to_raw(image_path, output_path, mode):
    # Открываем изображение используя PIL.Image
    image = Image.open(image_path)
    
    # Конвертируем изображение в нужный формат
    if mode == 'L':  # Для черно-белого или серого
        image = image.convert('L')
    elif mode == 'RGB':  # Для цветного
        if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
            image = image.convert('RGB')
    
    # Преобразуем в numpy массив и затем в байты
    raw_pixels = np.array(image)
    raw_data = raw_pixels.tobytes()

    # Записываем в файл
    with open(output_path, 'wb') as f:
        f.write(raw_data)

# Конвертируем изображения с правильными режимами
png_to_raw('bw_image.jpg', 'bw_image.raw', 'L')      # Черно-белое как grayscale
png_to_raw('gray_image.png', 'gray_image.raw', 'L')  # Серое
png_to_raw('color_image.png', 'color_image.raw', 'RGB')   # Цветное
