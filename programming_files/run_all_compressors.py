import os
import time
from comp_LZ77_HA import process_file_with_lz77_huffman
from comp_BWT_RLE import process_file_in_blocks
from comp_LZ78 import process_file_with_lz78
from comp_LZ78_HA import process_file_with_lz78_huffman
from comp_LZ77 import process_file_with_lz77_optimized
from comp_LZ77_HA import process_file_with_lz77_huffman
from comp_RLE import process_file_nontext_1
from comp_HA import process_file_nontext_1
from comp_BWT_RLE_MTF_HA import process_with_bwt_rle_mtf_ha
# Импортируйте остальные алгоритмы по аналогии

def format_size(size_in_bytes):
    """Форматирует размер в байтах в читаемый вид"""
    if size_in_bytes >= 1024 * 1024:
        return f"{size_in_bytes:,} байт ({size_in_bytes / (1024 * 1024):.1f} МБ)"
    elif size_in_bytes >= 1024:
        return f"{size_in_bytes:,} байт ({size_in_bytes / 1024:.1f} КБ)"
    else:
        return f"{size_in_bytes:,} байт"

def check_files_match(file1, file2):
    """Проверяет, совпадают ли два файла"""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        return f1.read() == f2.read()

# Список файлов для обработки
file_paths = [
    "binary_file.bin",
    "bw_image.raw",
    "gray_image.raw",
    "color_image.raw",
    "enwik7",
    "Это я - твой единственный зритель..txt"
]

# Список алгоритмов и их директорий
algorithms = [
    {
        'name': 'LZ77+HA',
        'function': process_file_with_lz77_huffman,
        'dir': 'LZ77+HA'
    },
    {
        'name': 'BWT+RLE',
        'function': process_file_in_blocks,
        'dir': 'BWT+RLE'
    },
    {
        'name': 'LZ78+HA',
        'function': process_file_with_lz78_huffman,
        'dir': 'LZ78+HA'
    },
    {
        'name': 'LZ78',
        'function': process_file_with_lz78,
        'dir': 'LZ78'   
    },
    {
        'name': 'LZ77',
        'function': process_file_with_lz77_optimized,
        'dir': 'LZ77'
    },
    {
        'name': 'RLE',
        'function': process_file_nontext_1,
        'dir': 'RLE'
    },
    {
        'name': 'HA',
        'function': process_file_nontext_1,
        'dir': 'HA'
    },
    {
        'name': 'BWT+RLE+MTF+HA',
        'function': process_with_bwt_rle_mtf_ha,
        'dir': 'BWT+RLE+MTF+HA'
    }     
    
]

# Создаем базовые директории
base_compressed_dir = "C:/Users/alexe/Desktop/uni/сем4/aicd1/compressed files"
base_decompressed_dir = "C:/Users/alexe/Desktop/uni/сем4/aicd1/decompressed files"

# Создаем директории для каждого алгоритма
for algo in algorithms:
    compressed_dir = f"{base_compressed_dir}/{algo['dir']}"
    decompressed_dir = f"{base_decompressed_dir}/{algo['dir']}"
    os.makedirs(compressed_dir, exist_ok=True)
    os.makedirs(decompressed_dir, exist_ok=True)

# Создаем словарь для хранения результатов
results = {file_path: [] for file_path in file_paths}

# Запускаем все алгоритмы для всех файлов и собираем результаты
for algo in algorithms:
    print(f"\n=== Запуск {algo['name']} ===")
    for file_path in file_paths:
        output_compressed = f"{base_compressed_dir}/{algo['dir']}/{file_path[:-4]}.bin"
        output_decompressed = f"{base_decompressed_dir}/{algo['dir']}/{file_path[:-4]}.bin"
        print(f"\nОбработка файла {file_path}...")
        
        # Замеряем время
        start_time = time.time()
        algo['function'](file_path, output_compressed, output_decompressed)
        elapsed_time = time.time() - start_time
        
        # Собираем статистику
        original_size = os.path.getsize(file_path)
        compressed_size = os.path.getsize(output_compressed)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        space_saving = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        # Сохраняем результаты
        results[file_path].append({
            'algorithm': algo['name'],
            'compressed_size': compressed_size,
            'ratio': compression_ratio,
            'saving': space_saving,
            'time': elapsed_time
        })

# Выводим сравнительную таблицу для каждого файла
for file_path in file_paths:
    original_size = os.path.getsize(file_path)
    print(f"\n--- Сравнение алгоритмов сжатия для файла: {file_path} ({format_size(original_size)}) ---\n")
    print("| Алгоритм          | Размер сжатый        | Степень сжатия | Экономия места (%) | Время сжатия (сек) |")
    print("|-------------------|---------------------|----------------|-------------------|-------------------|")
    
    # Сортируем алгоритмы по степени сжатия
    file_results = sorted(results[file_path], key=lambda x: x['ratio'], reverse=True)
    
    for result in file_results:
        print(f"| {result['algorithm']:<17} | {format_size(result['compressed_size']):<19} | "
              f"{result['ratio']:>14.3f} | {result['saving']:>17.2f} | {result['time']:>17.3f} |")
    print("\n" + "=" * 90)

print("\nВсе алгоритмы завершили работу!") 