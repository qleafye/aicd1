import numpy as np
import heapq
import time
import math
import os
import queue
from collections import defaultdict

# Размер блока (200 КБ)
BLOCK_SIZE = 200 * 1024


class Node():
    def __init__(self, symbol=None, counter=None, left=None, right=None, parent=None):
        self.symbol = symbol
        self.counter = counter
        self.left = left
        self.right = right
        self.parent = parent

    def __lt__(self, other):
        return self.counter < other.counter


# Функции для BWT
def bwt_transform(data: bytes, chunk_size: int = 1024) -> tuple[bytes, list[int]]:
    transformed_data = bytearray()
    indices = []
    for start in range(0, len(data), chunk_size):
        chunk = data[start:start + chunk_size]
        index, encoded_chunk = transform_chunk(chunk)
        transformed_data.extend(encoded_chunk)
        indices.append(index)
    return bytes(transformed_data), indices


def transform_chunk(chunk: bytes) -> tuple[int, bytes]:
    rotations = [chunk[i:] + chunk[:i] for i in range(len(chunk))]
    rotations.sort()
    original_index = rotations.index(chunk)
    encoded_chunk = bytes(rotation[-1] for rotation in rotations)
    return original_index, encoded_chunk


def bwt_inverse(transformed_data: bytes, indices: list[int], chunk_size: int = 1024) -> bytes:
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
    table = [(char, idx) for idx, char in enumerate(encoded_chunk)]
    table.sort()
    result = bytearray()
    current_row = original_index
    for _ in range(len(encoded_chunk)):
        char, current_row = table[current_row]
        result.append(char)
    return bytes(result)


# Функции для MTF
def mtf_transform(data: bytes) -> bytes:
    alphabet = list(range(256))
    transformed_data = bytearray()
    for byte in data:
        index = alphabet.index(byte)
        transformed_data.append(index)
        alphabet.pop(index)
        alphabet.insert(0, byte)
    return bytes(transformed_data)


def mtf_inverse(transformed_data: bytes) -> bytes:
    alphabet = list(range(256))
    original_data = bytearray()
    for index in transformed_data:
        byte = alphabet[index]
        original_data.append(byte)
        alphabet.pop(index)
        alphabet.insert(0, byte)
    return bytes(original_data)


# Функции для RLE с битовыми флагами
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
            compressed.append(0x80 | count)
            compressed.append(current)
            i += count
        else:
            seq = bytearray()
            seq.append(current)
            i += 1
            while i < n and len(seq) < 127 and (i >= n - 1 or data[i] != data[i + 1]):
                seq.append(data[i])
                i += 1
            compressed.append(len(seq))
            compressed.extend(seq)
    return bytes(compressed)


def rle_decompress(compressed_data: bytes) -> bytes:
    decompressed = bytearray()
    i = 0
    n = len(compressed_data)
    while i < n:
        header = compressed_data[i]
        i += 1

        if header & 0x80:
            count = header & 0x7F
            if i >= n:
                raise ValueError("Invalid RLE data")
            byte = compressed_data[i]
            i += 1
            decompressed.extend([byte] * count)
        else:
            length = header
            if i + length > n:
                raise ValueError("Invalid RLE data")
            decompressed.extend(compressed_data[i:i + length])
            i += length
    return bytes(decompressed)


def count_symb(data: bytes) -> np.ndarray:
    counter = np.zeros(256, dtype=int)
    for byte in data:
        counter[byte] += 1
    return counter

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

def read_huffman_codes(codes_file):
    huffman_codes = {}
    with open(codes_file, 'r') as f:
        for line in f:
            symbol, code = line.strip().split(':')
            huffman_codes[int(symbol)] = code
    return huffman_codes

def write_huffman_codes(huffman_codes, file_path):
    with open(file_path, 'w') as code_file:
        for symbol, code in huffman_codes.items():
            code_file.write(f"{symbol}:{code}\n")

def calculate_average_code_length(huffman_codes: dict, data: bytes) -> float:
    """
    Вычисляет среднюю длину кода Хаффмана.
    """
    counter = count_symb(data)
    total_symbols = len(data)
    total_length = 0.0

    for symbol, code in huffman_codes.items():
        probability = counter[symbol] / total_symbols
        total_length += probability * len(code)

    return total_length


def process_block(block: bytes) -> tuple[bytes, list[int], dict, float, float]:
    # BWT
    transformed_data, indices = bwt_transform(block)

    # MTF
    transformed_data = mtf_transform(transformed_data)

    # RLE
    transformed_data = rle_compress(transformed_data)

    # Huffman
    compressed_data, codes = huffman_compress(transformed_data)

    return compressed_data, indices, codes


