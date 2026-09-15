import re
import unicodedata
from mappings import am_dau_map, am_chinh_map, am_cuoi_map, TONE_DIACRITIC_TO_NUM

def remove_tone_diacritics(text):
    # Chuẩn hóa về NFD để tách base + diacritics
    normalized = unicodedata.normalize('NFD', text)
    # Bỏ các dấu thanh nhưng giữ nguyên nguyên âm có mũ, móc
    result = ''.join(c for c in normalized if c not in TONE_DIACRITIC_TO_NUM)
    # Chuẩn hóa về NFC để ghép ký tự lại
    output = unicodedata.normalize('NFC', result)
    return output

def step1_find_initial_consonant(syllable):
    syllable = remove_tone_diacritics(syllable)
    """
    Bước 1: Tìm âm đầu
    - Kiểm tra xem âm tiết có bắt đầu bằng phụ âm đầu nào trong am_dau_map
    - Nếu không có thì là zero (không thể hiện)
    """
    
    if not syllable:
        # Không có âm tiết -> âm đầu = zero"
        return "", syllable
    
    # Tạo danh sách tất cả các phụ âm đầu có thể có (từ cột 2 của am_dau_map)
    all_possible_initials = []
    for ipa_key, vietnamese_values in am_dau_map.items():
        all_possible_initials.extend(vietnamese_values)
    
    # Loại bỏ các giá trị rỗng và sắp xếp theo độ dài (dài trước)
    all_possible_initials = [init for init in all_possible_initials if init != ""]
    all_possible_initials.sort(key=len, reverse=True)
        
    # Kiểm tra từ phụ âm dài nhất đến ngắn nhất
    for initial in all_possible_initials:
        if syllable.startswith(initial):
            # Tìm IPA tương ứng
            for ipa_key, vietnamese_values in am_dau_map.items():
                if initial in vietnamese_values:
                    ipa_value = ipa_key.strip('/-')
                    return ipa_value, initial
    return "", ""

def step2_find_medial_vowel(syllable):
    syllable = remove_tone_diacritics(syllable)
    """
    Bước 2: Tìm âm đệm (2 bán nguyên âm u và o)
    
    Trường hợp u:
    - Điều kiện 1: Âm đầu là chữ "q"
    - Điều kiện 2: Âm chính /-i-/, /-e-/, /-ɤ-/, /-ɤ̆-/, /-ie-/
    
    Trường hợp o:
    - Các trường hợp còn lại
    
    Không thể hiện:
    - Các trường hợp khác
    """

    # Tìm âm đầu
    initial_ipa_value, initial = step1_find_initial_consonant(syllable)

    core = syllable

    # Remove initial
    if initial:
        core = core[len(initial):]
        
    if len(core) >= 2:
        vowel = core[0]
        if vowel == "u":
            if initial == "q":
                return "w", vowel
            goWithU = ["y", "i", "ê", "ơ", "â", "iê", "yê", "ia", "ya"]
            pattern = r"^u(" + "|".join(goWithU) + ")"
            if re.match(pattern, core):
                return "w", vowel
        elif vowel == "o":
            goWithO = ["a", "ă", "e"]
            pattern = r"^o(" + "|".join(goWithO) + ")"
            if re.match(pattern, core):
                return "w", vowel
    return "", ""  

