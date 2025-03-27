import numpy as np
import queue
import time
import math


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


# Функция для вычисления энтропии данных
def calculate_entropy(data: bytes) -> float:
    counter = count_symb(data)
    total_symbols = len(data)
    entropy = 0.0

    for count in counter:
        if count > 0:
            probability = count / total_symbols
            entropy -= probability * math.log2(probability)

    return entropy


# Функция для вычисления средней длины кода Хаффмана
def calculate_average_code_length(huffman_codes: dict, data: bytes) -> float:
    counter = count_symb(data)
    total_symbols = len(data)
    total_length = 0.0

    for symbol, code in huffman_codes.items():
        probability = counter[symbol] / total_symbols
        total_length += probability * len(code)

    return total_length


# Функция для сжатия данных с использованием LZ78 и Хаффмана
def lz78_huffman_compress(data: bytes) -> bytes:
    # Сжатие данных с помощью LZ78
    lz78_encoded_data = lz78_encode(data)

    # Сжатие результата LZ78 с помощью Хаффмана
    huffman_compressed_data, huffman_codes = huffman_compress(lz78_encoded_data)

    return huffman_compressed_data, huffman_codes


# Функция для декомпрессии данных с использованием LZ78 и Хаффмана
def lz78_huffman_decompress(compressed_data: bytes, huffman_codes: dict) -> bytes:
    # Декомпрессия Хаффмана
    huffman_decompressed_data = huffman_decompress(compressed_data, huffman_codes)

    # Декомпрессия LZ78
    lz78_decoded_data = lz78_decode(huffman_decompressed_data)

    return lz78_decoded_data


# Функция для обработки файла с использованием LZ78 и Хаффмана
def process_file_with_lz78_huffman(file_path, output_compressed, output_decompressed):
    start_time = time.time()

    # Чтение исходных данных
    with open(file_path, "rb") as f:
        data = f.read()
    original_size = len(data)
    print(f"Исходный размер данных: {original_size} байт")

    # Сжатие данных с использованием LZ78 и Хаффмана
    compressed_bytes, huffman_codes = lz78_huffman_compress(data)
    compressed_size = len(compressed_bytes)
    print(f"Размер сжатых данных: {compressed_size} байт")

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
    decompressed_data = lz78_huffman_decompress(compressed_data, huffman_codes)
    decompressed_size = len(decompressed_data)
    print(f"Размер после декомпрессии: {decompressed_size} байт")

    # Вычисление коэффициента сжатия
    compression_ratio = original_size / compressed_size
    print(f"Коэффициент сжатия: {compression_ratio:.2f}")

    # Вычисление энтропии и средней длины кода
    entropy = calculate_entropy(data)
    avg_code_length = calculate_average_code_length(huffman_codes, data)
    print(f"Энтропия: {entropy:.2f} бит/символ")
    print(f"Средняя длина кода: {avg_code_length:.2f} бит/символ \n")

    # Запись декомпрессированных данных
    with open(output_decompressed, "wb") as file:
        file.write(decompressed_data)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Время выполнения: {elapsed_time:.2f} секунд \n")


# Список файлов для обработки
file_paths = [
    "binary_file.bin",
        "bw_image.raw",
        "grayscale_image.raw",
        "color_image.raw",
        "enwik7"
]

# Обработка каждого файла
for i, file_path in enumerate(file_paths):
    output_compressed = f"compressed files/LZ78+HA/{file_path[:-4]}.bin"
    output_decompressed = f"decompressed files/LZ78+HA/{file_path[:-4]}.bin"
    print(f"Обработка файла {file_path}...")
    process_file_with_lz78_huffman(file_path, output_compressed, output_decompressed)