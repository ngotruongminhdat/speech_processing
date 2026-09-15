from check_pronunciation import convert_word_to_pronunciation, is_symbol

end_word_symbol = "\t"

def store_syllable(word: str, syllable_set: set, undf_set: set): 
    try:
        is_success, pronunciation =  convert_word_to_pronunciation(word)
        if is_success:
            syllable_set.add(word)
        else:
            undf_set.add(word)
    except:
        undf_set.add(word)


def split_syllable(line: str, syllable_set: set, undf_set: set): 
    end_word_symbol_index = line.find(end_word_symbol)

    if end_word_symbol_index > -1:
        text = line[:end_word_symbol_index]
    else:
        text = line

    text = text.lower()
    i = 0

    temp_word = ""

    while i < len(text):
        ch = text[i]
        
        if is_symbol(ch) or ch == "\n":
            if temp_word:
                store_syllable(temp_word, syllable_set, undf_set)
                temp_word = ""

            i += 1
            continue

        temp_word += ch
        i += 1

    if temp_word:
        store_syllable(temp_word, syllable_set, undf_set)
        temp_word = ""



# Mở file
with open("VDic_uni.txt", "r", encoding="utf-8") as f:
    syllable_set = set()
    undf_set = set()
    # Lặp qua từng dòng trong file
    for line in f:
        split_syllable(line, syllable_set, undf_set)
    
    # Mở file ở chế độ ghi
    with open("syllable.txt", "w", encoding="utf-8") as f:
        for line in sorted(syllable_set):
            f.write(line + "\n")  # mỗi chuỗi ghi thành một dòng

    with open("undefined.txt", "w", encoding="utf-8") as f:
        for line in sorted(undf_set):
            f.write(line + "\n")  # mỗi chuỗi ghi thành một dòng

    print(len(syllable_set))