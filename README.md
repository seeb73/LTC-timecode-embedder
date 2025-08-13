# LTC-timecode-embedder

> Bo życie jest zbyt krótkie na ręczne wpisywanie timecode’ów. 😉
> English version below.

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
# LTC-timecode-embedder

> Because life’s too short to type timecodes by hand. 😉

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
  - [System](#system)
  - [Python (virtual environment)](#python-virtual-environment)
- [Installation](#installation)
- [Usage](#usage)
  - [Project Directory Structure](#project-directory-structure)
  - [Displaying the QR code on the camera](#displaying-the-qr-code-on-the-camera)
  - [Running the script](#running-the-script)
  - [Audio synchronisation (Jam Sync)](#audio-synchronisation-jam-sync)
- [Optimisation & Roadmap](#optimisation--roadmap)
- [Licence](#licence)

## Introduction
LTC-timecode-embedder is a video‑processing tool that reads visible QR timecodes and embeds them as Linear Timecode (LTC) into your footage. It was conceived with GoPro cameras in mind — especially those running **GoPro Labs**, which can automatically generate and record QR timecodes.

The script is **hardware‑agnostic**: it works with any video file whose opening frames contain a QR timecode and whose frame rate is compatible with the **Linear Timecode (LTC)** standard.

Its mission, should you choose to accept it, is to:
1. Read the timecode from the QR (e.g. from a GoPro Hero 12).
2. Generate a continuous LTC signal based on the readout and the clip’s frame rate.
3. Embed that LTC as an audio track in the output file.

Voilà — frame‑accurate sync in post without the hand‑jive.

## Features
- **Smart QR timecode reader**  
  Scans the sharpest frames within the first 15 seconds to get the cleanest read.  
- **LTC generation**  
  Crafts a continuous Linear Timecode perfectly aligned to the source FPS.  
- **Audio embedding**  
  Adds a fresh LTC track (or mixes it with the existing one) via FFmpeg.  
- **Source safety**  
  Originals stay untouched; processed files land in `target/`.  
- **FPS agnosticism**  
  23.976, 24, 25, 29.97, 30, 50, 59.94, 60 — we don’t judge, we support. 😎  

## Requirements

### System
| Tool      | Version      | Install (Linux)                               | Install (Windows)                                       |
|-----------|--------------|-----------------------------------------------|---------------------------------------------------------|
| **FFmpeg**| 5.x or newer | `sudo apt update && sudo apt install ffmpeg`  | Download static build and add `bin\` to **PATH**       |
| **ZBar**  | any libzbar0 | `sudo apt update && sudo apt install libzbar0`| Follow *pyzbar* docs (DLL + add to **PATH**)            |

> **Pro‑tip:** Build FFmpeg with NVENC/NVDEC and your GPU fans will whisper their thanks.

### Python (virtual environment)
- **Python 3.8+**  
- Recommended: `venv` or `conda`  
- Install everything with one spell:  

  ```bash
  pip install -r requirements.txt
  ```

Packages include `opencv-python`, `pyzbar`, `pytz`, `numpy`, `scipy`, `timecode`.

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/seeb73/LTC-timecode-embedder.git
   cd LTC-timecode-embedder
   ```

2. **Create & activate a virtualenv**

   ```bash
   python3 -m venv timecode_env
   source timecode_env/bin/activate  # Windows: timecode_env\Scripts\activate
   ```

3. **Install Python deps**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install the local `timecode_tools` package**

   ```bash
   pip install -e ./external_libs/timecode_tools_repo/
   ```

## Usage

### Project Directory Structure

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

### Displaying the QR code on the camera
- Use a mobile app that generates **timecode QR** (e.g. GoPro Labs QR, Tentacle Sync, Timecode Buddy).  
- Point the camera at the phone/tablet screen — presto!

### Running the script

```bash
python main.py ./source/ ./target/
```

- `./source/` – directory with your videos (processed recursively).  
- `./target/` – where LTC‑fied files will be written (mirrored structure).

### Audio synchronisation (Jam Sync)

1. **Generate a reference LTC** – same app or a dedicated device.  
2. **Connect to your recorder** – 3.5 mm cable → line input (e.g. Zoom H6).  
3. **Jam Sync** – enable in the recorder’s menu or record LTC to a spare channel.  
4. **Record** – camera sees QR, recorder hears LTC.  
5. **Post** – import clips; the timeline snaps itself into place. 🎯

## Optimisation & Roadmap
- **NVENC/NVDEC** – GPU‑accelerated encoding/decoding.  
- **Better logging** – because `print("oops")` is so last season.  
- **Faster QR reading** – OpenCV tweaks.  
- **GUI** – for those who prefer clicking to typing.  

Pull requests welcome — coffee, too. ☕

## Licence
This project is released under the **MIT Licence**. See `LICENSE.txt` for details.

---
