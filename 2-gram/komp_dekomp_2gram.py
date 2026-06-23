import collections
import heapq
import os
import pickle
import sciezka

# 1. STRUKTURY DANYCH DLA KODERA HUFFMANA

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(frequencies):
    heap = [Node(char, f) for char, f in frequencies.items()]
    heapq.heapify(heap)

    if len(heap) == 1:
        return heap[0]

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0] if heap else None


def build_codes(node, current_code, codes):
    if node is None:
        return
    if node.char is not None:
        codes[node.char] = current_code if current_code else "0"
        return
    build_codes(node.left, current_code + "0", codes)
    build_codes(node.right, current_code + "1", codes)


# 2. LOGIKA UKŁADU KONTEKSTOWEGO (2-GRAM)

def compress_2gram(data):
    if not data:
        return "", {}

    # context_freqs[kontekst][znak] = liczba wystapien
    context_freqs = collections.defaultdict(lambda: collections.defaultdict(int))
    context = ""

    # Zliczanie częstotliwości w kontekstach 2-znakowych
    for char in data:
        context_freqs[context][char] += 1
        # Dodajemy nowy znak i ucinamy do maksymalnie 2 ostatnich znaków
        context = (context + char)[-2:]

    context_codes = {}
    for ctx, freqs in context_freqs.items():
        root = build_huffman_tree(freqs)
        codes = {}
        build_codes(root, "", codes)
        context_codes[ctx] = codes

    compressed_bits = []
    context = ""

    # kompresja
    for char in data:
        code = context_codes[context][char]
        compressed_bits.append(code)
        context = (context + char)[-2:]

    return "".join(compressed_bits), context_codes


def decompress_2gram(bitstring, context_codes):
    if not bitstring:
        return ""

    reverse_codes = {}
    for ctx, codes in context_codes.items():
        reverse_codes[ctx] = {code: char for char, code in codes.items()}

    decoded_chars = []
    current_bits = ""
    context = ""

    for bit in bitstring:
        current_bits += bit
        if current_bits in reverse_codes[context]:
            found_char = reverse_codes[context][current_bits]
            decoded_chars.append(found_char)
            # Aktualizujemy kontekst dla następnego bitu (2 ostatnie zdekodowane znaki)
            context = (context + found_char)[-2:]
            current_bits = ""

    return "".join(decoded_chars)


# 3. GLÓWNY PROCES

if __name__ == "__main__":
    # Definicje ścieżek do plików
    p_wejscie = sciezka.WEJSCIE
    p_skompresowany = "skompresowany.bin"
    p_slownik = "slownik.pkl"
    p_wyjscie = "wyjscie_odkompresowane.txt"

    # 1. Pobranie danych z pliku wejściowego
    with open(p_wejscie, "r", encoding="utf-8") as f:
        surowe_dane = f.read()

    # 2. Uruchomienie kompresora kontekstowego (2-gram)
    strumien_bitow, wygenerowany_slownik = compress_2gram(surowe_dane)
    oryginalna_dlugosc_bitowa = len(strumien_bitow)

    # 3. Zapis skompresowanego strumienia bitów do pliku binarnego .bin
    bajt_dopelnienia = (8 - oryginalna_dlugosc_bitowa % 8) % 8
    padded_bits = strumien_bitow + "0" * bajt_dopelnienia

    bajt_array = bytearray()
    for i in range(0, len(padded_bits), 8):
        bajt_array.append(int(padded_bits[i:i + 8], 2))

    with open(p_skompresowany, "wb") as f:
        f.write(bajt_array)

    # 4. Zapis słownika oraz metadanych do pliku .pkl
    metadane = {
        'slownik': wygenerowany_slownik,
        'dlugosc': oryginalna_dlugosc_bitowa
    }
    with open(p_slownik, "wb") as f:
        pickle.dump(metadane, f)

    print(f"Zapisano plik skompresowany danych (2-gram): {p_skompresowany}")
    print(f"Zapisano plik klucza/słownika: {p_slownik}")

    # Czyszczenie zmiennych
    del surowe_dane, strumien_bitow, wygenerowany_slownik, metadane, bajt_array, padded_bits


    # 1. Odczytanie słownika i metadanych z pliku klucza
    with open(p_slownik, "rb") as f:
        wczytane_metadane = pickle.load(f)

    odczytany_slownik = wczytane_metadane['slownik']
    wymagana_dlugosc_bitow = wczytane_metadane['dlugosc']

    # 2. Odczytanie bajtów z pliku binarnego i odtworzenie ciągu zer i jedynek
    with open(p_skompresowany, "rb") as f:
        wczytane_bajty = f.read()

    odtworzony_strumien_bitow = ""
    for bajt in wczytane_bajty:
        odtworzony_strumien_bitow += bin(bajt)[2:].zfill(8)

    # Odetnij sztuczne zera dodane jako dopełnienie bajtowe
    czysty_strumien_bitow = odtworzony_strumien_bitow[:wymagana_dlugosc_bitow]

    # 3. Uruchomienie dekodera
    odtworzony_tekst = decompress_2gram(czysty_strumien_bitow, odczytany_slownik)

    # 4. Zapisanie gotowego, odkodowanego tekstu do nowego pliku
    with open(p_wyjscie, "w", encoding="utf-8") as f:
        f.write(odtworzony_tekst)

    print(f"Zapisano odtworzony plik wynikowy: {p_wyjscie}")