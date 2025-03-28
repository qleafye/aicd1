import struct # Импортируем struct для упаковки/распаковки данных
import time
import os
import traceback # Импортируем traceback для детальной отладки ошибок
import matplotlib.pyplot as plt
from io import BytesIO # Используем BytesIO для сбора сжатых данных в памяти



#калич файл с моей реализацией






# --- Константы LZ77 ---
# Определяем биты для смещения (offset) и длины (length)
# Важно: OFFSET_BITS + LENGTH_BITS должно соответствовать формату упаковки (например, 16 бит для 'H')
OFFSET_BITS = 12  # 12 бит -> макс смещение 2^12 - 1 = 4095
LENGTH_BITS = 4   # 4 бита -> макс длина 2^4 - 1 = 15

# Максимальные значения на основе битов
MAX_OFFSET = (1 << OFFSET_BITS) - 1  # Максимально возможное смещение (4095)
MAX_LENGTH = (1 << LENGTH_BITS) - 1  # Максимальная кодируемая длина совпадения (15)

# Размер буфера поиска (search buffer) - должен быть <= MAX_OFFSET + 1
# Будет варьироваться в анализе, но ограничен MAX_OFFSET+1 при кодировании
# SEARCH_BUFFER_SIZE = 4096 # Пример, будет передан как параметр

# Размер буфера предпросмотра (lookahead buffer) - ограничивает макс. длину совпадения
LOOKAHEAD_BUFFER_SIZE = MAX_LENGTH # Максимальная длина совпадения = 15

# Минимальная длина совпадения, чтобы его кодировать (иначе кодируем как литерал)
MIN_MATCH_LENGTH = 3 # Обычно 3 выгодно (т.к. кодирование занимает 3 байта)

# Формат упаковки для struct: (Offset+Length, NextChar)
# '>' - big-endian (для переносимости)
# 'H' - unsigned short (16 бит = OFFSET_BITS + LENGTH_BITS)
# 'B' - unsigned char (8 бит для следующего символа или литерала)
# Если Offset=0 и Length=0, то 'B' - это литерал.
PACK_FORMAT = '>HB'
PACK_SIZE = struct.calcsize(PACK_FORMAT) # Размер одного закодированного блока (3 байта)


def find_longest_match(data, cursor, search_buffer_limit, lookahead_limit):
    """
    Ищет самое длинное совпадение для данных, начиная с 'cursor',
    в пределах предыдущих 'search_buffer_limit' байт.
    Возвращает (offset, length). Макс. длина ограничена 'lookahead_limit'.
    """
    end_of_buffer = len(data)
    best_match_length = 0
    best_match_offset = 0

    # Фактический предел буфера поиска, ограниченный MAX_OFFSET и началом данных
    effective_search_limit = min(search_buffer_limit, MAX_OFFSET + 1) # Учитываем предел формата
    search_start = max(0, cursor - effective_search_limit)

    # Максимально возможная длина совпадения (ограничена lookahead, концом данных и MAX_LENGTH)
    max_possible_match_len = min(lookahead_limit, MAX_LENGTH, end_of_buffer - cursor)

    # Если данных осталось меньше, чем минимальная длина совпадения, искать не нужно
    if max_possible_match_len < MIN_MATCH_LENGTH:
        return 0, 0

    # Итерация назад по буферу поиска для поиска начала совпадений
    for i in range(search_start, cursor):
        current_match_length = 0
        # Сравнение байтов: data[i+k] vs data[cursor+k]
        # Сравниваем до тех пор, пока символы совпадают и не превысили max_possible_match_len
        while current_match_length < max_possible_match_len and \
              data[i + current_match_length] == data[cursor + current_match_length]:
            current_match_length += 1

        # Если текущее совпадение лучшее И удовлетворяет мин. длине
        # (Условие current_match_length >= MIN_MATCH_LENGTH не нужно, т.к. best_match_length изначально 0
        # и обновится только если current_match_length >= MIN_MATCH_LENGTH будет найдено)
        if current_match_length > best_match_length:
            best_match_length = current_match_length
            best_match_offset = cursor - i # Смещение = расстояние назад от cursor

    # Если найдено подходящее совпадение (длиной >= MIN_MATCH_LENGTH)
    if best_match_length >= MIN_MATCH_LENGTH:
         # Длина уже ограничена MAX_LENGTH через max_possible_match_len
         return best_match_offset, best_match_length
    else:
         return 0, 0 # Подходящее совпадение не найдено

