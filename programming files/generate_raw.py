import numpy as np
import matplotlib.pyplot as plt

def create_binary_image(width, height):
    """Создание бинарного изображения со случайными черными и белыми пикселями"""
    # Создаем массив случайных значений с вероятностью 0.2 для белых пикселей
    binary_img = np.random.choice([0, 1], size=(height, width), p=[0.8, 0.2])
    
    return binary_img

def create_grayscale_image(width, height):
    """Создание изображения со случайными оттенками серого"""
    # Создаем массив случайных значений от 0 до 1
    gray_img = np.random.random(size=(height, width))
    return gray_img

def create_color_image(width, height):
    """Создание цветного RGB изображения со случайными цветами"""
    # Создаем массив случайных значений от 0 до 1 для каждого канала (R,G,B)
    color_img = np.random.random(size=(height, width, 3))
    return color_img

def display_images():
    # Параметры изображения
    width = 800
    height = 600
    
    try:
        # Создаем все типы изображений
        print("\nСоздаем изображения...")
        bw_img = create_binary_image(width, height)
        gray_img = create_grayscale_image(width, height)
        color_img = create_color_image(width, height)
       # Бинарное изbбрary_reprение
        plt.figure(figsize=(8, 6))
        plt.imshow(bw_img, cmap='binary')
        plt.title('Бинарное изображение')
        plt.axis('off')
        
        # Серое изображение
        plt.figure(figsize=(8, 6))
        plt.imshow(gray_img, cmap='gray')
        plt.title('Серое изображение')
        plt.axis('off')
        
        # Цветное изображение
        plt.figure(figsize=(8, 6))
        plt.imshow(color_img)
        plt.title('Цветное изображение')
        plt.axis('off')
        
        plt.show()
        
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    display_images() 