"""Tests for nlp4all dataset functions."""
import unittest

import pytest

from nlp4all.datasets import split_dict

class DatasetTest(unittest.TestCase):
    """All tests for nlp4all dataset functions."""
    @pytest.mark.data
    def test_split_dict(self):
        """Test split_dict"""
        test_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        split_l, split_r = split_dict(test_dict)
        assert len(split_l) == len(split_r)
