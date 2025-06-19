# LTC-timecode-embedder

> Bo życie jest zbyt krótkie na ręczne wpisywanie timecode’ów. 😉

## Spis treści
- [Wprowadzenie](#wprowadzenie)
- [Funkcjonalności](#funkcjonalno%C5%9Bci)
- [Wymagania](#wymagania)
  - [Systemowe](#systemowe)
  - [Python (środowisko wirtualne)](#python-%C5%9Brodowisko-wirtualne)
- [Instalacja](#instalacja)
- [Użycie](#u%C5%BCycie)
  - [Struktura katalogów projektu](#struktura-katalog%C3%B3w-projektu)
  - [Wyświetlanie kodu QR na kamerze](#wy%C5%9Bwietlanie-kodu-qr-na-kamerze)
  - [Uruchomienie skryptu](#uruchomienie-skryptu)
  - [Synchronizacja audio (Jam Sync)](#synchronizacja-audio-jam-sync)
- [Optymalizacja i dalszy rozwój](#optymalizacja-i-dalszy-rozwi%C3%B3j)
- [Licencja](#licencja)

## Wprowadzenie
LTC-timecode-embedder to narzędzie do przetwarzania materiałów wideo, bazujące na odczycie timecode z widocznych kodów QR. Projekt powstał głównie z myślą o kamerach GoPro korzystających z **GoPro Labs**, które potrafią automatycznie generować i zapisywać timecode w formie kodów QR.

Skrypt jest jednak **agnostyczny sprzętowo** – zadziała z każdym materiałem wideo, który w pierwszych klatkach ma kod QR z timecode oraz klatkaż zgodny ze standardem **Linear Timecode (LTC)**.

Jego główne zadanie to:
1. Odczytać timecode z kodu QR (np. z GoPro Hero 12).
2. Wygenerować ciągły sygnał LTC na podstawie odczytu i klatkażu.
3. Osadzić LTC jako ścieżkę audio w wyjściowym pliku wideo.

Voilà – masz idealną synchronizację w postprodukcji i możesz zaoszczędzić sobie ręcznego „alignowania” klipów.

## Funkcjonalności
- **Inteligentny odczyt timecode z kodów QR**  
  Przeszukuje ostre klatki w pierwszych 15 sekundach, aby uzyskać najpewniejszy odczyt.  
- **Generowanie LTC**  
  Tworzy ciągły sygnał Linear Timecode idealnie dopasowany do klatkażu źródłowego.  
- **Osadzanie LTC w audio**  
  Dodaje nową ścieżkę audio (lub miksuje z istniejącą) przy użyciu FFmpeg.  
- **Zachowanie oryginałów**  
  Pliki źródłowe zostają nietknięte; nowe lądują w katalogu `target/`.  
- **Obsługa różnych FPS**  
  23.976, 24, 25, 29.97, 30, 50, 59.94, 60 – nie oceniamy, tylko wspieramy. 😎  

## Wymagania

### Systemowe
| Narzędzie | Wersja      | Instalacja (Linux)                           | Instalacja (Windows)                                   |
|-----------|-------------|----------------------------------------------|--------------------------------------------------------|
| **FFmpeg**| 5.x lub nowszy | `sudo apt update && sudo apt install ffmpeg` | Pobierz binarki, dodaj `bin\` do zmiennej **PATH** |
| **ZBar**  | dowolna z libzbar0 | `sudo apt update && sudo apt install libzbar0` | Zgodnie z dokumentacją *pyzbar* (DLL + PATH) |

> **Pro-tip:** Zbuduj FFmpeg z NVENC/NVDEC, a Twoja karta GPU podziękuje Ci w ciszy swoich wentylatorów.

### Python (środowisko wirtualne)
- **Python 3.8+**  
- Zalecane: `venv` lub `conda`  
- Wszystkie zależności instalujesz jedną magiczną komendą:  

  ```bash
  pip install -r requirements.txt
  ```

Pakiety obejmują m.in.: `opencv-python`, `pyzbar`, `pytz`, `numpy`, `scipy`, `timecode`.

## Instalacja

1. **Sklonuj repozytorium**

   ```bash
   git clone https://github.com/seeb73/LTC-timecode-embedder.git
   cd LTC-timecode-embedder
   ```

2. **Utwórz i aktywuj środowisko wirtualne**

   ```bash
   python3 -m venv timecode_env
   source timecode_env/bin/activate  # Windows: timecode_env\Scripts\activate
   ```

3. **Zainstaluj zależności Python**

   ```bash
   pip install -r requirements.txt
   ```

4. **Zainstaluj lokalny pakiet `timecode_tools`**

   ```bash
   pip install -e ./external_libs/timecode_tools_repo/
   ```

## Użycie

### Struktura katalogów projektu

```
LTC-timecode-embedder/
├── main.py
├── video_processor.py
├── utils.py
├── requirements.txt
├── external_libs/
│   └── timecode_tools_repo/
│       ├── setup.py
│       └── timecode_tools/
├── source/
│   └── CameraName/
│       └── GX01xxxx.MP4
└── target/
    └── CameraName/
        └── GX01xxxx_LTC.MP4
```

### Wyświetlanie kodu QR na kamerze
- Użyj aplikacji mobilnej generującej **timecode QR** (np. GoPro Labs QR, Tentacle Sync, Timecode Buddy).  
- Skieruj kamerę na ekran telefonu/tabletu – magia działa sama.

### Uruchomienie skryptu

```bash
python main.py ./source/ ./target/
```

- `./source/` – katalog z plikami wideo (przetwarzany rekursywnie).  
- `./target/` – gdzie wylądują pliki z osadzonym LTC (struktura lustrzana).

### Synchronizacja audio (Jam Sync)

1. **Wygeneruj referencyjny LTC** – ta sama aplikacja lub dedykowane urządzenie.  
2. **Podłącz do rejestratora** – kabel 3.5 mm → wejście liniowe (np. Zoom H6).  
3. **Jam Sync** – włącz w menu rejestratora lub nagraj LTC na osobny kanał.  
4. **Nagrywaj** – kamera z QR, rejestrator z LTC.  
5. **Postprodukcja** – importujesz klipy, a oś czasu sama wskakuje w sync. 🎯

## Optymalizacja i dalszy rozwój
- **NVENC/NVDEC** – przyspieszenie enkodowania/dekodowania.  
- **Lepsze logowanie** – bo `print("oops")` to już nie te czasy.  
- **Szybszy odczyt QR** – optymalizacje OpenCV.  
- **GUI** – żeby można było klikać, a nie tylko klepać w terminal.  

Pull requesty mile widziane – kawa też. ☕

## Licencja
Projekt jest dostępny na licencji **MIT**. Szczegóły znajdziesz w pliku `LICENSE.txt`.

---
