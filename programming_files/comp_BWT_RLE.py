import time
import math
import os

# Создаем директории, если они не существуют
compressed_dir = "C:/Users/alexe/Desktop/uni/сем4/aicd1/compressed files/BWT+RLE"
decompressed_dir = "C:/Users/alexe/Desktop/uni/сем4/aicd1/decompressed files/BWT+RLE"

os.makedirs(compressed_dir, exist_ok=True)
os.makedirs(decompressed_dir, exist_ok=True)

# Размер блока (64 КБ)
BLOCK_SIZE = 64 * 1024

def bwt_transform(data: bytes, chunk_size: int = 1024) -> tuple[bytes, list[int]]:
    """
    Применяет преобразование Барроуза-Уилера к данным с разбиением на чанки.
    """
    transformed_data = bytearray()
    indices = []
    for start in range(0, len(data), chunk_size):
        chunk = data[start:start + chunk_size]
        index, encoded_chunk = transform_chunk(chunk)
        transformed_data.extend(encoded_chunk)
        indices.append(index)
    return bytes(transformed_data), indices

def transform_chunk(chunk: bytes) -> tuple[int, bytes]:
    """
    Преобразует один чанк данных с помощью BWT.
    """
    rotations = [chunk[i:] + chunk[:i] for i in range(len(chunk))]
    rotations.sort()
    original_index = rotations.index(chunk)
    encoded_chunk = bytes(rotation[-1] for rotation in rotations)
    return original_index, encoded_chunk

def bwt_inverse(transformed_data: bytes, indices: list[int], chunk_size: int = 1024) -> bytes:
    """
    Обратное преобразование Барроуза-Уилера с разбиением на чанки.
    """
    restored_data = bytearray()
    position = 0
    index = 0
    while position < len(transformed_data):
        end = position + chunk_size if position + chunk_size <= len(transformed_data) else len(transformed_data)
        chunk = transformed_data[position:end]
        original_index = indices[index]
        restored_chunk = reverse_transform_chunk(original_index, chunk)
        restored_data.extend(restored_chunk)
        position = end
        index += 1
    return bytes(restored_data)

def reverse_transform_chunk(original_index: int, encoded_chunk: bytes) -> bytes:
    """
    Обратное преобразование BWT для одного чанка.
    """
    table = [(char, idx) for idx, char in enumerate(encoded_chunk)]
    table.sort()
    result = bytearray()
    current_row = original_index
    for _ in range(len(encoded_chunk)):
        char, current_row = table[current_row]
        result.append(char)
    return bytes(result)

def rle_compress(data: bytes) -> bytes:
    compressed = bytearray()
    i = 0
    n = len(data)
    while i < n:
        current = data[i]
        count = 1
        while i + count < n and count < 127 and data[i + count] == current:
            count += 1
        if count > 1:
            compressed.append(0x80 | count)  # Бит 7 = 1 для повторов
            compressed.append(current)
            i += count
        else:
            # Собираем неповторяющуюся последовательность
            seq = bytearray()
            seq.append(current)
            i += 1
            while i < n and len(seq) < 127 and (i >= n-1 or data[i] != data[i+1]):
                seq.append(data[i])
                i += 1
            compressed.append(len(seq))  # Бит 7 = 0
            compressed.extend(seq)
    return bytes(compressed)


def rle_decompress(compressed_data: bytes) -> bytes:
    decompressed = bytearray()
    i = 0
    n = len(compressed_data)
    while i < n:
        header = compressed_data[i]
        i += 1

        if header & 0x80:  # Если установлен бит 7 - это повтор
            count = header & 0x7F  # Получаем длину (биты 0-6)
            if i >= n:
                raise ValueError("Invalid RLE data: missing byte after repeat header")
            byte = compressed_data[i]
            i += 1
            decompressed.extend([byte] * count)
        else:  # Это последовательность неповторяющихся символов
            length = header
            if i + length > n:
                raise ValueError(f"Invalid RLE data: expected {length} bytes, got {n - i}")
            decompressed.extend(compressed_data[i:i + length])
            i += length
    return bytes(decompressed)

def process_block(block: bytes) -> tuple[bytes, list[int]]:
    """
    Обрабатывает блок данных: применяет BWT и RLE.
    Возвращает сжатые данные и индексы BWT.
    """
    transformed_data, indices = bwt_transform(block)
    compressed_data = rle_compress(transformed_data)
    return compressed_data, indices

