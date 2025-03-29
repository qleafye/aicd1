import numpy as np
import queue
import time
import math
import os

# Создаем директории, если они не существуют
compressed_dir = "C:/Users/alexe/Desktop/uni/сем4/aicd1/compressed files/LZ77+HA"
decompressed_dir = "C:/Users/alexe/Desktop/uni/сем4/aicd1/decompressed files/LZ77+HA"

os.makedirs(compressed_dir, exist_ok=True)
os.makedirs(decompressed_dir, exist_ok=True)

# Класс для узла дерева Хаффмана
class Node():
    def __init__(self, symbol=None, counter=None, left=None, right=None, parent=None):
        self.symbol = symbol
        self.counter = counter
        self.left = left
        self.right = right
        self.parent = parent

    def __lt__(self, other):
        return self.counter < other.counter


# Функция для подсчета частоты символов
def count_symb(data: bytes) -> np.ndarray:
    counter = np.zeros(256, dtype=int)
    for byte in data:
        counter[byte] += 1
    return counter


# Функция для сжатия данных с помощью алгоритма Хаффмана
def huffman_compress(data: bytes) -> bytes:
    C = count_symb(data)
    list_of_leafs = []
    Q = queue.PriorityQueue()

    for i in range(256):
        if C[i] != 0:
            leaf = Node(symbol=i, counter=C[i])
            list_of_leafs.append(leaf)
            Q.put(leaf)

    while Q.qsize() >= 2:
        left_node = Q.get()
        right_node = Q.get()
        parent_node = Node(left=left_node, right=right_node)
        left_node.parent = parent_node
        right_node.parent = parent_node
        parent_node.counter = left_node.counter + right_node.counter
        Q.put(parent_node)

    codes = {}
    for leaf in list_of_leafs:
        node = leaf
        code = ""
        while node.parent is not None:
            if node.parent.left == node:
                code = "0" + code
            else:
                code = "1" + code
            node = node.parent
        codes[leaf.symbol] = code

    coded_message = ""
    for byte in data:
        coded_message += codes[byte]

    padding = 8 - len(coded_message) % 8
    coded_message += '0' * padding
    coded_message = f"{padding:08b}" + coded_message

    bytes_string = bytearray()
    for i in range(0, len(coded_message), 8):
        byte = coded_message[i:i + 8]
        bytes_string.append(int(byte, 2))

    return bytes(bytes_string), codes


# Функция для декомпрессии данных с помощью алгоритма Хаффмана
def huffman_decompress(compressed_data: bytes, huffman_codes: dict) -> bytes:
    padding = compressed_data[0]
    coded_message = ""
    for byte in compressed_data[1:]:
        coded_message += f"{byte:08b}"

    if padding > 0:
        coded_message = coded_message[:-padding]

    reverse_codes = {v: k for k, v in huffman_codes.items()}
    current_code = ""
    decoded_data = bytearray()

    for bit in coded_message:
        current_code += bit
        if current_code in reverse_codes:
            decoded_data.append(reverse_codes[current_code])
            current_code = ""

    return bytes(decoded_data)


# Функция для кодирования данных с помощью алгоритма LZ77
def lz77_encode(data: bytes, buffer_size: int) -> bytes:
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
        for length in range(min(255, n - i), 0, -1):
            substring = data[i:i + length]
            offset = data[search_start:search_end].rfind(substring)
            if offset != -1:
                max_length = length
                max_offset = search_end - search_start - offset
                break

        if max_length > 0:
            # Кодируем offset и length в два байта каждый
            encoded_data.append((max_offset >> 8) & 0xFF)  # Старший байт offset
            encoded_data.append(max_offset & 0xFF)  # Младший байт offset
            encoded_data.append((max_length >> 8) & 0xFF)  # Старший байт length
            encoded_data.append(max_length & 0xFF)  # Младший байт length
            i += max_length
        else:
            # Если совпадений нет, кодируем как символ
            encoded_data.append(0)  # offset = 0 (старший байт)
            encoded_data.append(0)  # offset = 0 (младший байт)
            encoded_data.append(0)  # length = 0 (старший байт)
            encoded_data.append(0)  # length = 0 (младший байт)
            encoded_data.append(data[i])  # символ (1 байт)
            i += 1

    return bytes(encoded_data)


