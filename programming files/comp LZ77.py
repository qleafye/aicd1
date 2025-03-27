import os
import struct
import time
import sys
import traceback # Для отладки ошибок

# --- LZ77 Configuration ---

# Формат триплета: (offset, length, char), хранится в 3 байтах.
# 12 бит для offset, 4 бита для length, 8 бит для char.
# - Если offset=0 и length=0, 'char' - это литеральный байт.
# - Если offset > 0 и length >= MIN_MATCH_LENGTH, это ссылка на совпадение
#   длиной 'length', начинающееся 'offset' байт назад, а 'char' - это
#   литеральный байт, следующий СРАЗУ ЗА совпадением в исходных данных.

OFFSET_BITS = 12
LENGTH_BITS = 4
CHAR_BITS = 8

# Расчет размеров буферов на основе бит
# Макс. смещение (0 до 2^12 - 1 = 4095). 0 - спец. значение (литерал).
# Макс. реальное смещение назад = 4095.
SEARCH_BUFFER_SIZE = (1 << OFFSET_BITS) - 1

# Макс. длина (0 до 2^4 - 1 = 15). 0 - спец. значение (литерал).
# Возможные длины совпадений: MIN_MATCH_LENGTH до 15.
# LOOKAHEAD_BUFFER_SIZE определяет макс. совпадение, которое МОЖЕМ НАЙТИ.
# Должен быть не меньше макс. значения 'length'.
LOOKAHEAD_BUFFER_SIZE = (1 << LENGTH_BITS) - 1 # Макс. длина = 15

# Минимальная длина совпадения для кодирования как ссылки (offset, length)
# Более короткие совпадения кодируются как литералы. Обычно 2 или 3.
MIN_MATCH_LENGTH = 3

# Размер окна (для понимания, не используется прямо в ограничениях поиска)
WINDOW_SIZE = SEARCH_BUFFER_SIZE + LOOKAHEAD_BUFFER_SIZE # 4095 + 15 = 4110

# Формат для struct для упаковки/распаковки 3-байтного триплета
# '>': big-endian (порядок байт не зависит от платформы)
# 'H': unsigned short (16 бит для offset << 4 | length)
# 'B': unsigned char (8 бит для char)
PACK_FORMAT = '>HB'
PACK_SIZE = struct.calcsize(PACK_FORMAT) # Должно быть 3

def find_longest_match(data, cursor, search_buffer_limit, lookahead_limit):
    """
    Ищет самое длинное совпадение для данных, начиная с 'cursor',
    в пределах предыдущих 'search_buffer_limit' байт.
    Возвращает (offset, length). Макс. длина ограничена 'lookahead_limit'.
    """
    end_of_buffer = len(data)
    best_match_length = 0
    best_match_offset = 0

    # Границы буфера поиска
    search_start = max(0, cursor - search_buffer_limit)
    # search_end = cursor # Поиск до текущей позиции

    # Максимально возможная длина совпадения (ограничена lookahead и концом данных)
    max_possible_match_len = min(lookahead_limit, end_of_buffer - cursor)

    # Если данных осталось меньше, чем минимальная длина совпадения
    if max_possible_match_len < MIN_MATCH_LENGTH:
        return 0, 0

    # Итерация назад по буферу поиска для поиска начала совпадений
    # range [search_start, cursor) -> range(search_start, cursor)
    for i in range(search_start, cursor):
        current_match_length = 0
        # Сравнение байтов: data[i+k] vs data[cursor+k]
        while current_match_length < max_possible_match_len and \
              data[i + current_match_length] == data[cursor + current_match_length]:
            current_match_length += 1

        # Если текущее совпадение лучшее И удовлетворяет мин. длине
        if current_match_length >= MIN_MATCH_LENGTH and current_match_length > best_match_length:
            best_match_length = current_match_length
            best_match_offset = cursor - i # Смещение = расстояние назад от cursor

    # Если найдено подходящее совпадение
    if best_match_length >= MIN_MATCH_LENGTH:
         # Убедимся, что найденная длина не превышает кодируемый лимит
         best_match_length = min(best_match_length, lookahead_limit)
         return best_match_offset, best_match_length
    else:
         return 0, 0 # Подходящее совпадение не найдено

