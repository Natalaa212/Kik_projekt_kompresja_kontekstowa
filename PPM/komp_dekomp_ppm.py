import collections
import heapq
import os
import pickle
import sciezka

# Unikalny znacznik ESCAPE, służący do "schodzenia" na niższe rzędy kontekstu
ESC = "<ESC>"


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
        root = Node(None, heap[0].freq)
        root.left = heap[0]
        return root

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



# 2. LOGIKA KASKADOWA: PPM (PREDICTION BY PARTIAL MATCHING)
# max_order ustawiony domyślnie na 4

def compress_ppm(data, max_order=4):
    if not data:
        return "", {}, 0

    # 1. budowa zestawu modeli dla rzędu: 0, 1, 2, 3 i 4
    freqs = {order: collections.defaultdict(lambda: collections.defaultdict(int)) for order in range(max_order + 1)}

    # Rząd 0: Kontekst zerowy (ratunkowy)
    for char in set(data):
        freqs[0][""][char] = data.count(char)

    # Rzędy wyższe (1, 2, 3 i 4)
    for i in range(len(data)):
        char = data[i]
        for order in range(1, min(max_order, i) + 1):
            context = data[i - order:i]
            freqs[order][context][char] += 1

    # Dodanie mechanizmu ESCAPE
    for order in range(1, max_order + 1):
        for context in freqs[order]:
            freqs[order][context][ESC] = 1

    # Generowanie słowników
    models = {order: {} for order in range(max_order + 1)}
    for order in range(max_order + 1):
        for context, f_table in freqs[order].items():
            root = build_huffman_tree(f_table)
            codes = {}
            build_codes(root, "", codes)
            models[order][context] = codes

    # 2. kompresja kaskadowa z użyciem <ESC>
    compressed_bits = []

    for i in range(len(data)):
        char = data[i]
        encoded = False

        # Zaczynamy od rzędu 4 i schodzimy w dół
        for order in range(min(max_order, i), -1, -1):
            context = data[i - order:i] if order > 0 else ""

            if context not in models[order]:
                continue

            codes = models[order][context]

            if char in codes:
                compressed_bits.append(codes[char])
                encoded = True
                break
            else:
                if ESC in codes:
                    compressed_bits.append(codes[ESC])

        if not encoded:
            raise Exception(f"Błąd kompresji krytyczny dla znaku: {char}")

    return "".join(compressed_bits), models, len(data)


# max_order ustawiony domyślnie na 4
def decompress_ppm(bitstring, models, original_len, max_order=4):
    if not bitstring:
        return ""

    rev_models = {order: {} for order in range(max_order + 1)}
    for order in range(max_order + 1):
        for context, codes in models[order].items():
            rev_models[order][context] = {code: char for char, code in codes.items()}

    decoded_chars = []
    bit_idx = 0

    while len(decoded_chars) < original_len:
        order = min(max_order, len(decoded_chars))
        char_decoded = False

        while not char_decoded:
            context = "".join(decoded_chars[-order:]) if order > 0 else ""

            if context not in rev_models[order]:
                order -= 1
                continue

            current_dict = rev_models[order][context]
            current_bits = ""
            match_found = False

            while not match_found and bit_idx < len(bitstring):
                current_bits += bitstring[bit_idx]
                bit_idx += 1

                if current_bits in current_dict:
                    symbol = current_dict[current_bits]

                    if symbol == ESC:
                        order -= 1
                        match_found = True
                    else:
                        decoded_chars.append(symbol)
                        char_decoded = True
                        match_found = True

    return "".join(decoded_chars)


# 3. GŁÓWNY PROCES

if __name__ == "__main__":
    p_wejscie = sciezka.WEJSCIE
    p_skompresowany = "skompresowany.bin"
    p_model = "slownik.pkl"
    p_wyjscie = "wyjscie_odkompresowane.txt"


    # --- ETAP 1: ODCZYT I KOMPRESJA ---
    with open(p_wejscie, "r", encoding="utf-8") as f:
        surowe_dane = f.read()

    strumien_bitow, wygenerowany_model, oryginalna_dlugosc_tekstu = compress_ppm(surowe_dane)
    dlugosc_bitow = len(strumien_bitow)

    bajt_dopelnienia = (8 - dlugosc_bitow % 8) % 8
    padded_bits = strumien_bitow + "0" * bajt_dopelnienia

    bajt_array = bytearray()
    for i in range(0, len(padded_bits), 8):
        bajt_array.append(int(padded_bits[i:i + 8], 2))

    with open(p_skompresowany, "wb") as f:
        f.write(bajt_array)

    metadane = {
        'model': wygenerowany_model,
        'dlugosc_bitow': dlugosc_bitow,
        'dlugosc_tekstu': oryginalna_dlugosc_tekstu
    }
    with open(p_model, "wb") as f:
        pickle.dump(metadane, f)

    del surowe_dane, strumien_bitow, wygenerowany_model, metadane, bajt_array, padded_bits

    # --- ETAP 2: ODCZYT Z PLIKÓW I DEKOMPRESJA ---
    with open(p_model, "rb") as f:
        wczytane_metadane = pickle.load(f)

    odczytany_model = wczytane_metadane['model']
    wymagana_dlugosc_bitow = wczytane_metadane['dlugosc_bitow']
    wymagana_dlugosc_tekstu = wczytane_metadane['dlugosc_tekstu']

    with open(p_skompresowany, "rb") as f:
        wczytane_bajty = f.read()

    odtworzony_strumien_bitow = ""
    for bajt in wczytane_bajty:
        odtworzony_strumien_bitow += bin(bajt)[2:].zfill(8)

    czysty_strumien_bitow = odtworzony_strumien_bitow[:wymagana_dlugosc_bitow]

    # Uruchomienie dekodera PPM
    odtworzony_tekst = decompress_ppm(czysty_strumien_bitow, odczytany_model, wymagana_dlugosc_tekstu)

    with open(p_wyjscie, "w", encoding="utf-8") as f:
        f.write(odtworzony_tekst)

    print(f"Zapisano pliki wynikowe: {p_skompresowany} i {p_wyjscie}.")
    print(f"Rząd wielkości modelu: 4")