def process_file_in_blocks(file_path, output_compressed, output_decompressed):
    # Начало измерения времени
    start_time = time.time()

    # Чтение исходных данных для вычисления энтропии
    with open(file_path, "rb") as f:
        data = f.read()
    original_size = len(data)
    print(f"Исходный размер данных: {original_size} байт")

    # Открываем файл для записи сжатых данных
    with open(output_compressed, "wb") as compressed_file:
        # Открываем файл для чтения и обработки блоков
        with open(file_path, "rb") as f:
            block_number = 0
            while True:
                block = f.read(BLOCK_SIZE)
                if not block:
                    break
                compressed_block, indices = process_block(block)
                # Записываем номер блока, количество индексов, индексы BWT и сжатые данные
                compressed_file.write(block_number.to_bytes(4, byteorder='big'))
                compressed_file.write(len(indices).to_bytes(4, byteorder='big'))
                for index in indices:
                    compressed_file.write(index.to_bytes(4, byteorder='big'))
                compressed_file.write(len(compressed_block).to_bytes(4, byteorder='big'))
                compressed_file.write(compressed_block)
                block_number += 1

    # Размер сжатых данных
    compressed_size = os.path.getsize(output_compressed)
    print(f"Размер сжатых данных: {compressed_size} байт")

    # Чтение сжатых данных и декомпрессия
    with open(output_compressed, "rb") as f:
        # Собираем блоки в словарь для восстановления порядка
        blocks = {}
        while True:
            # Читаем номер блока
            block_number_bytes = f.read(4)
            if not block_number_bytes:
                break
            block_number = int.from_bytes(block_number_bytes, byteorder='big')
            # Читаем количество индексов
            num_indices_bytes = f.read(4)
            num_indices = int.from_bytes(num_indices_bytes, byteorder='big')
            # Читаем индексы BWT
            indices = []
            for _ in range(num_indices):
                index_bytes = f.read(4)
                indices.append(int.from_bytes(index_bytes, byteorder='big'))
            # Читаем размер сжатого блока
            block_size_bytes = f.read(4)
            block_size = int.from_bytes(block_size_bytes, byteorder='big')
            # Читаем сжатые данные
            compressed_block = f.read(block_size)
            # Декомпрессия RLE
            decompressed_transformed_data = rle_decompress(compressed_block)
            # Обратное преобразование BWT
            decompressed_data = bwt_inverse(decompressed_transformed_data, indices)
            # Сохраняем блок в словаре
            blocks[block_number] = decompressed_data

        # Записываем блоки в правильном порядке
        with open(output_decompressed, "wb") as decompressed_file:
            for block_number in sorted(blocks.keys()):
                decompressed_file.write(blocks[block_number])

    # Размер после декомпрессии
    decompressed_size = os.path.getsize(output_decompressed)
 

    # Вычисление коэффициента сжатия
    compression_ratio = original_size / compressed_size


    # Конец измерения времени
    end_time = time.time()
    elapsed_time = end_time - start_time


    print("\n--- Результаты сжатия ---")
    print(f"Исходный файл:      {file_path}")
    print(f"Алгоритм:           BWT + RLE")
    print(f"Размер исходный:    {format_size(original_size)}")
    print(f"Размер сжатый:      {format_size(compressed_size)}")
    print(f"Степень сжатия:     {compression_ratio:.3f}")
    print(f"Экономия места:     {(1 - compressed_size / original_size) * 100:.2f}%")
    print(f"Время сжатия:       {elapsed_time:.3f} сек")
    print(f"Исходный и декомпрессированный файл совпадают: {'да' if check_files_match(file_path, output_decompressed) else 'нет'}")
    print("-" * 50)

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
            "Это я - твой единственный зритель..txt",
            "bw_image.raw",
            "color_image.raw",
            "gray_image.raw",
            "enwik7",
            "binary_file.bin"
]
print("--- Запуск BWT+RLE ---")
# Обработка каждого файла
for i, file_path in enumerate(file_paths):
    output_compressed = f"{compressed_dir}/{file_path[:-4]}.bin"
    output_decompressed = f"{decompressed_dir}/{file_path[:-4]}.bin"
    print(f"Обработка файла {file_path}...")
    process_file_in_blocks(file_path, output_compressed, output_decompressed)