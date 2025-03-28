import time
import os

# Функция для кодирования данных с помощью алгоритма LZ78
def lz78_encode(data: bytes) -> bytes:
    dictionary = {b'': 0}  # Инициализация словаря с пустой строкой
    current_string = b''
    encoded_data = bytearray()

    for byte in data:
        new_string = current_string + bytes([byte])
        if new_string in dictionary:
            current_string = new_string
        else:
            # Используем 4 байта для индекса
            encoded_data.extend(dictionary[current_string].to_bytes(4, 'big'))  # Индекс текущей строки
            encoded_data.append(byte)  # Новый символ
            dictionary[new_string] = len(dictionary)  # Добавляем новую строку в словарь
            current_string = b''

    if current_string:
        # Используем 4 байта для индекса
        encoded_data.extend(dictionary[current_string].to_bytes(4, 'big'))  # Индекс последней строки

    return bytes(encoded_data)

# Функция для декодирования данных с помощью алгоритма LZ78
def lz78_decode(encoded_data: bytes) -> bytes:
    dictionary = {0: b''}  # Инициализация словаря с пустой строкой
    decoded_data = bytearray()
    i = 0

    while i < len(encoded_data):
        # Чтение индекса (4 байта)
        index = int.from_bytes(encoded_data[i:i + 4], 'big')
        i += 4
        if i < len(encoded_data):
            byte = encoded_data[i]  # Чтение нового символа
            i += 1
        else:
            byte = None

        if index in dictionary:
            string = dictionary[index]
            if byte is not None:
                new_string = string + bytes([byte])
                dictionary[len(dictionary)] = new_string
                decoded_data.extend(new_string)
            else:
                decoded_data.extend(string)
        else:
            raise ValueError("Некорректный индекс в закодированных данных")

    return bytes(decoded_data)

# Функция для обработки файла с использованием LZ78
def process_file_with_lz78(file_path, output_compressed, output_decompressed):
    start_time = time.time()

    # Чтение исходных данных
    with open(file_path, "rb") as f:
        data = f.read()
    original_size = len(data)
    print(f"Исходный размер данных: {original_size} байт")

    # Сжатие данных с использованием LZ78
    compressed_bytes = lz78_encode(data)
    compressed_size = len(compressed_bytes)
    print(f"Размер сжатых данных: {compressed_size} байт")

    # Запись сжатых данных
    with open(output_compressed, "wb") as file:
        file.write(compressed_bytes)

    # Чтение сжатых данных и декомпрессия
    with open(output_compressed, "rb") as f:
        compressed_data = f.read()

    decompressed_data = lz78_decode(compressed_data)

    # Запись декомпрессированных данных
    with open(output_decompressed, "wb") as file:
        file.write(decompressed_data)

    end_time = time.time()
    print("\n--- Результаты сжатия ---")
    end_time = time.time()
    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(output_compressed)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
    elapsed_time = end_time - start_time
    print(f"Исходный файл:      {file_path}")
    print(f"Алгоритм:           LZ77 + Хаффман")
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
    "binary_file.bin",
        "bw_image.raw",
        "gray_image.raw",
        "color_image.raw",
        "enwik7"
]

if __name__ == "__main__":
    print("--- Запуск LZ78 ---")
# Обработка каждого файла
    for file_path in file_paths:
        output_compressed = f"compressed files/LZ78/{file_path[:-4]}.bin"
        output_decompressed = f"decompressed files/LZ78/{file_path[:-4]}.bin"
        print(f"Обработка файла {file_path}...")
        process_file_with_lz78(file_path, output_compressed, output_decompressed)