def step3_find_main_vowel(syllable):
    syllable = remove_tone_diacritics(syllable)
    """
    Bước 3: Tìm âm chính
    - Tìm âm đầu và âm cuối trước, loại bỏ ký tự của chúng khỏi syllable
    - Sau đó xác định âm chính từ phần còn lại
    """
    if not syllable:
        return "", syllable

    # Tìm âm đầu
    initial_ipa_value, initial = step1_find_initial_consonant(syllable)
    last_ipa_value, last = step4_find_final_consonant(syllable)
    sub_ipa_value, sub = step2_find_medial_vowel(syllable)

    # Loại bỏ ký tự đầu (initial) và cuối (last) khỏi syllable
    core = syllable
    if initial:
        core = core[len(initial):]
    if sub:
        core = core[len(sub):]
    if last:
        if len(core) >= 2 and core[-2:] == last:
            core = core[:-2]
        elif len(core) >= 1 and core[-1:] == last:
            core = core[:-1]
        
    if not core:
        return "", syllable
    
    # Exception
    # if (core.endswith('ua') or core.endswith('uô')) and initial == 'q':
    #     return "a", "a"

    # Kiểm tra các nguyên âm phức tạp trước (dài nhất trước)
    complex_vowels = ['iê', 'yê', 'ia', 'ya', 'ươ', 'ưa', 'uô', 'ua', 'ôô', 'oo']
    for vowel in complex_vowels:
        if core.endswith(vowel):
            for ipa_key, vietnamese_values in am_chinh_map.items():
                if vowel in vietnamese_values:
                    ipa_value = ipa_key.strip('/-')
                    return ipa_value, vowel
    # Chỉ còn case 1 ký tự
    main_char = core[len(core) - 1]

    # Xử lý trường hợp đặc biệt "o"
    # âm tiết đóng (kết thúc bằng phụ âm -c, -ng, -p) -> ɔ̆, ngược lại thì ɔ
    closed_syllable = ["c", "ng" ,"p", "t"]
    if main_char == 'o':
        if last in closed_syllable:
            return "ɔ̆", "o"
        else:
            return "ɔ", "o"

    # Xử lý đặc biệt cho âm chính "a"
    if main_char == 'a':
        # Trường hợp 1: "/-ă-/": ["a"] # (+ âm cuối /-w/, /-j -> Chỉ y dài thoi vì loại trường hợp "mái"/)
        if last in ['o', 'u', 'y']:
            return 'ă', 'a'
        # Trường hợp 2: "/-ɛ̆-/": ["a"] # Nếu âm cuối là nh, ng, ch
        if last in ["nh", "ng", "ch"]:
            return 'ɛ̆', 'a'
        else:
            return 'a', 'a'

    # Xử lý các nguyên âm khác
    for ipa_key, vietnamese_values in am_chinh_map.items():
        if main_char in vietnamese_values:
            ipa_value = ipa_key.strip('/-')
            return ipa_value, main_char

    # Không tìm thấy âm chính
    return "", syllable

def step4_find_final_consonant(syllable):
    syllable = remove_tone_diacritics(syllable)
    """
    Bước 4: Tìm âm cuối
    - Lấy 2 ký tự cuối, nếu khớp final thì tách, nếu không thì lấy 1 ký tự cuối, nếu khớp thì tách, không thì trả về rỗng
    """
    finals = []
    for vals in am_cuoi_map.values():
        finals.extend(vals)
    finals = [f for f in finals if f]  # bỏ rỗng
    finals = set(finals)

    initial_ipa_value, initial = step1_find_initial_consonant(syllable)
    sub_ipa, sub = step2_find_medial_vowel(syllable)

    special_case = ["y", "i", "o" ,"u"] # trùng với âm chính
    # Nếu bỏ đi cả âm đệm và âm đầu mà chỉ còn 1 ký tự => đó phải là âm chính => âm cuối ko thể hiện
    len_first_sub = len(initial) + len(sub)

    core = syllable[len_first_sub:]

    if len(core) == 1 and special_case.__contains__(core):
        return "" , ""

    # Ưu tiên kiểm tra 2 ký tự cuối
    if len(syllable) >= 2:
        last = syllable[-2:]
        if last in finals:
            # Tìm IPA key tương ứng
            for ipa_key, vals in am_cuoi_map.items():
                if last in vals:
                    ipa_value = ipa_key.strip('/-')
                    return ipa_value, last
    # Nếu không, kiểm tra 1 ký tự cuối
    if len(syllable) >= 1:
        last = syllable[-1]
        if last in finals:
            for ipa_key, vals in am_cuoi_map.items():
                if last in vals:
                    ipa_value = ipa_key.strip('/-')
                    return ipa_value, last

    # Không có âm cuối
    return "", ""

