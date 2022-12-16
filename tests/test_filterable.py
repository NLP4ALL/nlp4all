"""Tests for the filterable module."""

from datetime import datetime
import pytest

from nlp4all.helpers.filterable import (
    Filterable,
    FilterableType,
    FilterableString,
    FilterableNumber,
    FilterableDate,
    FilterableBoolean
)


@pytest.mark.helper
def test_filterabletype_fromstring():
    """Test the FilterableType class."""
    assert FilterableType.from_string('string') == FilterableType.STRING
    assert FilterableType.from_string('number') == FilterableType.NUMBER
    assert FilterableType.from_string('date') == FilterableType.DATE
    assert FilterableType.from_string('boolean') == FilterableType.BOOLEAN
    with pytest.raises(ValueError):
        FilterableType.from_string('invalid')


@pytest.mark.helper
def test_filterable():
    """Test the Filterable class."""

    # ensure filterable cannot be instantiated directly
    with pytest.raises(TypeError):
        filterable = Filterable('test', ('invalid'), {})  # noqa: F841


def test_filterablestring():
    """Test the FilterableString class."""
    name = 'teststring'
    path = ('test1', 'test2')

    # we also want to ensure arbitrary options remain, besides required ones
    options = {
        'testopt': 'testval',
        'another': 2,
    }

    filterable = FilterableString(name, path, options)
    assert filterable.name == name
    assert filterable._type == FilterableType.STRING  # pylint: disable=protected-access
    assert filterable.path == path
    # make sure options dict we passed in is a subset of the one in the object
    assert options.items() <= filterable.options.items()

    dict_out = filterable.to_dict()
    assert dict_out['name'] == name
    assert dict_out['type'] == FilterableType.STRING.value
    assert dict_out['path'] == list(path)
    assert options.items() <= dict_out['options'].items()

    del filterable

    # test FilterableString.from_dict
    filterable = FilterableString.from_dict(dict_out)
    assert isinstance(filterable, FilterableString)
    assert filterable.name == name
    assert filterable._type == FilterableType.STRING  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    del filterable

    # test Filterable.from_dict, to ensure type handler works
    filterable = Filterable.from_dict(dict_out)
    assert isinstance(filterable, FilterableString)
    assert filterable.name == name
    assert filterable._type == FilterableType.STRING  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    assert filterable.validate("test")
    assert not filterable.validate(1)

    # test with max_length option
    options['max_length'] = 10

    filterable = FilterableString(name, path, options)
    assert filterable.validate("test")
    assert not filterable.validate("testtesttesttest")


def test_filterablenumber():
    """Test the FilterableNumber class."""

    name = 'testnumber'
    path = ('test1', 'test2')

    options = {
        'min': 1,
        'max': 10,
    }

    filterable = FilterableNumber(name, path, options)
    assert filterable.name == name
    assert filterable._type == FilterableType.NUMBER  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    dict_out = filterable.to_dict()
    assert dict_out['name'] == name
    assert dict_out['type'] == FilterableType.NUMBER.value
    assert dict_out['path'] == list(path)
    assert options.items() <= dict_out['options'].items()

    del filterable

    # test FilterableNumber.from_dict
    filterable = FilterableNumber.from_dict(dict_out)
    assert isinstance(filterable, FilterableNumber)
    assert filterable.name == name
    assert filterable._type == FilterableType.NUMBER  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    del filterable

    # test Filterable.from_dict, to ensure type handler works
    filterable = Filterable.from_dict(dict_out)
    assert isinstance(filterable, FilterableNumber)
    assert filterable.name == name
    assert filterable._type == FilterableType.NUMBER  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    assert filterable.validate(5)
    assert not filterable.validate(11)
    assert not filterable.validate("test")

    # now test with float values
    options = {
        'min': 1.0,
        'max': 10.0,
        'is_float': True
    }

    filterable = FilterableNumber(name, path, options)
    assert filterable.name == name
    assert filterable._type == FilterableType.NUMBER  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    dict_out = filterable.to_dict()
    assert dict_out['name'] == name
    assert dict_out['type'] == FilterableType.NUMBER.value
    assert dict_out['path'] == list(path)
    assert options.items() <= dict_out['options'].items()

    del filterable

    # test FilterableNumber.from_dict
    filterable = FilterableNumber.from_dict(dict_out)
    assert isinstance(filterable, FilterableNumber)

    assert filterable.validate(5.0)
    assert not filterable.validate(11.0)
    assert not filterable.validate("test")


def test_filterabledate():
    """Test the FilterableDate class."""

    name = 'testdate'
    path = ('test1', 'test2')

    options = {
        'min': datetime.fromisoformat('2018-01-01'),
        'max': datetime.fromisoformat('2018-12-31'),
    }

    options_out = {
        'min': options['min'].isoformat(),
        'max': options['max'].isoformat(),
    }

    filterable = FilterableDate(name, path, options)
    assert filterable.name == name
    assert filterable._type == FilterableType.DATE  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    dict_out = filterable.to_dict()
    assert dict_out['name'] == name
    assert dict_out['type'] == FilterableType.DATE.value
    assert dict_out['path'] == list(path)
    assert options_out.items() <= dict_out['options'].items()

    del filterable

    # test Filterable.from_dict, to ensure type handler works
    filterable = Filterable.from_dict(dict_out)
    assert isinstance(filterable, FilterableDate)
    assert filterable.name == name
    assert filterable._type == FilterableType.DATE  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    assert filterable.validate(datetime.fromisoformat("2018-01-01"))
    assert filterable.validate(datetime.fromisoformat("2018-01-01"))
    assert not filterable.validate(1)
    assert not filterable.validate("test")


def test_filterableboolean():
    """Test the FilterableBoolean class."""

    name = 'testboolean'
    path = ('test1', 'test2')

    options = {
        'aaa': 'cc',
        'bbb': 'dd',
    }

    filterable = FilterableBoolean(name, path, options)
    assert filterable.name == name
    assert filterable._type == FilterableType.BOOLEAN  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    dict_out = filterable.to_dict()
    assert dict_out['name'] == name
    assert dict_out['type'] == FilterableType.BOOLEAN.value
    assert dict_out['path'] == list(path)
    assert options.items() <= dict_out['options'].items()

    del filterable

    # test FilterableBoolean.from_dict
    filterable = FilterableBoolean.from_dict(dict_out)
    assert isinstance(filterable, FilterableBoolean)
    assert filterable.name == name
    assert filterable._type == FilterableType.BOOLEAN  # pylint: disable=protected-access
    assert filterable.path == path
    assert options.items() <= filterable.options.items()

    assert filterable.validate(True)
    assert filterable.validate(False)
    assert not filterable.validate(1)
    assert not filterable.validate("test")
