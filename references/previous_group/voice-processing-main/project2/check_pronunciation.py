from io import StringIO
from json import load

initial_dict = load(open("initial_dict.json", "r", encoding="utf-8"))

vowel_tone_dict = load(open("vowel_tone_dict.json", "r", encoding="utf-8"))

medial_dict = load(open("medial_dict.json", "r", encoding="utf-8"))

nucleus_dict = load(open("nucleus_dict.json", "r", encoding="utf-8"))

coda_dict = load(open("coda_dict.json", "r", encoding="utf-8"))

head_consonant_dict = {
    "b": None,
	"c": {
		"h": None  
	}, 
	"d": None,
	"đ": None,
	"g": {
		"i": None,
		"h": None
	},
	"h": None,
	"k": {
		"h": None
	},
	"l": None,
	"m": None,
	"n": {
		"h": None,
		"g": {
			"h": None
		}
	},
	"p": { 
		"h": None
	},
	"q": {
		"u": None
	}, 
	"r": None,
	"s": None,
	"t": { 
		"h": None,
		"r": None
	},
	"v": None, 
	"x": None
}

medial_rule_dict = {
    "u": { "y", "ê", "ơ", "â" },
    "o": { "a", "ă", "e" }
} 

double_vowel_rule_dict = {
    "i": { "ê", "a" },
    "y": { "ê", "a" },
    "u": { "ô", "a" },
    "ư": { "ơ", "a" },
    "o": { "o" },
    "ô": { "ô" }
}

sepecial_single_vowel_rule_dict = {
    "a": {
        "nh": "a1",
        "ch": "a1",
        "u": "a2",
        "y": "a2",
    },
    "o" : {
        "ng": "o1",
        "c": "o1",
    }
}

symbol_set = {
    " ", "(", ")", "-", "=", "+", "[", "]", "{", "}", ";", ":", "'", '"', ",", ".", "<", ">", "/", "?", "!", "@", "#", "$", "%", "^", "&", "*", "~", "`"
}

_sentinel = object()

def is_symbol(ch: str) -> bool:
    return ch in symbol_set


def split_head_consonant_to_pronunciation(current_char: str, current_index: int, head_consonant_dict: dict| None, word: str) -> tuple[str, int]:
    next_index = current_index + 1
    if head_consonant_dict is None or next_index >= len(word):
        return current_char, current_index

    result = current_char

    next_word = word[next_index]

    next_consonant_dict = head_consonant_dict.get(next_word, _sentinel)

    if next_consonant_dict is _sentinel:
        return result, current_index
    
    next_consonant, current_index = split_head_consonant_to_pronunciation(next_word, next_index, next_consonant_dict, word)

    result += next_consonant
    return result, current_index

def head_consonant_to_pronunciation(head_consonant: str) -> str:
    return initial_dict.get(head_consonant)

def split_tone_form_word(word: str, index: int) -> tuple[str, str]:
    if index >= len(word):
        return "", ""
    
    result = ""

    # Mặc định là thanh ngang
    tone = "1"

    while index < len(word):
        ch = word[index]

        vowel, tone = vowel_tone_dict.get(ch, (None, "1"))
        if vowel:
            result += vowel
            result += word[index + 1:] if index + 1 < len(word) else ""
            break
        else:
            result += ch
        
        index += 1

    return result, tone

def split_medial_to_pronunciation(word: str, index: int) -> tuple[str, int]:
    if index >= len(word) - 1:
        return "", index
    
    current_char = word[index]

    medial_rule_set = medial_rule_dict.get(current_char, None)
    if medial_rule_set is None:
        return "", index

    next_char = word[index + 1]
    if next_char not in medial_rule_set:
        return "", index
    
    result = medial_dict.get(current_char, None)
    if result is None:
        return "", index
    
    return result, index + 1

def split_coda(word: str, index: int) -> tuple[str, int]:
    coda = ""

    while index < len(word):
        coda += word[index]
        index += 1
    
    return coda, index

