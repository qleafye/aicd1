import numpy as np
import matplotlib.pyplot as plt
import math
import os

def bwt_transform(data: bytes) -> tuple[bytes, int]:
    """Преобразование Барроуза-Уилера"""
    # Создаем все возможные повороты строки
    rotations = [data[i:] + data[:i] for i in range(len(data))]
    # Сортируем повороты
    rotations.sort()
    # Находим индекс исходной строки
    original_index = rotations.index(data)
    # Берем последний символ каждого поворота
    transformed = bytes(rotation[-1] for rotation in rotations)
    return transformed, original_index

def mtf_encode(data: bytes) -> bytes:
    """Move-to-Front кодирование"""
    # Инициализируем алфавит
    alphabet = list(range(256))
    result = bytearray()
    
    # Кодируем каждый символ
    for byte in data:
        # Находим позицию символа в алфавите
        index = alphabet.index(byte)
        result.append(index)
        # Перемещаем символ в начало алфавита
        alphabet.pop(index)
        alphabet.insert(0, byte)
    
    return bytes(result)

def calculate_entropy(data: bytes) -> float:
    """Вычисляет энтропию данных"""
    # Подсчет частот символов
    counter = np.zeros(256, dtype=int)
    for byte in data:
        counter[byte] += 1
    
    # Вычисление энтропии
    total_symbols = len(data)
    entropy = 0.0
    for count in counter:
        if count > 0:
            probability = count / total_symbols
            entropy -= probability * math.log2(probability)
    return entropy

def process_block_and_get_entropy(data: bytes, block_size: int) -> float:
    """Обрабатывает данные блоками и возвращает среднюю энтропию"""
    total_entropy = 0
    block_count = 0
    
    # Обработка каждого блока
    for i in range(0, len(data), block_size):
        block = data[i:i + block_size]
        if len(block) < block_size:  # Пропускаем неполный последний блок
            continue
            
        # Применяем BWT и MTF к блоку
        transformed_data, _ = bwt_transform(block)
        mtf_data = mtf_encode(transformed_data)
        
        # Вычисляем энтропию преобразованного блока
        entropy = calculate_entropy(mtf_data)
        total_entropy += entropy
        block_count += 1
        
        # Выводим прогресс
        print(f"Обработано блоков: {block_count}", end='\r')
    
    print()  # Новая строка после прогресса
    return total_entropy / block_count if block_count > 0 else 0

def analyze_block_sizes():
    # Проверяем наличие файла enwik7
    if not os.path.exists('enwik7'):
        print("Ошибка: файл enwik7 не найден!")
        return
    
    # Читаем файл enwik7
    print("Чтение файла enwik7...")
    with open('enwik7', 'rb') as f:
        data = f.read()
    
    # Определяем размеры блоков для анализа (от 1KB до 1MB)
    block_sizes = [
        1024,        # 1 KB
        4096,        # 4 KB
        16384,       # 16 KB
        65536,       # 64 KB
        262144,      # 256 KB
        1048576      # 1 MB
    ]
    
    # Вычисляем энтропию для каждого размера блока
    entropies = []
    for size in block_sizes:
        print(f"\nОбработка блоков размером {size/1024:.1f} KB...")
        entropy = process_block_and_get_entropy(data, size)
        entropies.append(entropy)
        print(f"Средняя энтропия: {entropy:.4f} бит/символ")
    
    # Строим график
    plt.figure(figsize=(10, 6))
    plt.semilogx(block_sizes, entropies, 'bo-')
    plt.grid(True)
    plt.xlabel('Размер блока (байт)')
    plt.ylabel('Средняя энтропия (бит/символ)')
    plt.title('Зависимость энтропии от размера блока для enwik7')
    
    # Добавляем подписи размеров в KB/MB
    plt.xticks(block_sizes, [f'{size/1024:.0f}KB' if size < 1048576 else f'{size/1048576:.0f}MB' 
                            for size in block_sizes])
    
    # Находим оптимальный размер блока
    optimal_index = np.argmin(entropies)
    optimal_size = block_sizes[optimal_index]
    optimal_entropy = entropies[optimal_index]
    
    plt.plot(optimal_size, optimal_entropy, 'ro', label=f'Оптимальный размер: {optimal_size/1024:.0f}KB')
    plt.legend()
    
    # Сохраняем график
    plt.savefig('entropy_analysis.png')
    plt.show()
    
    # Выводим результаты
    print("\nРезультаты анализа:")
    print("-" * 50)
    print(f"{'Размер блока':>15} | {'Энтропия':>10}")
    print("-" * 50)
    for size, entropy in zip(block_sizes, entropies):
        print(f"{size/1024:>12.1f} KB | {entropy:>10.4f}")
    print("-" * 50)
    print(f"\nОптимальный размер блока: {optimal_size/1024:.1f} KB")
    print(f"Минимальная энтропия: {optimal_entropy:.4f} бит/символ")

if __name__ == "__main__":
    analyze_block_sizes() 