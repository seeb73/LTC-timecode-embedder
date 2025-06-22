import sys
import os # <-- Dodano to

# Dynamicznie dodaj katalog 'external_libs' do sys.path
# Zakładamy, że 'external_libs' jest w tym samym katalogu co 'main.py'
current_script_dir = os.path.dirname(os.path.abspath(__file__))
external_libs_path = os.path.join(current_script_dir, 'external_libs')
if external_libs_path not in sys.path:
    sys.path.insert(0, external_libs_path)

# Teraz możesz bezpiecznie importować swoje moduły
from video_processor import VideoProcessor
import argparse

def main():
    parser = argparse.ArgumentParser(description="Przetwarza pliki wideo, dodając ścieżki audio LTC oparte na kodach QR GoPro.")
    parser.add_argument("input_dir", help="Ścieżka do katalogu wejściowego zawierającego pliki wideo.")
    parser.add_argument("output_dir", help="Ścieżka do katalogu wyjściowego, gdzie zostaną zapisane przetworzone pliki wideo.")
    
    args = parser.parse_args()

    processor = VideoProcessor(args.output_dir, args.input_dir)
    
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', "mts") # Dodaj więcej rozszerzeń, jeśli potrzebujesz
    
    found_files = []
    print(f"Scanning for video files in: {args.input_dir}/")
    print("-----------------------------------")
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if file.lower().endswith(video_extensions):
                found_files.append(os.path.join(root, file))

    if not found_files:
        print(f"Nie znaleziono żadnych plików wideo w: {args.input_dir}")
        return

    for video_file in found_files:
        processor.process_video(video_file)

if __name__ == "__main__":
    main()