def coda_to_pronunciation(coda: str) -> str:
    coda_pronunciation = coda_dict.get(coda, None)
    if coda_pronunciation is None:
        raise ValueError(f"Không tìm thấy cách phát âm cho phụ âm cuối '{coda}'")

    return coda_pronunciation


def split_coda_to_pronunciation(word: str, index: int) -> tuple[str, int]:
    coda, index = split_coda(word, index)
    if not coda:
        return "", index

    coda_pronunciation = coda_to_pronunciation(coda)
    return coda_pronunciation, index
    

def split_nucleus_to_pronunciation(word: str, index: int) -> tuple[str, int]:
    if index >= len(word):
        return "", index
    
    current_char = word[index]

    # Kiểm tra nguyên âm đôi
    double_vowel_rule_set = double_vowel_rule_dict.get(current_char, None)
    if double_vowel_rule_set is not None and index < len(word) - 1:
        next_char = word[index + 1]
        if next_char in double_vowel_rule_set:
            result = nucleus_dict.get(current_char + next_char, None)
            if result:
                return result, index + 2
    
    # Kiểm tra nguyên âm đơn

    # --Kiểm tra nguyên âm đơn có nhiều hơn 1 cách phát âm
    special_single_vowel_rule_set = sepecial_single_vowel_rule_dict.get(current_char, None)
    if special_single_vowel_rule_set is not None:
        coda, index = split_coda(word, index + 1)
        vowel = special_single_vowel_rule_set.get(coda, None)
        vowel = vowel if vowel else current_char
        result = nucleus_dict.get(vowel, None)
        if result is None:
            raise ValueError(f"Không tìm thấy cách phát âm cho nguyên âm '{vowel}'")
            
        if coda:
            coda_pronunciation = coda_to_pronunciation(coda)
            result += coda_pronunciation
        return result, index

    # -- Xư lý nguyên âm đơn có 1 cách phát âm
    result = nucleus_dict.get(current_char, None)
    if result is None:
        return "", index

    return result, index + 1
    
    
def convert_word_to_pronunciation(word: str) -> tuple[bool, str]:
    result = StringIO()
    is_have_nucleus = False
    is_success = False

    # Xử lý phụ âm đầu
    i = 0
    head_char = word[i]
    head_consonant = head_consonant_dict.get(head_char, _sentinel)
    if head_consonant is not _sentinel:
        head_consonant, i = split_head_consonant_to_pronunciation(head_char, i, head_consonant, word)

        initial = head_consonant_to_pronunciation(head_consonant)
        if initial:
            result.write(initial)
        
        i += 1

    # Xử lý dấu thanh
    # -- Sau khi tách dấu thanh, word sẽ chỉ còn thành phần "Vần"
    word, tone = split_tone_form_word(word, i)

    i = 0

    # Xử lý âm đệm
    medial, i = split_medial_to_pronunciation(word, i)
    if medial:
        result.write(medial)
    
    # Xử lý âm chính
    nucleus, i = split_nucleus_to_pronunciation(word, i)
    if nucleus:
        result.write(nucleus)
        is_have_nucleus = True

    # Xử lý âm cuối
    coda, i = split_coda_to_pronunciation(word, i)
    if coda:
        result.write(coda)

    # Thêm dấu thanh
    result.write(tone)

    is_success = is_have_nucleus

    return is_success, result.getvalue()

def convert_text_to_pronunciation(text: str) -> str: 
    result = StringIO()
    text = text.lower()
    i = 0

    temp_word = ""

    while i < len(text):
        ch = text[i]
        
        if is_symbol(ch) or ch == "\n":
            if temp_word:
                result.write(convert_word_to_pronunciation(temp_word))
                temp_word = ""

            result.write(ch)
            i += 1
            continue

        temp_word += ch
        i += 1

    if temp_word:
        result.write(convert_word_to_pronunciation(temp_word))
        temp_word = ""

    return result.getvalue()
