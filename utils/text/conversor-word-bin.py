from dict import word_to_bin_dict
class conversor:
    def __init__(self, word):
        self.word = word
    def word_to_bin(self):
        self.word = self.word.upper()
        bin_word = ""
        for letter in self.word:
            bin_word += str(word_to_bin_dict[letter])
            bin_word += "|"
        return bin_word
    def bin_to_word(self, bin_word):
        word = ""
        bin_word = self.word.split("|")
        for bin_letter in bin_word:
            for letter, bin in word_to_bin_dict.items():
                if bin == bin_letter:
                    word += letter
        return word
    
if __name__ == "__main__":  
    #teste
    word = "realiehgay"
    conversor_word = conversor(word)
    bin_word = conversor_word.word_to_bin()
    print(bin_word)
    conversor_bin = conversor(bin_word)
    word = conversor_bin.bin_to_word(bin_word)
    print(word)