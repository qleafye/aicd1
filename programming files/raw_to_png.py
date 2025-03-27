from PIL import Image
import numpy as np
import os

def raw_to_png(raw_path, output_path, mode):
    # Получаем размер файла
    file_size = os.path.getsize(raw_path)
    
    # Читаем RAW данные
    with open(raw_path, 'rb') as f:
        raw_data = f.read()
    
    # Определяем размеры на основе размера файла
    if mode == 'L':  # Для черно-белого/серого
        total_pixels = file_size  # 1 байт на пиксель
    else:  # RGB
        total_pixels = file_size // 3  # 3 байта на пиксель
    
    # Пробуем разные стандартные разрешения
    standard_resolutions = [
        (512, 512),
        (600, 600),
        (800, 600),
        (1024, 768),
        (1280, 720),
        (3000,2000),
        (3080,1732)
    ]
    
    # Находим подходящее разрешение
    width = height = None
    for w, h in standard_resolutions:
        if w * h == total_pixels:
            width, height = w, h
            break
    
    if width is None:
        # Если не нашли стандартное разрешение, используем квадратное
        width = height = int(np.sqrt(total_pixels))
        if width * height != total_pixels:
            # Если не получается квадратное, пробуем прямоугольное
            width = int(np.sqrt(total_pixels * 4/3))  # пропорция 4:3
            height = total_pixels // width
    
    print(f"Файл: {raw_path}")
    print(f"Размер файла: {file_size} байт")
    print(f"Определенные размеры: {width}x{height}")
    
    try:
        # Преобразуем байты в numpy массив
        if mode == 'L':
            image_array = np.frombuffer(raw_data, dtype=np.uint8).reshape(height, width)
        elif mode == 'RGB':
            image_array = np.frombuffer(raw_data, dtype=np.uint8).reshape(height, width, 3)
        
        # Создаем изображение из массива
        image = Image.fromarray(image_array, mode)
        
        # Сохраняем как PNG
        image.save(output_path)
        print(f"Изображение успешно сохранено как {output_path}\n")
        
    except ValueError as e:
        print(f"Ошибка при обработке файла: {e}\n")

# Конвертируем RAW файлы обратно в PNG
raw_to_png('bw_image.raw', 'bw_image_restored.png', 'L')
raw_to_png('gray_image.raw', 'gray_image_restored.png', 'L')
raw_to_png('color_image.raw', 'color_image_restored.png', 'RGB') 