"""Dataset related utils

These should not have any within-module dependencies.
"""

import random

def create_n_train_and_test_sets(n, dict_of_tweets_and_cats):
    """Create n train and test sets from a dict of tweets and categories"""
    # takes a list of tups each containing a tweet_id and tweet_category
    return_list = []
    half = int(len(dict_of_tweets_and_cats) / 2)
    for n in range(n):
        d1, d2 = split_dict(dict_of_tweets_and_cats)
        return_list.append((d1, d2))
    return return_list

def split_dict(adict):
    """Split a dict into two dicts"""
    keys = list(adict.keys())
    n = len(keys) // 2
    random.shuffle(keys)
    return ({k: adict[k] for k in keys[:n]}, {k: adict[k] for k in keys[n:]})

def n_split_dict(adict, split):
    """Split a dict into n dicts"""
    keys = list(adict.keys())
    n = int(len(keys) * split)
    random.shuffle(keys)
    # TODO: equally distributed categories in both sets
    return ({k: adict[k] for k in keys[:n]}, {k: adict[k] for k in keys[n:]})


def create_n_split_tnt_sets(n, split, dict_of_tweets_and_cats):
    """Create n train and test sets from a dict of tweets and categories"""
    return_list = []
    # half = int(len(dict_of_tweets_and_cats) / 2)
    for n in range(n):
        d1, d2 = n_split_dict(dict_of_tweets_and_cats, split)
        return_list.append((d1, d2))
    return return_list