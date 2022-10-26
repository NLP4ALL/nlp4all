"""Color related functions."""

def generate_n_hsl_colors(no_colors, transparency=1, offset=0):
    """generate a list of n hsl colors"""
    no_colors = 1 if no_colors == 0 else no_colors
    hsl_span = int(255 / no_colors)
    return [(hsl_span * n + offset, 50, 100 * transparency) for n in range(no_colors)]


# takes a list of TweetTagCategory objects, returns
# a dict with the name of a category and its corresponding
# color
def assign_colors(list_of_categories):
    """assign colors to categories"""
    category_color_dict = {}
    no_colors = len(list_of_categories)
    hsl_span = int(255 / no_colors)
    for i in range(no_colors):
        category_color_dict[list_of_categories[i].name] = (i * hsl_span) + (hsl_span / 10)
    return category_color_dict



def hsl_color_to_string(hsltup):
    """convert an hsl color tuple to a string"""
    return f"hsl({hsltup[0]}, {hsltup[1]}%, {hsltup[2]}%)"


# takes a list of TweetTagCategory objects, returns
# a dict with the name of a category and its corresponding
# color
def ann_assign_colors(list_of_tags):  # take all tags
    """assign colors to a list of tags"""
    category_color_dict = {}
    no_colors = len(list_of_tags)
    hsl_span = int(255 / no_colors)
    for i in range(no_colors):
        category_color_dict[list_of_tags[i].lower()] = (i * hsl_span) + (hsl_span / 10)
    return category_color_dict
