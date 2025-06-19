# video_processor.py
# Moduł odpowiedzialny za przetwarzanie wideo, włącznie z dodawaniem kodu czasowego
#
# Autor: [Twoje Imię/Nazwa Firmy - lub pozostaw puste]
# Data: 2025-06-18
# Wersja: 4.8 (Poprawiona logika tworzenia obiektu Timecode ze stringa HH:MM:SS:FF)
#
# Opis:
# Ten moduł zawiera klasę VideoProcessor do przetwarzania plików wideo.
# Główne funkcje obejmują:
# 1. Odczytywanie kodu QR GoPro z nagrań wideo w celu uzyskania dokładnego czasu rozpoczęcia.
# 2. Generowanie sygnału Linear Timecode (LTC) jako pliku audio WAV, opartego na odczytanym czasie i klatkażu wideo.
# 3. Łączenie wygenerowanego pliku audio z oryginalnym wideo jako dodatkowej ścieżki audio za pomocą FFmpeg.
#    Rozwiązanie omija brak filtra 'smpteh' w standardowych kompilacjach FFmpeg.
#
# Zależności:
# - FFmpeg (musi być zainstalowany i dostępny w PATH)
# - ffprobe (część pakietu FFmpeg, musi być zainstalowany i dostępny w PATH)
# - OpenCV (cv2) (instalacja: `pip install opencv-python`)
# - pyzbar (instalacja: `pip install pyzbar`)
# - pytz (biblioteka Python, instalacja: `pip install pytz`)
# - numpy (instalacja: `pip install numpy`)
# - scipy (instalacja: `pip install scipy`)
# - timecode (biblioteka Python, najprawdopodobniej zainstalowana globalnie, np. `pip install timecode`)
# - timecode_tools (repozytorium sklonowane do external_libs/, używamy tylko tools.py z tego)

import sys
import os
import datetime
import subprocess
import cv2
from pyzbar import pyzbar
import re
from fractions import Fraction
import pytz
import numpy as np
import traceback
import numbers

# Import dla zapisu pliku WAV (nadal używamy scipy)
#from scipy.io.wavfile import write as write_wav

# Dodaj ścieżkę do katalogu 'external_libs'
#current_script_dir = os.path.dirname(os.path.abspath(__file__))
#external_libs_path = os.path.join(current_script_dir, 'external_libs')
#if external_libs_path not in sys.path:
#    sys.path.insert(0, external_libs_path)


from timecode import Timecode
from timecode_tools.tools import ltc_encode, cint


# --- KLUCZOWE ZMIANY W IMPORCIE ---
try:
    # Import Timecode z systemowej biblioteki (tej, którą masz zainstalowaną)
    from timecode import Timecode
    # Import ltc_encode i cint z 'external_libs/timecode_tools/tools.py'
    from timecode_tools.tools import ltc_encode, cint 
    print("Pomyślnie załadowano Timecode (zewnętrzny) i ltc_encode/cint (z timecode_tools).")
except ImportError as e:
    print(f"Błąd: Nie można załadować wymaganych modułów. Upewnij się, że 'timecode' (pip install timecode) jest zainstalowany i 'external_libs/timecode_tools/tools.py' jest dostępne. Błąd: {e}")
    traceback.print_exc()
    sys.exit(1) # Zakończ program z błędem, ponieważ to jest krytyczny import

__version__ = "4.8" # Zaktualizowany numer wersji
print(f"Ładowanie video_processor.py - Wersja: {__version__}")


