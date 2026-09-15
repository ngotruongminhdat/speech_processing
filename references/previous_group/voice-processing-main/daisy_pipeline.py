from align_to_dtbook import create_dtbook
from alignment import alignment
from correct_align import correct_text
from create_daisy_file import create_daisy_file
from create_dir import create_dir
from map_to_smill import generate_smil
import os
import shutil

BASE_OUTPUT_DIR="./output"

range = range(1, 2)
# range = range(1, 71)

# Tạo thư mục output cho các hồi
create_dir(range, BASE_OUTPUT_DIR)

for i in range:
    try:
        INPUT_AUDIO_FILE = f"./audio/Thuy-Hu-{i}.mp3"
        DOC_INPUT = f"./doc/Hoi{i}.docx"

        OUTPUT_DIR=f"[Thuỷ Hử] Hồi {i}"

        SPEECH_TO_TEXT_OUTPUT = f"./alignResult/hoi{i}_aligned_result.json"
        CORRECT_TEXT_OUTPUT = f"./alignResult/hoi{i}_aligned_result_corrected.json"
        DTBOOK_OUTPUT = os.path.join(BASE_OUTPUT_DIR, OUTPUT_DIR, "dtbook.xml")
        SMIL_OUTPUT = os.path.join(BASE_OUTPUT_DIR, OUTPUT_DIR, "mo0.smil")
        AUDIO_NAME = f"Hoi{i}.mp3"

        AUDIO_DES=os.path.join(BASE_OUTPUT_DIR, OUTPUT_DIR,AUDIO_NAME)
        BOOK_OUTPUT=os.path.join(BASE_OUTPUT_DIR,OUTPUT_DIR,"book.opf")
        NAVIGATION_OUTPUT=os.path.join(BASE_OUTPUT_DIR, OUTPUT_DIR, "navigation.ncx")
        RESOURCE_OUTUPT=os.path.join(BASE_OUTPUT_DIR, OUTPUT_DIR,"resources.res")

        # Bước 1: Chạy speech to text
        alignment(INPUT_AUDIO_FILE, SPEECH_TO_TEXT_OUTPUT)
        # Bước 3: Dùng LLM correct chính tả
        correct_text(SPEECH_TO_TEXT_OUTPUT, DOC_INPUT, CORRECT_TEXT_OUTPUT)
        # Bước 4: Tạo file dtbook
        create_dtbook(CORRECT_TEXT_OUTPUT, i, DTBOOK_OUTPUT)
        # Bước 5: Tạo file smil
        generate_smil(DTBOOK_OUTPUT, CORRECT_TEXT_OUTPUT, SMIL_OUTPUT, AUDIO_NAME)
        # Bước 6: Tạo file book.opf, navigation.ncx, resources.res
        create_daisy_file(BOOK_OUTPUT, NAVIGATION_OUTPUT, RESOURCE_OUTUPT, i)

        shutil.copy(INPUT_AUDIO_FILE, AUDIO_DES)

        print(f"Đã copy {INPUT_AUDIO_FILE} sang {AUDIO_DES}")
        print(f"Tạo dasy book thành công cho {OUTPUT_DIR}")
    except:
        print(f"Tạo dasy book  {OUTPUT_DIR} thất bại")
