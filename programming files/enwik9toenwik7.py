# Открываем исходный файл для чтения в бинарном режиме
with open(f'C:/Users/alexe/Desktop/uni/сем4/aicd1/enwik9', 'rb') as source_file:
    # Читаем первые 10^7 символов
    data = source_file.read(10**7)
    
    # Открываем новый файл для записи в бинарном режиме
    with open('enwik7', 'wb') as target_file:
        # Записываем данные в новый файл
        target_file.write(data)
