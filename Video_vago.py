import os
import subprocess

# ==============================================================================
# KONFIGURÁCIÓ
# ==============================================================================
input_folder = r"D:\eredeti_videok"
output_folder = r"K:\0 Szakdolgozat\vagott_videok"

start_trim = 10
end_trim = 5
total_length = 60


vagas_vege = total_length - end_trim 

# ==============================================================================
# FELDOLGOZÁS
# ==============================================================================

if not os.path.exists(input_folder):
    print(f"[HIBA] Nem található a bemeneti mappa: {input_folder}")
    exit()

if not os.path.exists(output_folder):
    try:
        os.makedirs(output_folder)
        print(f"Kimeneti mappa létrehozva: {output_folder}")
    except OSError as e:
        print(f"[HIBA] Nem sikerült létrehozni a mappát.\n{e}")
        exit()

files = [f for f in os.listdir(input_folder) if f.lower().endswith('.avi')]

print(f"\nÖsszesen {len(files)} videó feldolgozása...\n" + "="*40)

for file_name in files:
    input_path = os.path.join(input_folder, file_name)
    output_path = os.path.join(output_folder, file_name)
    
    command = [
        "ffmpeg", 
        "-y",             
        "-i", input_path,
        "-ss", str(start_trim),
        "-to", str(vagas_vege),
        "-c", "copy", 
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[OK] {file_name}")
    except subprocess.CalledProcessError:
        print(f"[HIBA] FFmpeg hiba ennél a fájlnál: {file_name}")
    except FileNotFoundError:
        print("KRITIKUS HIBA: Az 'ffmpeg' parancs nem található!")
        break
    except Exception as e:
        print(f"[HIBA] Váratlan hiba: {e}")

print("\n" + "="*40 + "\nFeldolgozás befejezve!")