def step5_find_tone(syllable):
    """
    Bước 5: Tìm dấu (thanh điệu)
    - Tra cứu trong TONE_DIACRITIC_TO_NUM để tìm dấu thanh điệu
    - Mặc định là thanh 1 (không có dấu)
    """
    if not syllable:
        return "1"
    # Chuẩn hóa về NFD để tách dấu ra khỏi ký tự gốc
    normalized = unicodedata.normalize('NFD', syllable)
    for char in normalized:
        if char in TONE_DIACRITIC_TO_NUM:
            return TONE_DIACRITIC_TO_NUM[char]
    return "1"

def step6_combine_phonemes(initial, medial, main, final, tone):
    """
    Bước 6: Ghép kết quả
    - Nối các thành phần âm tiết lại với nhau
    - Thêm thanh điệu (chỉ hiển thị nếu không phải thanh 1)
    """
    
    result = ""
    
    # Thêm âm đầu
    if initial:
        result += initial
    
    # Thêm âm đệm (bỏ qua nếu là zero)
    if medial and medial != "":
        result += medial
    
    # Thêm âm chính
    if main:
        result += main
    
    # Thêm âm cuối (bỏ qua nếu là zero)
    if final and final != "":
        result += final
    
    result += tone
    
    return result

def phonemize_syllable(syllable):
    """
    Phiên âm một âm tiết theo các bước
    """
        
    # Bước 1: Tìm âm đầu
    initial, init = step1_find_initial_consonant(syllable)

    # Bước 2: Tìm âm đệm
    medial, init_sub = step2_find_medial_vowel(syllable)

    # Bước 2: Tìm âm chính
    main, init_main = step3_find_main_vowel(syllable)

    # Bước 4: Tìm âm cuối
    final, init_last = step4_find_final_consonant(syllable)
    
    # Bước 5: Tìm dấu
    tone = step5_find_tone(syllable)

    # Bước 6: Ghép kết quả
    result = step6_combine_phonemes(initial, medial, main, final, tone)

    # print(f"initial: {initial}, medial: {medial}, main: {main}, final: {final}, tone: {tone}")
    
    return result

def phonemize_text(text):
    """
    Phiên âm toàn bộ văn bản
    - Đầu vào: chuỗi text
    - Đầu ra: chuỗi phiên âm
    """
    
    # Tách thành các từ (giả sử mỗi từ là một âm tiết)
    text = text.lower()
    # Tách từ và dấu câu riêng (giữ dấu câu)
    words = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    phonemized_words = []
    # print(words)
    for word in words:
        if re.match(r'\w+', word, re.UNICODE):
            phoneme = phonemize_syllable(word)
            phonemized_words.append(phoneme)
        else:
            phonemized_words.append(word)
    # Ghép lại, đảm bảo không có dấu cách trước dấu câu
    result = ""
    for i, w in enumerate(phonemized_words):
        if i > 0 and re.match(r'\w+', phonemized_words[i-1], re.UNICODE) and re.match(r'\w+', w, re.UNICODE):
            result += " "
        elif i > 0 and re.match(r'\w+', phonemized_words[i-1], re.UNICODE) and not re.match(r'\w+', w, re.UNICODE):
            result += ""
        elif i > 0:
            result += " "
        result += w
    return result


if __name__ == "__main__":

    # Nhập văn bản từ người dùng
    print("\n" + "=" * 60)
    print("NHẬP VĂN BẢN TIẾNG VIỆT ĐỂ PHIÊN ÂM:")
    print("=" * 60)
    user_input = input()
    result = phonemize_text(user_input)
    print(f"\nKẾT QUẢ PHIÊN ÂM: {result}")
