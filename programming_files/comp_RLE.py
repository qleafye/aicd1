import numpy as np
import time
import math
import os
import sys
# --- Вспомогательные функции ---

def count_symb(data: bytes) -> np.ndarray:
    """
    Подсчитывает частоту символов в данных.
    """
    counter = np.zeros(256, dtype=int)
    for byte in data:
        counter[byte] += 1
    return counter

def calculate_entropy(data: bytes) -> float:
    """
    Вычисляет энтропию данных по формуле Шеннона.
    """
    if not data: # Обработка пустого ввода
        return 0.0
    counter = count_symb(data)
    total_symbols = len(data)
    entropy = 0.0

    for count in counter:
        if count > 0:
            probability = count / total_symbols
            # Избегаем log2(0) - это не должно происходить при count > 0, но для надежности
            if probability > 0:
                entropy -= probability * math.log2(probability)

    return entropy

def calculate_average_code_length(data: bytes, compressed_data: bytes) -> float:
    """
    Вычисляет среднюю длину кода.
    """
    total_symbols = len(data)
    if total_symbols == 0: # Обработка пустого ввода
        return 0.0
    total_compressed_bytes = len(compressed_data)
    # Средняя длина кода в битах на ИСХОДНЫЙ символ
    return (total_compressed_bytes * 8) / total_symbols

# --- PackBits RLE Реализация ---

def packbits_rle_compress(data: bytes) -> bytes:
    """
    Сжимает данные с использованием PackBits-подобного RLE.
    Управляющий байт N:
    - 0 <= N <= 127: Следующие N+1 байт - литералы (копируются как есть).
    - 129 <= N <= 255: Следующий байт повторить 258-N раз (для длин от 3 до 128).
    - N = 128: Зарезервировано (здесь игнорируется/не используется при кодировании).
    """
    compressed_data = bytearray()
    n = len(data)
    i = 0
    MAX_LEN = 128 # Макс. длина для одного блока литералов (N+1) или повторов (258-N -> до 128 раз)

    while i < n:
        # Вывод прогресса для долгих операций


        # 1. Ищем последовательность повторов
        repeat_count = 1
        # Ищем повторы (нужно хотя бы 3 для кодирования как повтор)
        # Ограничиваем максимальную длину повтора значением MAX_LEN (128)
        while (i + repeat_count < n and
               data[i + repeat_count] == data[i] and
               repeat_count < MAX_LEN):
            repeat_count += 1

        # ИЗМЕНЕНИЕ ЗДЕСЬ: Кодируем как повтор только если длина 3 или больше
        if repeat_count >= 3:
            # Нашли повтор. Кодируем его.
            # Управляющий байт: 258 - repeat_count (будет в диапазоне [130, 255])
            control_byte = 258 - repeat_count
            compressed_data.append(control_byte)
            compressed_data.append(data[i]) # Байт для повторения
            i += repeat_count # Продвигаем индекс

        else:
            # 2. Не нашли повтор >= 3, значит ищем последовательность литералов
            literal_start = i
            # Ищем конец последовательности литералов. Останавливаемся, если:
            # - Достигли конца данных
            # - Нашли 3 одинаковых байта подряд (это будет начало следующего повтора) - ИЗМЕНЕНО УСЛОВИЕ
            # - Достигли максимальной длины для литералов (MAX_LEN)
            i += 1 # Начинаем проверку со следующего байта
            while i < n:
                 # Проверяем, не превысили ли максимальную длину литералов
                 if i - literal_start >= MAX_LEN:
                      break

                 # Проверяем, не начинается ли последовательность повторов из 3х символов
                 if (i + 1 < n and data[i] == data[i+1] and # Нашли два подряд
                     i > literal_start and data[i] == data[i-1]): # и предыдущий такой же (т.е. три подряд)
                      # Нашли начало повтора из 3х, останавливаем литералы ПЕРЕД ним
                      i -= 1 # Возвращаемся на один символ назад, чтобы он не попал в литералы
                      break

                 # Если дошли до конца файла, текущий символ - последний литерал
                 if i == n - 1:
                      i += 1 # Продвигаем i за конец, чтобы включить последний символ
                      break

                 # Если просто два одинаковых подряд (AA) - это еще не повод останавливать литералы
                 # (так как мы кодируем повторы только от 3х)
                 # if i + 1 < n and data[i] == data[i+1]:
                 #      pass # Просто продолжаем, AA пойдут как литералы

                 # Если текущий и следующий разные - продолжаем литералы
                 if i + 1 < n and data[i] != data[i+1]:
                      i += 1
                      continue

                 # Если i+1 >= n (конец файла) - выходим из внутреннего while после этой итерации
                 # но нужно убедиться что i увеличился

                 # Попали сюда, если i+1 < n и data[i] == data[i+1].
                 # Мы не вышли по условию "3 подряд", значит это только 2 подряд.
                 # Продолжаем искать литералы, включая эту пару.
                 i += 1


            # Определяем длину найденной последовательности литералов
            literal_len = i - literal_start

            if literal_len > 0:
                # Кодируем литералы.
                # Управляющий байт: literal_len - 1 (будет в диапазоне [0, 127])
                control_byte = literal_len - 1
                compressed_data.append(control_byte)
                compressed_data.extend(data[literal_start : i]) # Добавляем сами литералы
            # i уже указывает на байт после литералов (или на конец данных)

    # print() # Убрал дублирующуюся новую строку
    return bytes(compressed_data)