# Изменено: Принимает данные и размер буфера, возвращает сжатые байты
def encode_data(data: bytes, search_buffer_size: int) -> bytes:
    """Кодирует переданные байтовые данные с использованием алгоритма LZ77."""
    data_len = len(data)
    cursor = 0
    # Используем bytearray для эффективного добавления байт
    compressed_data = bytearray()

    while cursor < data_len:
        # Поиск самого длинного совпадения
        # Передаем актуальный размер буфера поиска и лимит на длину
        offset, length = find_longest_match(data, cursor, search_buffer_size, LOOKAHEAD_BUFFER_SIZE)

        if length >= MIN_MATCH_LENGTH: # Найдено подходящее совпадение
            # Нужен байт, СЛЕДУЮЩИЙ за совпадением
            next_char_pos = cursor + length
            # Важная проверка: Убедиться, что СЛЕДУЮЩИЙ байт существует в данных
            if next_char_pos < data_len:
                next_char_code = data[next_char_pos]

                # Упаковка (offset, length, next_char_code)
                # Сдвигаем offset влево на LENGTH_BITS и добавляем length
                combined = (offset << LENGTH_BITS) | length
                try:
                    # struct.pack ожидает bytes для 'c' или 's' формата, поэтому [next_char_code] -> bytes([next_char_code])
                    packed = struct.pack(PACK_FORMAT, combined, next_char_code)
                    compressed_data.extend(packed)
                except struct.error as e:
                    print(f"Ошибка упаковки: offset={offset}, length={length}, combined={combined}, next_char={next_char_code}")
                    print(f"MAX_OFFSET={MAX_OFFSET}, MAX_LENGTH={MAX_LENGTH}")
                    raise e


                # Переместить курсор за совпадение И за следующий символ
                cursor += length + 1
            else:
                # Совпадение доходит до самого конца файла. Нельзя взять 'next_char'.
                # Кодируем последнее совпадение как есть, но с "фиктивным" следующим символом (например, 0).
                # Или, как в оригинале, кодируем последний символ как литерал. Выберем второй вариант для простоты.
                # В этом случае, совпадение не используется, и мы переходим к кодированию литерала.
                length = 0 # Принудительно переходим к кодированию литерала ниже

        # Если length < MIN_MATCH_LENGTH (не нашли совпадение, или оно уперлось в конец файла и было отменено)
        if length < MIN_MATCH_LENGTH:
            # Кодируем текущий байт как литерал (0, 0, char)
            # Проверка не нужна, т.к. while cursor < data_len гарантирует это
            literal_char_code = data[cursor]
            offset = 0
            length = 0 # Явно указываем 0 для литерала

            # Упаковка (0, 0, literal_char_code)
            combined = 0 # (0 << LENGTH_BITS) | 0 = 0
            try:
                # struct.pack ожидает bytes для 'c' или 's' формата
                packed = struct.pack(PACK_FORMAT, combined, literal_char_code)
                compressed_data.extend(packed)
            except struct.error as e:
                 print(f"Ошибка упаковки литерала: char={literal_char_code}")
                 raise e

            # Переместить курсор на 1 (за литерал)
            cursor += 1

    # Возвращаем сжатые данные как неизменяемый объект bytes
    return bytes(compressed_data)


