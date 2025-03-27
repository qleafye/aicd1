import numpy as np
import matplotlib.pyplot as plt
import time
import os

def lz77_encode(data: bytes, buffer_size: int) -> bytes:
    """LZ77 кодирование с настраиваемым размером буфера"""
    encoded_data = bytearray()
    i = 0
    n = len(data)

    while i < n:
        max_length = 0
        max_offset = 0

        # Определяем границы поиска
        search_start = max(0, i - buffer_size)
        search_end = i

        # Ищем максимальное совпадение
        for length in range(min(255, n - i), 2, -1):
            substring = data[i:i + length]
            offset = data[search_start:search_end].rfind(substring)
            if offset != -1:
                max_length = length
                max_offset = search_end - search_start - offset
                break

        if max_length > 2:  # Минимальная длина для эффективного сжатия
            # Кодируем offset и length
            encoded_data.append(1)  # Флаг для ссылки
            encoded_data.append((max_offset >> 8) & 0xFF)
            encoded_data.append(max_offset & 0xFF)
            encoded_data.append(max_length & 0xFF)
            i += max_length
        else:
            # Кодируем один символ
            encoded_data.append(0)  # Флаг для литерала
            encoded_data.append(data[i])
            i += 1

    return bytes(encoded_data)

def analyze_buffer_sizes(file_path: str):
    """Анализирует эффективность сжатия для разных размеров буфера"""
    print(f"Анализ файла: {file_path}")
    
    # Читаем файл
    with open(file_path, 'rb') as f:
        data = f.read()
    original_size = len(data)
    print(f"Размер файла: {original_size:,} байт")

    # Размеры буфера для тестирования (от 256 байт до 64 КБ)
    buffer_sizes = [
        256,         # 256 B
        1024,        # 1 KB
        4096,        # 4 KB
        16384,       # 16 KB
        65536,       # 64 KB
        262144,      # 256 KB
        1048576      # 1 MB
    ]

    results = []
    for buffer_size in buffer_sizes:
        print(f"\nТестирование буфера размером {buffer_size/1024:.1f} KB...")
        
        # Замеряем время и сжимаем
        start_time = time.time()
        compressed = lz77_encode(data, buffer_size)
        compression_time = time.time() - start_time
        
        # Вычисляем метрики
        compressed_size = len(compressed)
        compression_ratio = original_size / compressed_size
        space_saving = (1 - compressed_size / original_size) * 100
        
        results.append({
            'buffer_size': buffer_size,
            'compressed_size': compressed_size,
            'ratio': compression_ratio,
            'saving': space_saving,
            'time': compression_time
        })
        
        print(f"Степень сжатия: {compression_ratio:.2f}")
        print(f"Экономия места: {space_saving:.1f}%")
        print(f"Время сжатия: {compression_time:.2f} сек")

    # Строим графики
    plt.figure(figsize=(15, 5))

    # График степени сжатия
    plt.subplot(131)
    plt.semilogx([r['buffer_size'] for r in results], 
                 [r['ratio'] for r in results], 'bo-')
    plt.grid(True)
    plt.xlabel('Размер буфера (байт)')
    plt.ylabel('Степень сжатия')
    plt.title('Степень сжатия')

    # График экономии места
    plt.subplot(132)
    plt.semilogx([r['buffer_size'] for r in results], 
                 [r['saving'] for r in results], 'go-')
    plt.grid(True)
    plt.xlabel('Размер буфера (байт)')
    plt.ylabel('Экономия места (%)')
    plt.title('Экономия места')

    # График времени сжатия
    plt.subplot(133)
    plt.semilogx([r['buffer_size'] for r in results], 
                 [r['time'] for r in results], 'ro-')
    plt.grid(True)
    plt.xlabel('Размер буфера (байт)')
    plt.ylabel('Время сжатия (сек)')
    plt.title('Время сжатия')

    plt.tight_layout()
    plt.savefig('lz77_analysis.png')
    plt.show()

    # Находим оптимальный размер буфера
    # Используем метрику, учитывающую и степень сжатия, и время
    optimal_result = max(results, key=lambda x: x['ratio'] / (x['time'] ** 0.5))
    
    # Выводим таблицу результатов
    print("\nРезультаты анализа:")
    print("-" * 80)
    print(f"{'Размер буфера':>15} | {'Степень сжатия':>15} | {'Экономия места':>15} | {'Время (сек)':>12}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['buffer_size']/1024:>12.1f} KB | "
              f"{r['ratio']:>15.3f} | "
              f"{r['saving']:>14.1f}% | "
              f"{r['time']:>12.3f}")
    
    print("-" * 80)
    print(f"\nОптимальный размер буфера: {optimal_result['buffer_size']/1024:.1f} KB")
    print(f"Степень сжатия: {optimal_result['ratio']:.3f}")
    print(f"Экономия места: {optimal_result['saving']:.1f}%")
    print(f"Время сжатия: {optimal_result['time']:.3f} сек")

if __name__ == "__main__":
    # Анализируем файл enwik7
    if not os.path.exists('enwik7'):
        print("Ошибка: файл enwik7 не найден!")
    else:
        analyze_buffer_sizes('enwik7') 