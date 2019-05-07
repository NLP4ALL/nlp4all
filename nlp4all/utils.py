
# this function takes a dictionary containing 
def add_css_class(words, text):
    categories = list(words.keys())
    all_words = list(words[categories[0]].keys())
    text_words = text.lower().split()
    for w in text_words:
        print(w)
        # css_class = (category, )
        # print(t, )