def analyze_buffer_sizes(file_path: str):
    """Анализирует эффективность сжатия для разных размеров буфера"""
    print(f"Анализ файла: {file_path}")

    try:
        # Читаем файл
        with open(file_path, 'rb') as f:
            data = f.read()
        original_size = len(data)
        if original_size == 0:
            print("Файл пуст, анализ невозможен.")
            return
        print(f"Размер файла: {original_size:,} байт")
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден: {file_path}")
        return
    except MemoryError:
        print(f"Ошибка: Недостаточно памяти для загрузки файла '{file_path}'.")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    # Размеры буфера для тестирования (от 256 байт до MAX_OFFSET+1)
    # Используем степени двойки до предела, заданного OFFSET_BITS
    buffer_sizes = [2**i for i in range(8, OFFSET_BITS + 1)] # 2^8=256, ..., 2^12=4096
    # Добавим еще несколько промежуточных или больших, если нужно, но учтем MAX_OFFSET
    # buffer_sizes = [256, 512, 1024, 2048, 4096] # Явное задание
    print(f"Тестируемые размеры буфера поиска (до {MAX_OFFSET+1}): {buffer_sizes}")


    results = []
    for buffer_size in buffer_sizes:
        # Убедимся, что размер буфера не превышает лимит кодирования
        current_search_buffer_size = min(buffer_size, MAX_OFFSET + 1)
        print(f"\nТестирование буфера размером {current_search_buffer_size} байт...")

        try:
            # Замеряем время и сжимаем
            start_time = time.time()
            # Вызываем исправленную функцию encode_data
            compressed = encode_data(data, current_search_buffer_size)
            compression_time = time.time() - start_time

            # Вычисляем метрики
            compressed_size = len(compressed)
            # Предотвращаем деление на ноль, если сжатый размер 0 (маловероятно, но возможно для пустых/малых данных)
            if compressed_size == 0:
                compression_ratio = float('inf') # Бесконечное сжатие?
                space_saving = 100.0
            else:
                compression_ratio = original_size / compressed_size
                space_saving = (1 - compressed_size / original_size) * 100

            results.append({
                'buffer_size': current_search_buffer_size,
                'compressed_size': compressed_size,
                'ratio': compression_ratio,
                'saving': space_saving,
                'time': compression_time
            })

            print(f"Размер после сжатия: {compressed_size:,} байт")
            print(f"Степень сжатия: {compression_ratio:.3f}")
            print(f"Экономия места: {space_saving:.1f}%")
            print(f"Время сжатия: {compression_time:.3f} сек")

        except MemoryError:
             print(f"Ошибка: Недостаточно памяти во время сжатия с буфером {current_search_buffer_size}.")
             # Можно прервать цикл или пропустить этот размер
             continue
        except Exception as e:
            print(f"Произошла ошибка во время сжатия с буфером {current_search_buffer_size}: {e}")
            traceback.print_exc() # Печать стека вызовов
            # Пропустить этот размер буфера
            continue


    # Проверяем, есть ли результаты для построения графика
    if not results:
        print("\nНе удалось получить результаты для анализа.")
        return

    # Строим графики
    plt.figure(figsize=(18, 6)) # Немного шире

    buffer_labels = [f"{r['buffer_size']/1024:.1f}K" if r['buffer_size'] >= 1024 else f"{r['buffer_size']}B" for r in results]
    buffer_values = [r['buffer_size'] for r in results]

    # График степени сжатия
    plt.subplot(1, 3, 1)
    plt.plot(buffer_values, [r['ratio'] for r in results], 'bo-')
    plt.grid(True, which="both", ls="--")
    plt.xlabel('Размер буфера поиска (байт)')
    plt.ylabel('Степень сжатия')
    plt.title('Степень сжатия vs Размер буфера')
    plt.xscale('log', base=2) # Логарифмическая шкала по X (основание 2)
    plt.xticks(buffer_values, buffer_labels, rotation=45)


    # График экономии места
    plt.subplot(1, 3, 2)
    plt.plot(buffer_values, [r['saving'] for r in results], 'go-')
    plt.grid(True, which="both", ls="--")
    plt.xlabel('Размер буфера поиска (байт)')
    plt.ylabel('Экономия места (%)')
    plt.title('Экономия места vs Размер буфера')
    plt.xscale('log', base=2)
    plt.xticks(buffer_values, buffer_labels, rotation=45)
    plt.ylim(bottom=min(0, min(r['saving'] for r in results) - 5), top=100) # Убедимся, что 0 и 100 видны


    # График времени сжатия
    plt.subplot(1, 3, 3)
    plt.plot(buffer_values, [r['time'] for r in results], 'ro-')
    plt.grid(True, which="both", ls="--")
    plt.xlabel('Размер буфера поиска (байт)')
    plt.ylabel('Время сжатия (сек)')
    plt.title('Время сжатия vs Размер буфера')
    plt.xscale('log', base=2)
    plt.xticks(buffer_values, buffer_labels, rotation=45)
    plt.ylim(bottom=0) # Время не может быть отрицательным

    plt.tight_layout(pad=2.0) # Добавим отступы
    try:
        plt.savefig('lz77_analysis.png')
        print(f"\nГрафики сохранены в lz77_analysis.png")
    except Exception as e:
        print(f"\nНе удалось сохранить графики: {e}")
    plt.show()

    # Находим оптимальный размер буфера по выбранной метрике
    # Метрика: (Степень сжатия) / sqrt(Время + epsilon), чтобы избежать деления на ноль и уменьшить влияние очень малого времени
    epsilon = 1e-9
    try:
        optimal_result = max(results, key=lambda x: x['ratio'] / ((x['time'] + epsilon)**0.5) if x['time'] >= 0 else -1)
    except ValueError: # Если results пустой
        optimal_result = None


    # Выводим таблицу результатов
    print("\nРезультаты анализа:")
    print("-" * 80)
    print(f"{'Размер буфера':>15} | {'Степень сжатия':>15} | {'Экономия места':>15} | {'Время (сек)':>12}")
    print("-" * 80)

    for r in results:
         buffer_kb = f"{r['buffer_size']/1024:.1f} KB" if r['buffer_size'] >= 1024 else f"{r['buffer_size']} B"
         print(f"{buffer_kb:>15} | "
              f"{r['ratio']:>15.3f} | "
              f"{r['saving']:>14.1f}% | "
              f"{r['time']:>12.3f}")

    print("-" * 80)

    if optimal_result:
        opt_buffer_kb = f"{optimal_result['buffer_size']/1024:.1f} KB" if optimal_result['buffer_size'] >= 1024 else f"{optimal_result['buffer_size']} B"
        print(f"\nОптимальный размер буфера (по метрике ratio/sqrt(time)): {opt_buffer_kb}")
        print(f"  Степень сжатия: {optimal_result['ratio']:.3f}")
        print(f"  Экономия места: {optimal_result['saving']:.1f}%")
        print(f"  Время сжатия: {optimal_result['time']:.3f} сек")
    else:
        print("\nНе удалось определить оптимальный размер буфера.")


if __name__ == "__main__":
    # Имя файла для анализа (может потребоваться скачать enwik8 или enwik9 для теста)
    # Использование enwik7 может быть проблематично из-за размера (около 100MB)
    # Убедитесь, что у вас достаточно ОЗУ
    filename_to_analyze = 'enwik7' # Используем enwik8 как более стандартный бенчмарк (100MB)
    # filename_to_analyze = 'enwik7' # Если вы хотите использовать enwik7
    # filename_to_analyze = 'some_text_file.txt' # Или любой другой файл

    if not os.path.exists(filename_to_analyze):
        print(f"Ошибка: файл '{filename_to_analyze}' не найден!")
    else:
        analyze_buffer_sizes(filename_to_analyze)