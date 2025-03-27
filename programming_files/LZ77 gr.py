import numpy as np
import matplotlib.pyplot as plt
import zlib

def compress_lz77(data, buffer_size):
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed_data = compressor.compress(data[:buffer_size]) + compressor.flush()
    return len(compressed_data)

file_path = "C:/Users/79508/Desktop/4 семестри/АИСД/1 лабораторная/коди/буквы и картинки/enwik7"
with open(file_path, "rb") as f:
    data = f.read()

buffer_sizes = [10 * 1024, 25 * 1024, 50 * 1024, 100 * 1024, 200 * 1024, 500 * 1024, 1024 * 1024, 2048 * 1024, 4096 * 1024, 8192 * 1024]

compression_ratios = []

for buffer_size in buffer_sizes:
    compressed_sizes = []

    for start in range(0, len(data), buffer_size):
        block = data[start:start + buffer_size]
        if not block:
            continue

        compressed_size = compress_lz77(block, buffer_size)
        compression_ratio = len(block) / compressed_size if compressed_size > 0 else 0
        compressed_sizes.append(compression_ratio)

    compression_ratios.append(np.mean(compressed_sizes))

plt.figure(figsize=(10, 5))
plt.plot(buffer_sizes, compression_ratios, marker="o", linestyle="-", color="pink", label="Коэффициент сжатия (LZ77)")

plt.xlabel("Размер буфера (байты)")
plt.ylabel("Коэффициент сжатия")
plt.title("Зависимость коэффициента сжатия от размера буфера (LZ77)")
plt.legend()
plt.grid()
plt.xscale("log")
plt.show()