def lz77_decode(encoded_data: bytes) -> bytes:
    decoded_data = bytearray()
    i = 0
    n = len(encoded_data)

    while i < n:
        # Читаем offset и length (по два байта каждый)
        offset = (encoded_data[i] << 8) | encoded_data[i + 1]
        length = (encoded_data[i + 2] << 8) | encoded_data[i + 3]
        i += 4

        if offset == 0 and length == 0:
            # Это символ
            decoded_data.append(encoded_data[i])
            i += 1
        else:
            # Это ссылка
            start = len(decoded_data) - offset
            end = start + length
            decoded_data.extend(decoded_data[start:end])

    return bytes(decoded_data)


# Функция для чтения кодов Хаффмана из файла
def read_huffman_codes(codes_file):
    huffman_codes = {}
    with open(codes_file, 'r') as f:
        for line in f:
            symbol, code = line.strip().split(':')
            huffman_codes[int(symbol)] = code
    return huffman_codes


# Функция для записи кодов Хаффмана в файл
def write_huffman_codes(huffman_codes, file_path):
    with open(file_path, 'w') as code_file:
        for symbol, code in huffman_codes.items():
            code_file.write(f"{symbol}:{code}\n")




# Функция для вычисления средней длины кода Хаффмана
def calculate_average_code_length(huffman_codes: dict, data: bytes) -> float:
    counter = count_symb(data)
    total_symbols = len(data)
    total_length = 0.0

    for symbol, code in huffman_codes.items():
        probability = counter[symbol] / total_symbols
        total_length += probability * len(code)

    return total_length


# Функция для сжатия данных с использованием LZ77 и Хаффмана
def lz77_huffman_compress(data: bytes, buffer_size: int) -> bytes:
    # Сжатие данных с помощью LZ77
    lz77_encoded_data = lz77_encode(data, buffer_size)

    # Сжатие результата LZ77 с помощью Хаффмана
    huffman_compressed_data, huffman_codes = huffman_compress(lz77_encoded_data)

    return huffman_compressed_data, huffman_codes


# Функция для декомпрессии данных с использованием LZ77 и Хаффмана
def lz77_huffman_decompress(compressed_data: bytes, huffman_codes: dict) -> bytes:
    # Декомпрессия Хаффмана
    huffman_decompressed_data = huffman_decompress(compressed_data, huffman_codes)

    # Декомпрессия LZ77
    lz77_decoded_data = lz77_decode(huffman_decompressed_data)

    return lz77_decoded_data


# Функция для обработки файла с использованием LZ77 и Хаффмана
def process_file_with_lz77_huffman(file_path, output_compressed, output_decompressed, buffer_size=1024):
    start_time = time.time()

    # Чтение исходных данных
    with open(file_path, "rb") as f:
        data = f.read()

    # Сжатие данных с использованием LZ77 и Хаффмана
    compressed_bytes, huffman_codes = lz77_huffman_compress(data, buffer_size)

    # Запись сжатых данных и кодов Хаффмана
    with open(output_compressed, "wb") as file:
        file.write(compressed_bytes)

    with open(output_compressed + '_codes', 'w') as code_file:
        for symbol, code in huffman_codes.items():
            code_file.write(f"{symbol}:{code}\n")

    # Чтение сжатых данных и декомпрессия
    with open(output_compressed, "rb") as f:
        compressed_data = f.read()

    huffman_codes = read_huffman_codes(output_compressed + '_codes')
    decompressed_data = lz77_huffman_decompress(compressed_data, huffman_codes)
    
    # Добавляем запись декомпрессированных данных
    with open(output_decompressed, "wb") as f:
        f.write(decompressed_data)

    decompressed_size = len(decompressed_data)
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
    print("--- Запуск LZ77+HA ---")
# Обработка каждого файла
    for file_path in file_paths:
        output_compressed = f"{compressed_dir}/{file_path[:-4]}.bin"
        output_decompressed = f"{decompressed_dir}/{file_path[:-4]}.bin"
        print(f"Обработка файла {file_path}...")
        process_file_with_lz77_huffman(file_path, output_compressed, output_decompressed)