def packbits_rle_decompress(compressed_data: bytes) -> bytes:
    """
    Декомпрессия данных, сжатых PackBits-подобным RLE.
    """
    decompressed_data = bytearray()
    n = len(compressed_data)
    i = 0

    while i < n:

        control_byte = compressed_data[i]
        i += 1

        if control_byte <= 127:
            # Литералы: control_byte = N, длина = N + 1
            length = control_byte + 1
            if i + length > n:
                 raise ValueError(f"Ошибка данных: недостаточно байт для литеральной последовательности. Индекс: {i}, нужно: {length}, доступно: {n-i}")
            decompressed_data.extend(compressed_data[i : i + length])
            i += length
        elif control_byte >= 129:
            # Повторы: control_byte = N, длина = 258 - N
            count = 258 - control_byte # count будет от 3 до 129
            if i >= n:
                 raise ValueError(f"Ошибка данных: отсутствует байт значения для повторяющейся последовательности. Индекс: {i}")
            byte_to_repeat = compressed_data[i]
            decompressed_data.extend([byte_to_repeat] * count)
            i += 1
        else: # control_byte == 128
             # В стандарте PackBits байт 128 ('80' hex) игнорируется (No-Op)
             # print(f"Decompress No-Op: control={control_byte}, next_byte_idx={i}")
             pass

    sys.stdout.flush()
    print() # Новая строка после прогресс-бара
    return bytes(decompressed_data)

# --- Функция обработки файла ---

def process_file_nontext_1(file_path, output_compressed, output_decompressed):
    # Начало измерения времени
    start_time = time.time()

    # Чтение исходных данных
    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден - {file_path}\n")
        return
    except Exception as e:
        print(f"Ошибка чтения файла {file_path}: {e}\n")
        return



    # Сжатие данных
    try:
        compressed_bytes = packbits_rle_compress(data)
    except Exception as e:
        print(f"Ошибка во время сжатия файла {file_path}: {e}")
        return # Прерываем обработку этого файла

    # Создание директорий, если их нет
    try:
        os.makedirs(os.path.dirname(output_compressed), exist_ok=True)
        os.makedirs(os.path.dirname(output_decompressed), exist_ok=True)
    except Exception as e:
         print(f"Ошибка создания директорий: {e}")
         return # Не можем продолжать без директорий

    # Запись сжатых данных
    try:
        with open(output_compressed, "wb") as file:
            file.write(compressed_bytes)
    except Exception as e:
        print(f"Ошибка записи сжатого файла {output_compressed}: {e}")
        return

    # Чтение сжатых данных и декомпрессия
    try:
        with open(output_compressed, "rb") as f:
            compressed_data_read = f.read()
    except Exception as e:
        print(f"Ошибка чтения сжатого файла {output_compressed}: {e}")
        return

    decompressed_data = b"" # Инициализация на случай ошибки
    try:
        decompressed_data = packbits_rle_decompress(compressed_data_read)
    except ValueError as e:
        print(f"Ошибка декомпрессии файла {output_compressed}: {e}")
        # Записываем пустой файл или маркер ошибки
        try:
            with open(output_decompressed, "wb") as file:
                # file.write(b"DECOMPRESSION_ERROR")
                file.write(b"") # Или просто пустой файл
        except Exception as we:
            print(f"Ошибка записи файла ошибки декомпрессии {output_decompressed}: {we}")
        # Продолжаем для вывода статистики, но проверка данных не пройдет
    except Exception as e:
        print(f"Неожиданная ошибка во время декомпрессии {output_compressed}: {e}")
        try:
            with open(output_decompressed, "wb") as file:
                file.write(b"")
        except Exception as we:
             print(f"Ошибка записи файла ошибки декомпрессии {output_decompressed}: {we}")

    # Запись декомпрессированных данных (даже если была ошибка декомпрессии, запишется результат - пустой или неполный)
    try:
        with open(output_decompressed, "wb") as file:
            file.write(decompressed_data)
    except Exception as e:
        print(f"Ошибка записи декомпрессированного файла {output_decompressed}: {e}")
        # Статистику все равно выведем



  
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



# --- Основной блок выполнения ---


    # Список файлов для обработки (убедись, что они лежат рядом со скриптом или укажи полные пути)
file_paths = [
        "binary_file.bin",
        "bw_image.raw",
        "grayscale_image.raw",
        "color_image.raw",
        "enwik7"
        # Добавь другие файлы при необходимости
    ]



print("--- Запуск PackBits RLE ---")
for i, file_path in enumerate(file_paths):
    output_compressed = f"compressed files/RLE/{file_path[:-4]}.bin"
    output_decompressed = f"decompressed files/RLE/{file_path[:-4]}.bin"
    print(f"Обработка файла {file_path}...")
    process_file_nontext_1(file_path, output_compressed, output_decompressed)