def encode(input_file_path, output_file_path):
    """Кодирует файл с использованием алгоритма LZ77."""
    print(f"Кодирование {input_file_path} в {output_file_path}...")
    start_time = time.time()
    input_size = 0
    output_size = 0
    success = False

    try:
        with open(input_file_path, 'rb') as infile, open(output_file_path, 'wb') as outfile:
            # Чтение всего файла в память.
            # ВНИМАНИЕ: Может вызвать MemoryError для очень больших файлов!
            data = infile.read()
            data_len = len(data)
            input_size = data_len
            cursor = 0

            while cursor < data_len:
                # Поиск самого длинного совпадения
                offset, length = find_longest_match(data, cursor, SEARCH_BUFFER_SIZE, LOOKAHEAD_BUFFER_SIZE)

                if length > 0: # Найдено подходящее совпадение
                    # Нужен байт, СЛЕДУЮЩИЙ за совпадением
                    next_char_pos = cursor + length
                    # Важная проверка: Убедиться, что СЛЕДУЮЩИЙ байт существует в данных
                    if next_char_pos < data_len:
                        next_char_code = data[next_char_pos]

                        # Упаковка (offset, length, next_char_code)
                        combined = (offset << LENGTH_BITS) | length
                        packed = struct.pack(PACK_FORMAT, combined, next_char_code)
                        outfile.write(packed)
                        output_size += PACK_SIZE

                        # Переместить курсор за совпадение И за следующий символ
                        cursor += length + 1
                    else:
                        # Совпадение доходит до самого конца файла. Нельзя взять 'next_char'.
                        # Вместо этого кодируем ТЕКУЩИЙ символ как литерал.
                        length = 0 # Принудительно переходим к кодированию литерала

                # Если length == 0 (не нашли совпадение, или оно уперлось в конец файла)
                if length == 0:
                    # Кодируем текущий байт как литерал (0, 0, char)
                    # Проверка, что курсор еще не вышел за пределы (должен быть в пределах из-за while)
                    if cursor < data_len:
                         literal_char_code = data[cursor]
                         offset = 0
                         length = 0

                         # Упаковка (0, 0, literal_char_code)
                         combined = 0 # (0 << LENGTH_BITS) | 0 = 0
                         packed = struct.pack(PACK_FORMAT, combined, literal_char_code)
                         outfile.write(packed)
                         output_size += PACK_SIZE

                         # Переместить курсор на 1 (за литерал)
                         cursor += 1
                    # else: курсор достиг data_len, цикл завершится

                # Отчет о прогрессе (примерно каждые 1MB)
                if cursor & 0xFFFFF == 0 and cursor > 0: # Проверка каждые ~1MB (1048576 байт)
                     progress = cursor / data_len * 100 if data_len > 0 else 100
                     print(f"\rКодировано: {cursor // 1024 // 1024} MB / {data_len // 1024 // 1024} MB ({progress:.1f}%)", end="")
                     sys.stdout.flush()

            # Финальный отчет
            success = True

    except FileNotFoundError:
        print(f"\nОшибка: Входной файл не найден: {input_file_path}")
    except MemoryError:
        print(f"\nОшибка: Недостаточно памяти для загрузки файла '{input_file_path}'. Файл слишком большой для этой реализации.")
    except Exception as e:
        print(f"\nПроизошла ошибка во время кодирования: {e}")
        traceback.print_exc() # Печать стека вызовов для детальной отладки

    return success