def process_with_bwt_rle_mtf_ha(file_path, output_compressed, output_decompressed):
    start_time = time.time()

    with open(file_path, "rb") as f:
        data = f.read()
    original_size = len(data)
    print(f"Обработка файла {file_path}...")
    print(f"Исходный размер данных: {original_size} байт")

    block_count = 0

    with open(output_compressed, "wb") as compressed_file:
        with open(file_path, "rb") as f:
            block_number = 0
            while True:
                block = f.read(BLOCK_SIZE)
                if not block:
                    break

                compressed_block, indices, codes = process_block(block)
                block_count += 1

                compressed_file.write(block_number.to_bytes(4, 'big'))
                compressed_file.write(len(indices).to_bytes(4, 'big'))
                for index in indices:
                    compressed_file.write(index.to_bytes(4, 'big'))

                code_bytes = serialize_huffman_codes(codes)
                compressed_file.write(len(code_bytes).to_bytes(4, 'big'))
                compressed_file.write(code_bytes)

                compressed_file.write(len(compressed_block).to_bytes(4, 'big'))
                compressed_file.write(compressed_block)
                block_number += 1

    with open(output_compressed, "rb") as f:
        blocks = {}
        while True:
            block_number_bytes = f.read(4)
            if not block_number_bytes:
                break

            block_number = int.from_bytes(block_number_bytes, 'big')
            num_indices = int.from_bytes(f.read(4), 'big')
            indices = [int.from_bytes(f.read(4), 'big') for _ in range(num_indices)]

            code_size = int.from_bytes(f.read(4), 'big')
            code_bytes = f.read(code_size)
            codes = deserialize_huffman_codes(code_bytes)

            block_size = int.from_bytes(f.read(4), 'big')
            compressed_block = f.read(block_size)

            # Huffman декомпрессия
            decompressed_transformed = huffman_decompress(compressed_block, codes)

            # RLE декомпрессия
            decompressed_transformed = rle_decompress(decompressed_transformed)

            # MTF декомпрессия
            decompressed_transformed = mtf_inverse(decompressed_transformed)

            # BWT декомпрессия
            decompressed_data = bwt_inverse(decompressed_transformed, indices)
            blocks[block_number] = decompressed_data

    with open(output_decompressed, "wb") as decompressed_file:
        for block_number in sorted(blocks.keys()):
            decompressed_file.write(blocks[block_number])

   


    end_time = time.time()
    print("\n--- Результаты сжатия ---")
    end_time = time.time()
    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(output_compressed)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
    elapsed_time = end_time - start_time
    print(f"Исходный файл:      {file_path}")
    print(f"Алгоритм:           BWT + RLE")
    print(f"Размер исходный:    {format_size(original_size)}")
    print(f"Размер сжатый:      {format_size(compressed_size)}")
    print(f"Степень сжатия:     {compression_ratio:.3f}")
    print(f"Экономия места:     {(1 - compressed_size / original_size) * 100:.2f}%")
    print(f"Время сжатия:       {end_time - start_time:.3f} сек")
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




   


def serialize_huffman_codes(codes):
    serialized = bytearray()
    for char, code in codes.items():
        serialized.extend([char, len(code)])
        code_bytes = int(code, 2).to_bytes((len(code) + 7) // 8, 'big')
        serialized.append(len(code_bytes))
        serialized.extend(code_bytes)
    return bytes(serialized)


def deserialize_huffman_codes(code_bytes):
    codes = {}
    i = 0
    while i < len(code_bytes):
        char = code_bytes[i]
        code_len = code_bytes[i + 1]
        bytes_len = code_bytes[i + 2]
        i += 3

        code_int = int.from_bytes(code_bytes[i:i + bytes_len], 'big')
        code = bin(code_int)[2:].zfill(code_len)
        codes[char] = code
        i += bytes_len
    return codes


# Список файлов для обработки
file_paths = [
    "Это я - твой единственный зритель..txt",
    "bw_image.raw",
    "color_image.raw",
    "gray_image.raw",
    "enwik7",
    "binary_file.bin"
]
if __name__ == "__main__":
    print("--- Запуск BWT+RLE+MTF+HA ---")
        # Обработка каждого файла
    for file_path in file_paths:
        output_compressed = f"compressed files/BWT+RLE+MTF+HA/{file_path[:-4]}.bin"
        output_decompressed = f"decompressed files/BWT+RLE+MTF+HA/{file_path[:-4]}.bin"
        process_with_bwt_rle_mtf_ha(file_path, output_compressed, output_decompressed)

