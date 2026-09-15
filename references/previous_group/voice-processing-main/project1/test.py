from phonemizeText import phonemize_syllable, phonemize_text, step1_find_initial_consonant, step2_find_medial_vowel, step3_find_main_vowel, step4_find_final_consonant, step5_find_tone

def test_step1():
    """Test Bước 1: Tìm âm đầu"""
    test_cases = {
        "bè": "b",
        "bạn": "b",
        "mệt": "m",
        "mỏi": "m",
        "phờ": "f",
        "phạc": "f",
        "vờ": "v",
        "vĩnh": "v",
        "tí": "t",
        "tẹo": "t",
        "tha": "t'",
        "thướt": "t'",
        "đủng": "d",
        "đĩnh": "d",
        "no": "n",
        "nề": "n",
        "giày": "z",
        "da": "z",
        "bánh": "b",
        "dầy": "z",
        "rườm": "ʐ",
        "rà": "ʐ",
        "xa": "s",
        "xôi": "s",
        "san": "ʂ",
        "sẻ": "ʂ",
        "chim": "c",
        "chóc": "c",
        "trang": "ʈ",
        "trại": "ʈ",
        "nhí": "ɲ",
        "nhảnh": "ɲ",
        "lươn": "l",
        "lọeo": "l",
        "kim": "k",
        "kè": "k",
        "kẻ": "k",
        "kiểm": "k",
        "quả": "k",
        "quýt": "k",
        "quê": "k",
        "con": "k",
        "cà": "k",
        "cuống": "k",
        "khắt": "χ",
        "khe": "χ",
        "nghĩ": "ŋ",
        "nghèo": "ŋ",
        "nghiền": "ŋ",
        "ngõ": "ŋ",
        "ngáo": "ŋ",
        "ngớ": "ŋ",
        "ghi": "ɣ",
        "ghè": "ɣ",
        "ghế": "ɣ",
        "gà": "ɣ",
        "gõ": "ɣ",
        "gụ": "ɣ",
        "hát": "h",
        "hò": "h",
        "ăn": "",
        "uống": "",
        "uể": "",
        "oải": "",
        "huỳnh": "h"
    }
    
    print("=" * 60)
    print("TEST BƯỚC 1: TÌM ÂM ĐẦU")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():
        ipaVal, inital = step1_find_initial_consonant(test)
        is_correct = ipaVal == expected
        
        if is_correct:
            print(f"✅ <{test}><{ipaVal}> ✅")
            correct_count += 1
        else:
            print(f"❌  <{test}><{ipaVal}> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_step2():
    """Test Bước 2: Tìm âm đệm"""
    test_cases = {
        "quê": "w",
        "quả": "w",
        "quán": "w",
        "quyên": "w",
        "quẫn": "w",
        "quặn": "w",
        "quốc": "w",
        "huy": "w",
        "huế": "w",
        "huơ": "w",
        "huấn": "w",
        "huân": "w",
        "huyền": "w",
        "hữu": "",
        "hoa": "w",
        "hoe": "w",
        "hoác": "w",
        "họa": "w",
        "hoẵn": "w",
        "hể": "",
        "hà": "",
        "hiền": "",
        "hương": "",
        "bong": "",
        "boong": "",
        "xoong": "",
        "huỳnh": "w",
        "hoàng": "w",
        "lượng": ""
    }
    
    print("=" * 60)
    print("TEST BƯỚC 2: TÌM ÂM ĐỆM")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():
        ipa, sub = step2_find_medial_vowel(test)
        is_correct = ipa == expected
        
        if is_correct:
            if ipa:
                print(f"✅ <{test}><{ipa}> ✅")
            else:
                print(f"✅ <{test}><không có âm đệm> ✅")
            correct_count += 1
        else:
            if ipa:
                print(f"❌  <{test}><{ipa}> (mong muốn: <{expected}>)")
            else:
                print(f"❌  <{test}><không có âm đệm> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_step3():
    """Test Bước 3: Tìm âm chính"""
    test_cases = {
        # /-i-/
        "huy": "i",
        "thúy": "i",
        "quýt": "i",
        "ý": "i",
        "y": 'i',
        "im": "i",
        "đi": "i",
        "nhìn": "i",
        "mình": "i",

        # /-e-/
        "lên": "e",
        "bên": "e",
        "tênh": "e",

        # /-ɛ-/
        "em": "ɛ",
        "mẹ": "ɛ",
        "kẻm": "ɛ",

        # /-ɯ-/
        "từ": "ɯ",
        "chữ": "ɯ",
        "từng": "ɯ",

        # /-ɤ-/
        "trơn": "ɤ",
        "mơ": "ɤ",
        "lớp": "ɤ",

        # /-a-/
        "má": "a",
        "mái": "a",
        "qua": "a",
        "lại": "a",

        # /-u-/
        "dù": "u",
        "súng": "u",

        # /-o-/
        "cô": "o",
        "bốn": "o",
        "boong": "ɔ",

        # /-ɔ-/
        "con": "ɔ",
        "có": "ɔ",
        "đói": "ɔ",
        "xoong": "ɔ",

        # /-ɤ̆-/
        "trần": "ɤ̆",
        "sân": "ɤ̆",
        "tầng": "ɤ̆",

        # /-ɛ̆-/
        "anh": "ɛ̆",
        "ách": "ɛ̆",
        "nhanh": "ɛ̆",
        "nhách": "ɛ̆",

        # /-aː-/
        "rau": "ă",
        "tay": "ă",
        "quay": "ă",

        # /-ă-/
        "ăn": "ă",
        "năn": "ă",
        "chăn": "ă",
        "đắng": "ă",

        # /-ɔ̆-/
        "ong": "ɔ̆",
        "óc": "ɔ̆",
        "mong": "ɔ̆",
        "móc": "ɔ̆",
        "bong": "ɔ̆",

        # /-iə-/
        "biển": "ie",
        "biếng": "ie",
        "khuyên": "ie",
        "yếu": "ie",
        "yểng": "ie",
        "yểm": "ie",
        "bia": "ie",
        "mía": "ie",
        "tía": "ie",
        "khuya": "ie",
        "tuya": "ie",

        # /-ɯɤ-/
        "ươn": "ɯɤ",
        "lươn": "ɯɤ",
        "bướng": "ɯɤ",
        "hươu": "ɯɤ",
        "mưa": "ɯɤ",
        "ưa": "ɯɤ",
        "chưa": "ɯɤ",

        # /-uo-/
        "buồn": "uo",
        "uống": "uo",
        "ùa": "uo",
        "chùa": "uo",

        "huỳnh": "i",
        "hoàng": "ɛ̆",
        "lượng": "ɯɤ"
    }
    
    print("=" * 60)
    print("TEST BƯỚC 3: TÌM ÂM CHÍNH")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():        
        ipa, main = step3_find_main_vowel(test)
        is_correct = ipa == expected
        
        if is_correct:
            print(f"✅ <{test}><{ipa}> ✅")
            correct_count += 1
        else:
            print(f"❌  <{test}><{ipa}> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_step4():
    """Test Bước 4: Tìm âm cuối"""
    test_cases = {
        # /-m/
        "ôm": "m",
        "nam": "m",
        "nem": "m",

        # /-n/
        "ôn": "n",
        "nan": "n",
        "nén": "n",

        # /-p/
        "ốp": "p",
        "hấp": "p",

        # /-t/
        "ắt": "t",
        "hát": "t",

        # /-ŋ/
        "inh": "ŋ",
        "ểnh": "ŋ",
        "anh": "ŋ",
        "xinh": "ŋ",
        "mệnh": "ŋ",
        "xanh": "ŋ",

        # /-ŋ/
        "ong": "ŋ",
        "ông": "ŋ",
        "ung": "ŋ",
        "keng": "ŋ",
        "kiểng": "ŋ",

        # /-k/
        "ích": "k",
        "ếch": "k",
        "ách": "k",
        "thích": "k",
        "chệch": "k",
        "bạch": "k",
        "óc": "k",
        "úc": "k",
        "ác": "k",
        "cóc": "k",
        "cúc": "k",
        "các": "k",
        "lắc": "k",
        "nắc": "k",

        # /-w/
        "áo": "w",
        "éo": "w",
        "báo": "w",
        "béo": "w",
        "au": "w",
        "eo": "w",
        "êu": "w",
        "iu": "w",
        "châu": "w",
        "kêu": "w",
        "chịu": "w",

        # /-j/
        "cáy": "j",
        "cấy": "j",
        "cái": "j",
        "ngoái": "j",
        "cưới": "j",
        "cuối": "j",

        # /zero/ (không âm cuối)
        "bà": "",
        "bố": "",
        "mẹ": "",

        "huỳnh": "ŋ",
        "hoàng": "ŋ",

        "lượng": "ŋ"
    }
    
    print("=" * 60)
    print("TEST BƯỚC 4: TÌM ÂM CUỐI")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():
        ipa, last = step4_find_final_consonant(test)
        is_correct = ipa == expected
        
        if is_correct:
            if ipa:
                print(f"✅ <{test}><{ipa}> ✅")
            else:
                print(f"✅ <{test}><không có âm cuối> ✅")
            correct_count += 1
        else:
            if ipa:
                print(f"❌  <{test}><{ipa}> (mong muốn: <{expected}>)")
            else:
                print(f"❌  <{test}><không có âm cuối> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_step5():
    """Test Bước 5: Tìm dấu"""    
    test_cases = {
        "nếu": "5",  # có dấu sắc
        "anh": "1",  # không có dấu
        "chương": "1",  # không có dấu
        "trình": "2",  # không có dấu
        "phương": "1",  # không có dấu
        "không": "1",  # không có dấu
        "nghề": "2",  # có dấu huyền
        "giấu": "5",  # có dấu sắc
        "quan": "1",  # không có dấu
        "cảm": "4",  # có dấu ngã
        "trang": "1",  # không có dấu
        "huy": "1",  # không có dấu
        "bạn": "6",  # có dấu nặng
        "mẹ": "6",  # có dấu nặng
        "vui": "1",  # không có dấu
        "thương": "1",  # không có dấu
        "dân": "1",  # không có dấu
        "nước": "5",  # có dấu sắc
        "rồi": "2",  # có dấu huyền
        "xanh": "1",  # không có dấu
        "sống": "5",  # có dấu nặng
        "lớn": "5",  # có dấu sắc
        "ghế": "5",  # có dấu sắc
        "gì": "2",  # có dấu huyền
        "hỏi": "4"   # có dấu hỏi
    }
    
    print("=" * 60)
    print("TEST BƯỚC 5: TÌM DẤU")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():
        actual = step5_find_tone(test)
        is_correct = actual == expected
        
        if is_correct:
            print(f"✅ <{test}><{actual}> ✅")
            correct_count += 1
        else:
            print(f"❌  <{test}><{actual}> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_combined():
    """Test ghép chữ lại"""    
    test_cases = {
        "nếu": "new5",
        "anh": "ɛ̆ŋ1",
        "chương": "cɯɤŋ1",
        "trình": "ʈiŋ2",
        "phương": "fɯɤŋ1",
        "không": "χoŋ1",
        "nghề": "ŋe2",
        "giấu": "zɤ̆w5",
        "quan": "kwan1",
        "cảm": "kam4",
        "trang": "ʈɛ̆ŋ1",
        "huy": "hwi1",
        "bạn": "ban6",
        "mẹ": "mɛ6",
        "vui": "vwi1",
        "thương": "t'ɯɤŋ1",
        "dân": "zɤ̆n1",
        "nước": "nɯɤk5",
        "rồi": "ʐoj2",
        "xanh": "sɛ̆ŋ1",
        "sống": "ʂoŋ5",
        "lớn": "lɤn5",
        "ghế": "ɣe5",
        "gì": "zj2",
        "hỏi": "hɔj4",
        "xuân": "swɤ̆n1",
        "chồng": "coŋ2",
        "án": "an5",
        "xuệch": "swek6",
        "xoạc": "swak6",
        "xuềnh": "sweŋ2",
        "xoàng": "swɛ̆ŋ2",
        "xuề": "swe2",
        "xoà": "swa2",
        "má": "ma5",
        "ác": "ak5",
        "khuya": "χwie1",
        "toán": "twan5",
        "đoái": "dwaj5",
        "hoài": "hwaj2",
        "bố": "bo5",
        "nghiệt": "ŋiet6",
        "nghiêng": "ŋieŋ1",
        "tiền": "tien2",
        "cuối": "kuoj5"
    }
    
    print("=" * 60)
    print("TEST GHÉP CHỮ LẠI")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():
        actual = phonemize_syllable(test)
        is_correct = actual == expected
        
        if is_correct:
            print(f"✅ <{test}><{actual}> ✅")
            correct_count += 1
        else:
            print(f"❌  <{test}><{actual}> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_sentence():
    """Test cả câu"""    
    test_cases = {
        "xin chào bạn": "sin1 căw2 ban6",
        "cảm ơn bạn": "kam4 ɤn1 ban6",
        "hẹn gặp lại": "hɛn6 ɣăp6 laj6",
        "ang áng": "ɛ̆ŋ1 ɛ̆ŋ5"
    }
    
    print("=" * 60)
    print("TEST CẢ CÂU")
    print("=" * 60)
    print("Format: <input><output>")
    print("-" * 60)
    
    correct_count = 0
    total_count = len(test_cases)
    
    for test, expected in test_cases.items():
        actual = phonemize_text(test)
        is_correct = actual == expected
        
        if is_correct:
            print(f"✅ <{test}><{actual}> ✅")
            correct_count += 1
        else:
            print(f"❌  <{test}><{actual}> (mong muốn: <{expected}>)")
    
    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")

def test_phonemize_text():
    """Test hàm phonemize_text với nhiều câu"""
    test_cases = {
        "Làm sao sống được mà không yêu":
        "lam2 ʂăw1 ʂoŋ5 dɯɤk6 ma2 χoŋ1 iew1",
        "Không nhớ, không thương một người nào":
        "χoŋ1 ɲɤ5, χoŋ1 t'ɯɤŋ1 mot6 ŋɯɤj2 năw2",
        "Nếu biết rằng em đã có chồng":
        "new5 biet5 ʐăŋ2 ɛm1 da3 kɔ5 coŋ2",
        "Trời ơi! Người ấy có buồn không":
        "ʈɤj2 ɤj1! ŋɯɤj2 ɤ̆j5 kɔ5 buon2 χoŋ1",
        "Trời, còn có bữa sao quên mọc":
        "ʈɤj2, kɔn2 kɔ5 bɯɤ3 ʂăw1 kwen1 mɔ̆k6",
        "Anh, chẳng đêm nào chẳng nhớ em":
        "ɛ̆ŋ1, căŋ4 dem1 năw2 căŋ4 ɲɤ5 ɛm1",
        "Sầu đong càng lắc càng đầy":
        "ʂɤ̆w2 dɔ̆ŋ1 kɛ̆ŋ2 lăk5 kɛ̆ŋ2 dɤ̆j2",
        "Ba thu dồn lại một ngày dài ghê.":
        "ba1 t'u1 zon2 laj6 mot6 ŋăj2 zaj2 ɣe1.",
        "Buồn trông cửa bể chiều hôm":
        "buon2 ʈoŋ1 kɯɤ4 be4 ciew2 hom1",
        "Thuyền ai thấp thoáng cánh buồm xa xăm":
        "t'wien2 aj1 t'ɤ̆p5 t'wɛ̆ŋ5 kɛ̆ŋ5 buom2 sa1 săm1"
    }
    correct_count = 0
    total_count = len(test_cases)

    for input_text, expected_output in test_cases.items():
        actual_output = phonemize_text(input_text)
        is_correct = actual_output == expected_output

        if is_correct:
            print(f"✅ <{input_text}><{actual_output}> ✅")
            correct_count += 1
        else:
            print(f"❌  <{input_text}><{actual_output}> (mong muốn: <{expected_output}>)")

    print("-" * 60)
    print(f"KẾT QUẢ: {correct_count}/{total_count} test cases đúng ({correct_count/total_count*100:.1f}%)")


if __name__ == "__main__":
    # Test Bước 1
    test_step1()
    print("\n")
    
    # Test Bước 2
    test_step2()
    print("\n")
    
    # # Test Bước 3
    test_step3()
    print("\n")
    
    # Test Bước 4
    test_step4()
    print("\n")
    
    # # Test Bước 5
    test_step5()
    print("\n")
    
    # # Test ghép chữ lại
    test_combined()
    print("\n")
    
    # # Test cả câu
    test_sentence()

    test_phonemize_text()


