import time

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
    decompressed_size = len(decompressed_data)
    print(f"Размер после декомпрессии: {decompressed_size} байт")

    # Вычисление коэффициента сжатия
    compression_ratio = original_size / compressed_size
    print(f"Коэффициент сжатия: {compression_ratio:.2f}")

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
    output_compressed = f"compressed files/LZ78/{file_path[:-4]}.bin"
    output_decompressed = f"decompressed files/LZ78/{file_path[:-4]}.bin"
    print(f"Обработка файла {file_path}...")
    process_file_with_lz78(file_path, output_compressed, output_decompressed)