def decode(input_compressed_path, output_decompressed_path):
    """Декодирует файл, сжатый алгоритмом LZ77."""
    print(f"Декодирование {input_compressed_path} в {output_decompressed_path}...")
    start_time = time.time()
    bytes_read = 0
    success = False

    try:
        # Используем bytearray для эффективного добавления и среза при восстановлении
        decompressed_data = bytearray()

        with open(input_compressed_path, 'rb') as infile:
            while True:
                chunk = infile.read(PACK_SIZE)
                if not chunk:
                    break # Конец сжатого файла

                if len(chunk) < PACK_SIZE:
                     print("\nПредупреждение: Обнаружен неполный блок данных в конце сжатого файла. Файл может быть поврежден.")
                     break # Прекращаем обработку

                bytes_read += PACK_SIZE

                # Распаковка 3-байтного триплета
                combined, char_code = struct.unpack(PACK_FORMAT, chunk)

                # Извлечение offset и length
                offset = combined >> LENGTH_BITS
                length = combined & ((1 << LENGTH_BITS) - 1) # Маска для младших бит (0b1111 для LENGTH_BITS=4)

                if offset == 0 and length == 0: # Это литерал
                    decompressed_data.append(char_code)
                else: # Это ссылка на совпадение
                    # Расчет начальной позиции в уже декодированных данных
                    reference_start = len(decompressed_data) - offset

                    # Базовая проверка: offset должен указывать на существующие данные
                    if reference_start < 0:
                         raise ValueError(f"Некорректное смещение {offset} на позиции {bytes_read}. Длина дек.: {len(decompressed_data)}.")

                    # Копирование 'length' байт из позиции reference_start
                    # Побайтовое добавление корректно обрабатывает перекрывающиеся совпадения
                    for i in range(length):
                         # Доп. проверка (хотя при использовании bytearray не должна срабатывать)
                         # if reference_start + i >= len(decompressed_data):
                         #    raise ValueError("Ошибка ссылки: попытка чтения за пределами текущего буфера.")
                         decompressed_data.append(decompressed_data[reference_start + i])

                    # После копирования совпадения, добавляем литеральный символ, который шел за ним
                    decompressed_data.append(char_code)

                # Отчет о прогрессе (примерно каждые 1M триплетов)
                if bytes_read % (PACK_SIZE * 350000) == 0: # ~1MB входных данных
                    print(f"\rПрочитано сжатых: {bytes_read // 1024 // 1024} MB...", end="")
                    sys.stdout.flush()

        # Запись полностью декодированных данных в выходной файл
        with open(output_decompressed_path, 'wb') as outfile:
             outfile.write(decompressed_data)

        print(f"\rДекодирование завершено. Размер выхода: {len(decompressed_data)} байт.               ")
        success = True

    except FileNotFoundError:
        print(f"\nОшибка: Сжатый файл не найден: {input_compressed_path}")
    except struct.error:
         print(f"\nОшибка: Не удалось распаковать данные на позиции {bytes_read}. Сжатый файл поврежден или имеет неверный формат.")
    except ValueError as e:
         print(f"\nОшибка во время декодирования: {e}. Возможно повреждение сжатого файла.")
    except Exception as e:
        print(f"\nПроизошла ошибка во время декодирования: {e}")
        traceback.print_exc()

    end_time = time.time()
    if success:
        print(f"Декодирование заняло {end_time - start_time:.2f} секунд.")
    return success

# --- Ваша функция process_file_with_lz77_optimized ---
def process_file_with_lz77_optimized(input_path, compressed_path, decompressed_path):
    """Кодирует, декодирует и проверяет файл с использованием LZ77."""

    start_time = time.time()
    # Кодирование
    encode_success = encode(input_path, compressed_path)
    if not encode_success:
        print(f"Кодирование {input_path} не удалось. Пропуск декодирования и проверки.")
        return

    # Декодирование
    decode_success = decode(compressed_path, decompressed_path)
    if not decode_success:
        print(f"Декодирование {compressed_path} не удалось. Пропуск проверки.")
        return

   
    print("\n--- Результаты сжатия ---")
    end_time = time.time()
    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
    elapsed_time = end_time - start_time
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

# --- Ваш основной цикл обработки файлов ---
if __name__ == "__main__":
    # Определите пути к файлам относительно скрипта или используйте абсолютные пути
    # Убедитесь, что эти файлы существуют, или создайте тестовые файлы
    file_paths = [
        "binary_file.bin",
        "bw_image.raw",
        "gray_image.raw",
        "color_image.raw",
        "enwik7" # Пример: добавьте большие файлы, если они доступны и хватает памяти
        # "path/to/your/enwik7" # Укажите полный путь, если нужно
    ]

    # --- Создание тестовых файлов (если их нет) ---
    # Этот блок нужен только для примера, если у вас нет файлов


    # Пример создания небольшого текстового файла
  
    # Обработка каждого файла из списка
    for file_path in file_paths:
        if not os.path.exists(file_path):
             print(f"\n--- Пропуск файла (Не найден): {file_path} ---")
             continue # Переход к следующему файлу

        # Формирование имен выходных файлов
        base_name = os.path.basename(file_path)
        name_part, original_ext = os.path.splitext(base_name)

        # Имя сжатого файла
        output_compressed = f"compressed files/LZ77/{file_path[:-4]}.bin"

        output_decompressed = f"decompressed files/LZ77/{file_path[:-4]}.bin"

        print(f"\n--- Обработка файла: {file_path} ---")
        process_file_with_lz77_optimized(file_path, output_compressed, output_decompressed)

    print("\n--- Обработка всех файлов завершена ---")