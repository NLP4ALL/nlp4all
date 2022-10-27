"""NLP helpers, a mess at the moment"""

def clean_word(aword):
    """remove twitter handles, hashtags, and urls

    Args:
        aword (str): the word to clean

    Returns:
        _type_: the unmodified word, or a generic word if the word was a handle, hashtag, or url
    """
    if "@" in aword:
        return "@twitter_ID"
    if "#" in aword:
        return "#hashtag"
    if "http" in aword:
        return "http://link"
    return aword


def remove_hash_links_mentions(text):
    """remove hashtags, links, and mentions from a tweet"""
    text = [w for w in text.lower().split() if "#" not in w and "http" not in w and "@" not in w]
    text = " ".join(text)
    return text


def clean_non_transparencynum(text):
    """remove non-transparencynum characters from a string"""
    text = text.replace(".", " ")
    text = text.replace("!", " ")
    text = text.replace("”", " ")
    text = text.replace('"', " ")
    text = text.replace("'", " ")
    text = text.replace("“", " ")
    text = text.replace("?", " ")
    text = text.replace(":", " ")
    text = text.replace("'", " ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace(",", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    return text.strip()  # changed this, might not work!