# --- FUNKCJA parse_gopro_qr_timecode - PRZYWRÓCONA ---
def parse_gopro_qr_timecode(qr_data: str) -> datetime.datetime:
    """
    Parsuje dane kodu QR GoPro do obiektu datetime.
    Oczekiwany format: oT<YYMMDDHHMMSS.mmm>oTD<DST_FLAG>oTZ<TIMEZONE_OFFSET>oTI<UTC_OFFSET>
    Przykład: oT250618091541.679oTD1oTZ2oTI0
    """
    if not qr_data.startswith('oT'):
        raise ValueError("Nieprawidłowy format kodu QR GoPro: nie zaczyna się od 'oT'")

    timestamp_match = re.search(r'oT(\d{12}\.\d{3})', qr_data)
    if not timestamp_match:
        raise ValueError("Nieprawidłowy format kodu QR GoPro: nie znaleziono części znacznika czasu")

    timestamp_str = timestamp_match.group(1)

    year_str = timestamp_str[0:2]
    current_year = datetime.datetime.now().year
    year_prefix = (current_year // 100) * 100
    # Prosta heurystyka dla roku: jeśli XX w YYMMDD jest większe niż bieżący rok + 10 lat,
    # zakładamy, że to poprzednie stulecie (np. 99 dla 1999, jeśli jest rok 2000-2009)
    if int(year_str) > (current_year % 100) + 10: 
        year_prefix -= 100
    full_year = year_prefix + int(year_str)

    month = int(timestamp_str[2:4])
    day = int(timestamp_str[4:6])
    hour = int(timestamp_str[6:8])
    minute = int(timestamp_str[8:10])
    second = int(timestamp_str[10:12])
    millisecond = int(timestamp_str[13:16])

    # Tworzymy naive datetime
    naive_dt = datetime.datetime(full_year, month, day, hour, minute, second, millisecond * 1000)

    # Parsowanie offsetu UTC
    utc_offset_match = re.search(r'oTI(-?\d+)', qr_data)
    if not utc_offset_match:
        utc_offset_hours = 0 # Domyślnie 0, jeśli nie ma offsetu
    else:
        utc_offset_hours = int(utc_offset_match.group(1))

    # Tworzenie obiektu timezone z offsetu
    offset_timedelta = datetime.timedelta(hours=utc_offset_hours)
    tz_info = datetime.timezone(offset_timedelta)
    
    # Lokalizacja naive_dt do strefy czasowej z QR i konwersja na UTC
    localized_dt = naive_dt.replace(tzinfo=tz_info)
    utc_dt = localized_dt.astimezone(datetime.timezone.utc)

    return utc_dt


def generate_ltc_audio_file(start_time_utc: datetime.datetime, duration_seconds: float, fps: float, output_path: str):
    """
    Generuje plik WAV zawierający sygnał LTC.
    Używa klasy Timecode z zewnętrznej biblioteki 'timecode' i funkcji ltc_encode z 'timecode_tools/tools.py'.
    """
    sample_rate = 48000
    bits = 16 # Domyślnie 16-bitowe audio, jak w standardach LTC

    print(f"DEBUG (LTC Gen): start_time_utc: {start_time_utc} (type: {type(start_time_utc)})")
    print(f"DEBUG (LTC Gen): duration_seconds: {duration_seconds} (type: <class 'float'>)")
    print(f"DEBUG (LTC Gen): fps: {fps} (type: <class 'float'>)")

    try:
        if not isinstance(duration_seconds, (int, float)):
            raise TypeError(f"duration_seconds musi być liczbą, otrzymano {type(duration_seconds)}: {duration_seconds}")
        if not isinstance(fps, (int, float)):
            raise TypeError(f"fps musi być liczbą, otrzymano {type(fps)}: {fps}")
        if not isinstance(start_time_utc, datetime.datetime):
            raise TypeError(f"start_time_utc musi być obiektem datetime.datetime, otrzymano {type(start_time_utc)}: {start_time_utc}")

        print(f"DEBUG (LTC Gen): Wartości po konwersji/sprawdzeniu: duration_seconds={duration_seconds}, fps={fps}")

        # Utworzenie obiektu Timecode
        # Biblioteka Timecode (v1.4.1) nie posiada metody from_datetime().
        # Musimy ręcznie sformatować datetime na string HH:MM:SS:FF dla konstruktora Timecode(fps, start_string).
        
        # Obliczanie całkowitej liczby klatek od północy UTC do start_time_utc
        # Upewniamy się, że czas jest "naiwny" (bez strefy czasowej) do obliczeń
        naive_start_time = start_time_utc.replace(tzinfo=None)
        
        # Oblicz sekundy od północy
        total_seconds_from_midnight = (naive_start_time - naive_start_time.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        
        # Dodaj klatki wynikające z milisekund. Zaokrąglamy w dół, aby nie przekroczyć bieżącej klatki.
        frames_from_seconds = int(total_seconds_from_midnight * fps)
        
        # Rozłożenie całkowitej liczby klatek na HH:MM:SS:FF
        frames_per_hour = int(fps * 3600)
        frames_per_minute = int(fps * 60)
        frames_per_second = int(fps)

        hours = frames_from_seconds // frames_per_hour
        remaining_frames = frames_from_seconds % frames_per_hour
        
        minutes = remaining_frames // frames_per_minute
        remaining_frames %= frames_per_minute
        
        seconds = remaining_frames // frames_per_second
        frames = remaining_frames % frames_per_second

        # Upewniamy się, że nie ma wartości ujemnych dla klatek (może się zdarzyć przy bardzo małych floatach)
        frames = max(0, frames)

        start_time_code_string = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{int(frames):02d}"
        
        print(f"DEBUG (LTC Gen): Tworzenie obiektu Timecode. Start timecode string: {start_time_code_string}, fps: {fps}")

        tc_start = Timecode(fps, start_time_code_string) # Używamy konstruktora Timecode(fps, start_string)
        print(f"DEBUG (LTC Gen): Obiekt Timecode startowy utworzony: {tc_start}")


        total_frames_to_generate_ltc = int(duration_seconds * fps)
        print(f"DEBUG (LTC Gen): Całkowita liczba klatek do wygenerowania LTC: {total_frames_to_generate_ltc}")

        # Generowanie danych LTC dla każdej klatki
        ltc_frames_data = []
        current_tc = tc_start
        # Generujemy o jedną klatkę więcej niż total_frames_to_generate_ltc, aby upewnić się,
        # że pokrywamy pełny czas trwania i uniknąć niedomiaru w przypadku zaokrągleń
        for _ in range(total_frames_to_generate_ltc + 1): 
            ltc_frames_data.append(ltc_encode(current_tc, as_string=True))
            current_tc.next()
        
        # Łączenie danych binarnych LTC
        ltc_bitstream = ''.join(ltc_frames_data)

        # Generowanie sygnału "Double Pulse" na podstawie bitstreamu LTC
        double_pulse_data = ''
        next_is_up = True
        for bit_char in ltc_bitstream:
            if bit_char == '0':
                if next_is_up:
                    double_pulse_data += '11'
                else:
                    double_pulse_data += '00'
                next_is_up = not next_is_up
            else:
                double_pulse_data += '10' if next_is_up else '01'
        
        # Konwersja sygnału "Double Pulse" na dane PCM
        total_samples = int(sample_rate * duration_seconds)
        
        # Obliczamy liczbę próbek na "bit" w double_pulse_data
        # Jeśli double_pulse_data jest puste (mało prawdopodobne, ale dla bezpieczeństwa)
        if not double_pulse_data:
            print("Ostrzeżenie: double_pulse_data jest puste, nie można wygenerować audio LTC.")
            return False

        samples_per_bit_in_double_pulse = total_samples / len(double_pulse_data)

        # Stworzenie tablicy NumPy na dane audio
        audio_data = np.zeros(total_samples, dtype=np.int16) # np.int16 dla 16-bitowych próbek

        on_val = 32767  # Max wartość dla int16
        off_val = -32768 # Min wartość dla int16

        for i in range(total_samples):
            # Obliczenie, który bit z double_pulse_data odpowiada bieżącej próbce
            # Używamy min, aby zapobiec wyjściu poza zakres przy ostatniej próbce
            double_pulse_index = min(int(i / samples_per_bit_in_double_pulse), len(double_pulse_data) - 1)
            
            if double_pulse_data[double_pulse_index] == '1':
                audio_data[i] = on_val
            else:
                audio_data[i] = off_val
        
        # Zapisanie danych audio do pliku WAV
        write_wav(output_path, sample_rate, audio_data)
        
        print(f"Wygenerowano tymczasowy plik audio (LTC): {output_path}")
        return True
    except Exception as e:
        print(f"Błąd podczas generowania pliku LTC audio {output_path}: {e}")
        traceback.print_exc()
        return False


class VideoProcessor:
    def __init__(self, output_base_dir: str, input_base_dir: str):
        self.output_base_dir = output_base_dir
        self.input_base_dir = input_base_dir
        if not os.path.exists(self.output_base_dir):
            os.makedirs(self.output_base_dir)

    def _get_video_info(self, video_path: str) -> tuple[float, float]:
        """Pobiera czas trwania wideo i klatkaż za pomocą ffprobe."""
        
        try:
            probe_duration_cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path
            ]
            duration_result = subprocess.run(probe_duration_cmd, capture_output=True, text=True, check=True)
            duration_str = duration_result.stdout.strip()
            
            if not duration_str:
                raise ValueError(f"FFprobe nie zwrócił czasu trwania dla {video_path}. Wyjście: '{duration_result.stdout.strip()}' Błąd: '{duration_result.stderr.strip()}'")
            
            duration_seconds = float(duration_str)

            probe_fps_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=avg_frame_rate',
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path
            ]
            fps_result = subprocess.run(probe_fps_cmd, capture_output=True, text=True, check=True)
            fps_output = fps_result.stdout.strip()

            fps_matches = re.findall(r'^\d+(?:/\d+)?$', fps_output, re.MULTILINE)
            if not fps_matches:
                raise ValueError(f"Nie udało się sparsować klatkażu z wyjścia ffprobe dla {video_path}. Wyjście: '{fps_output}' Błąd: '{fps_result.stderr.strip()}'")

            fps_str = fps_matches[0]
            frame_rate = float(Fraction(fps_str))
            
            print(f"DEBUG: _get_video_info dla {video_path} zwróciło: duration={duration_seconds}, fps={frame_rate}")
            return duration_seconds, frame_rate
        except (subprocess.CalledProcessError, ValueError, ZeroDivisionError) as e:
            raise ValueError(f"Błąd podczas pobierania informacji wideo dla {video_path}: {e}") from e


    def _read_qr_from_video(self, video_path: str, frame_rate: float) -> tuple[datetime.datetime | None, int]:
        """Odczytuje pierwszy prawidłowy kod QR z początku wideo."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Błąd: Nie można otworzyć pliku wideo {video_path}")
            return None, -1

        first_qr_time = None
        first_qr_frame_index = -1

        frame_index = 0
        max_frames_to_scan = int(frame_rate * 10) # Skanuj pierwsze 5 sekund
        if max_frames_to_scan < 50: # Przynajmniej 50 klatek, żeby nie przegapić QR
            max_frames_to_scan = 50

        while frame_index < max_frames_to_scan:
            ret, frame = cap.read()
            if not ret:
                print(f"Ostrzeżenie: Osiągnięto koniec wideo lub nie udało się odczytać klatki {frame_index} dla {video_path}.")
                break

            decoded_objects = pyzbar.decode(frame)
            for obj in decoded_objects:
                try:
                    qr_data = obj.data.decode('utf-8')
                    # Upewnij się, że parse_gopro_qr_timecode jest zdefiniowane
                    qr_timestamp = parse_gopro_qr_timecode(qr_data) 
                    first_qr_time = qr_timestamp
                    first_qr_frame_index = frame_index
                    cap.release()
                    return first_qr_time, first_qr_frame_index
                except ValueError as e:
                    # print(f"Ostrzeżenie: Nieprawidłowy kod QR: {e}") # Można włączyć dla debugowania
                    continue

            frame_index += 1

        cap.release()
        print(f"Nie znaleziono prawidłowego kodu QR w pierwszych {max_frames_to_scan} klatkach {video_path}.")
        return None, -1

    def _add_ltc_track_to_video(self, video_path: str, start_datetime_utc: datetime.datetime, frame_rate: float, duration_seconds: float) -> bool:
        """Dodaje ścieżkę audio z sygnałem (LTC) do wideo za pomocą ffmpeg."""

        relative_to_input = os.path.relpath(video_path, start=self.input_base_dir)
        output_sub_dir = os.path.join(self.output_base_dir, os.path.dirname(relative_to_input))
        os.makedirs(output_sub_dir, exist_ok=True)

        base_name, ext = os.path.splitext(os.path.basename(video_path))
        output_filename = f"{base_name}_LTC{ext}"
        output_path = os.path.join(output_sub_dir, output_filename)

        temp_ltc_audio_file = os.path.join(os.path.dirname(output_path), f"temp_ltc_{base_name}.wav")

        if start_datetime_utc is None or duration_seconds is None or frame_rate is None:
            print(f"Błąd (w _add_ltc_track_to_video): Brak wymaganych danych (czas rozpoczęcia, czas trwania lub klatkaż) do wygenerowania audio dla {video_path}. Pomijam generowanie audio.")
            return False

        if not isinstance(duration_seconds, (int, float)) or not isinstance(frame_rate, (int, float)):
            print(f"Błąd (w _add_ltc_track_to_video): Czas trwania ({duration_seconds}) lub klatkaż ({frame_rate}) nie jest liczbą dla {video_path}. Pomijam generowanie audio.")
            return False


        if not generate_ltc_audio_file(start_datetime_utc, duration_seconds, frame_rate, temp_ltc_audio_file):
            return False

        # Komenda FFmpeg do dodawania ścieżki audio
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', temp_ltc_audio_file,
            '-map', '0:v:0',      # Mapuje pierwszą ścieżkę wideo z wejścia 0 (oryginalne wideo)
            '-map', '0:a?',       # Mapuje wszystkie istniejące ścieżki audio z wejścia 0, jeśli są
            '-map', '1:a:0',      # Mapuje pierwszą ścieżkę audio z wejścia 1 (nasz nowo wygenerowany LTC)
            '-c:v', 'copy',       # Kopiuje strumień wideo bez rekompresji
            '-c:a', 'copy',       # Kopiuje istniejące strumienie audio bez rekompresji
            '-c:a:1', 'pcm_s16le', # Koduje NOWĄ (drugą, jeśli była oryginalna) ścieżkę audio (nasz LTC) jako PCM 16-bit Little-Endian
                                   # UWAGA: Index `1` dla `-c:a:1` oznacza, że ta opcja będzie dotyczyć mapowanego strumienia audio z indeksu 1 (czyli `1:a:0`)
            '-shortest',          # Kończy kodowanie, gdy najkrótszy strumień się skończy
            '-y',                 # Nadpisuje plik wyjściowy bez pytania
            '-metadata', f"creation_time={start_datetime_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')}", # Dodaje metadane czasu utworzenia
            output_path
        ]

        print(f"FFmpeg command (final): {' '.join(command)}")

        try:
            # Użycie subprocess.run z przekierowaniem wyjścia dla lepszego debugowania
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"Pomyślnie dodano sygnał audio (LTC) do {video_path}. Plik zapisano jako {output_path}")
            if result.stdout:
                print("FFmpeg stdout (fragment):\n", result.stdout[-500:]) # Ostatnie 500 znaków
            if result.stderr:
                print("FFmpeg stderr (fragment):\n", result.stderr[-500:]) # Ostatnie 500 znaków
            return True
        except subprocess.CalledProcessError as e:
            print(f"Błąd FFmpeg podczas dodawania audio do {video_path}: {e}")
            print("FFmpeg stdout (pełny):\n", e.stdout)
            print("FFmpeg stderr (pełny):\n", e.stderr)
            return False
        except FileNotFoundError:
            print("Błąd: ffmpeg nie znaleziono. Upewnij się, że jest zainstalowany i dostępny w PATH.")
            return False
        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd podczas wywołania FFmpeg dla {video_path}: {e}")
            traceback.print_exc()
            return False
        finally:
            if os.path.exists(temp_ltc_audio_file):
                os.remove(temp_ltc_audio_file)
                print(f"Usunięto tymczasowy plik audio (LTC): {temp_ltc_audio_file}")

    def process_video(self, video_path: str) -> bool:
        """Przetwarza pojedynczy plik wideo, aby dodać ścieżkę audio (LTC)."""
        print(f"Przetwarzanie: {video_path}")
        try:
            duration_seconds, frame_rate = self._get_video_info(video_path)

            calculated_start_time_utc, qr_frame_index = self._read_qr_from_video(video_path, frame_rate)

            if calculated_start_time_utc:
                print(f"Znaleziono QR kod w klatce {qr_frame_index}: {calculated_start_time_utc.isoformat()}")
                print(f"Obliczony czas rozpoczęcia wideo (UTC): {calculated_start_time_utc}")
                return self._add_ltc_track_to_video(video_path, calculated_start_time_utc, frame_rate, duration_seconds)
            else:
                print(f"Pomijanie {video_path}: Nie znaleziono prawidłowego kodu QR lub błąd odczytu.")
                return False
        except ValueError as e:
            print(f"Wystąpił błąd podczas pobierania informacji o wideo dla {video_path}: {e}")
            return False
        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd podczas przetwarzania {video_path}: {e}")
            return False
