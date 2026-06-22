import os
import sciezka

# Definicje ścieżek
p_wejscie = sciezka.WEJSCIE
p_skompresowany = "skompresowany.bin"
p_wyjscie = "wyjscie_odkompresowane.txt"


def porownaj_pliki():

    print("====================================================")
    # Obliczanie wag plików
    waga_wejscia = os.path.getsize(p_wejscie)
    waga_bin = os.path.getsize(p_skompresowany)

    print(f" Rozmiar pliku pierwotnego: {waga_wejscia} bajtów")
    print(f" Rozmiar pliku skompresowanego (.bin): {waga_bin} bajtów")

    zysk = ((waga_wejscia - waga_bin) / waga_wejscia) * 100
    print(f" Zysk z kompresji danych: {zysk:.2f}%")


    # Weryfikacja bezstratności (porównanie tekstu znaku po znaku)
    print("Weryfikacja bezstratności:")
    try:
        with open(p_wejscie, "r", encoding="utf-8") as f1, open(p_wyjscie, "r", encoding="utf-8") as f2:
            tekst_oryginalny = f1.read()
            tekst_odtworzony = f2.read()

            if tekst_oryginalny == tekst_odtworzony:
                print(" Zawartość odtworzona w 100% poprawnie.")
            else:
                print(" Pliki różnią się zawartością. Algorytm zgubił lub przekłamał dane.")
    except Exception as e:
        print(f" Wystąpił błąd podczas czytania plików: {e}")

    print("====================================================")


if __name__ == "__main__":
    porownaj_pliki()