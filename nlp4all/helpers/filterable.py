"""A module to represent filterable options

This module contains the FilterableType enum and the Filterable abstract class
as well as some basic types for the filterable options.

These help to avoid ever directly interacting with the metadata for DataSource.

Classes:
    FilterableType: An enum to represent the type of filterable options
    Filterable: An abstract class to represent filterable options


"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import typing as t


class FilterableType(Enum):
    """An enum to represent the type of filterable options"""
    STRING = 'string'
    NUMBER = 'number'
    DATE = 'date'
    BOOLEAN = 'boolean'

    @staticmethod
    def from_string(string: str) -> 'FilterableType':
        """Returns a FilterableType from a string

        Args:
            string (str): The string to convert

        Returns:
            FilterableType: The FilterableType that corresponds to the string
        """
        if string == FilterableType.STRING.value:
            return FilterableType.STRING
        if string == FilterableType.NUMBER.value:
            return FilterableType.NUMBER
        if string == FilterableType.DATE.value:
            return FilterableType.DATE
        if string == FilterableType.BOOLEAN.value:
            return FilterableType.BOOLEAN

        raise ValueError(f"Invalid FilterableType: {string}")


class Filterable(ABC):
    """An abstract class to represent filterable options"""

    _type: FilterableType
    _type_handlers: t.Dict[str, t.Type['Filterable']] = {}
    nullable: bool

    def __init__(self, name: str, path: t.Tuple[str, ...], options: t.Dict[str, t.Any]):
        """Initializes a Filterable object

        Args:
            name (str): The name of the filterable option
            path (t.Tuple[str, ...]): The path to the filterable option
            options (t.Dict[str, t.Any]): The options for the filterable option
                Keys:
                    - nullable: Whether the option can be null (default: False)
                    - ...
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        self.name = name

        if not isinstance(path, tuple):
            raise TypeError("path must be a tuple")

        if not len(path) > 0:
            raise ValueError("path must have at least one element")

        if not all(isinstance(p, str) for p in path):
            raise TypeError("path must be a tuple of strings")

        self.path = path

        if not isinstance(options, dict):
            raise TypeError("options must be a dictionary")

        self._validate_options(options)

        self.options = options.copy()
        self.options["nullable"] = self.options.get("nullable", False)
        self.nullable = self.options["nullable"]

    @staticmethod
    def register_type_handler(klass: t.Type['Filterable']):
        """Registers a new type handler for a Filterable object

        Args:
            klass (t.Type[Filterable]): The class to register"""

        if not issubclass(klass, Filterable):
            raise TypeError("Class must be a subclass of Filterable")

        filter_type = klass._type  # pylint: disable=protected-access
        if filter_type.value in Filterable._type_handlers:
            raise ValueError(f"Filterable for type {filter_type.value} already registered")

        Filterable._type_handlers[filter_type.value] = klass

    @classmethod
    def _modify_options_from_dict(cls, options: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Preprocesses options Filterable object is created

        If subclasses need alter the options dictionary before it is passed
        to the constructor, they should override this method.

        Args:
            options (t.Dict[str, t.Any]): The options dictionary to preprocess

        Returns:
            dict (t.Dict[str, t.Any]): The preprocessed options dictionary
        """
        return options

    def _modify_options_to_dict(self, options: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Preprocesses an options dictionary before it is returned

        If subclasses need alter the options dictionary before it is returned,
        they should override this method.

        Args:
            options (t.Dict[str, t.Any]): The options dictionary to preprocess

        Returns:
            dict (t.Dict[str, t.Any]): The preprocessed options dictionary
        """
        return options

    @classmethod
    def _validate_dict(cls, data: t.Dict[str, t.Any]):
        """Validates that a dictionary is a valid Filterable object

        Args:
            data (dict): The dictionary to validate
        """
        try:
            name = data['name']
            tipe = data['type']
            path = data['path']
        except KeyError as err:
            raise KeyError(f"Missing required key {err}") from err

        if 'options' not in data:
            raise KeyError("Missing required key 'options'")

        if not isinstance(name, str):
            raise TypeError(f"Name must be a string, not {type(name)}")

        if not isinstance(tipe, str):
            raise TypeError(f"Type must be a string, not {type(tipe)}")

        if not isinstance(path, list):
            raise TypeError(f"Path must be a list, not {type(path)}")

    @classmethod
    def _validate_options(cls, options: t.Dict[str, t.Any]):
        """Validates that the options dictionary is valid

        Subclasses requiring specific options should test them here
        and raise a ValueError if they are invalid.

        Args:
            options (dict): The options dictionary to validate
        """
        if not isinstance(options, dict):
            raise TypeError(f"Options must be a dictionary, not {type(options)}")

        nullable = options.get('nullable', False)
        if not isinstance(nullable, bool):
            raise TypeError(f"Nullable must be a boolean, not {type(nullable)}")

    @classmethod
    def from_dict(cls, data: dict) -> 'Filterable':
        """Creates a new Filterable object from a dictionary"""

        cls._validate_dict(data)

        tipe = data['type']

        if tipe not in Filterable._type_handlers:
            raise ValueError(f"No Filterable class registered for FilterableType: {tipe}")

        handler = Filterable._type_handlers[tipe]

        # don't want to modify the original dictionary
        opts = data['options'].copy()

        handler._validate_options(opts)  # pylint: disable=protected-access

        return handler(
            data['name'],
            tuple(data['path']),
            handler._modify_options_from_dict(opts))  # pylint: disable=protected-access

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the FilterableString object"""
        return {
            'name': self.name,
            'type': self._type.value,
            'path': list(self.path),
            'options': self._modify_options_to_dict(self.options.copy())
        }

    @abstractmethod
    def validate(self, value: t.Any) -> bool:
        """Validates that a value is valid for the filterable

        Args:
            value (t.Any): The value to validate

        Returns:
            bool: Whether the value is valid or not
        """


class FilterableString(Filterable):
    """A class to represent filterable strings"""

    _type = FilterableType.STRING

    def __init__(self, name: str, path: t.Tuple[str, ...],
                 options: t.Optional[t.Union[None, t.Dict[str, t.Any]]] = None):
        """Initializes a new FilterableString object

        Args:
            name (str): The name of the filterable
            path (t.Tuple[str, ...]): The path to the filterable
            options (t.Dict[str, t.Any]): The options for the filterable (unused)
        """

        if options is None:
            options = {}

        super().__init__(name, path, options)

    def validate(self, value: t.Any) -> bool:
        """Validates that a value is valid for the filterable string

        Args:
            value (t.Any): The value to validate

        Returns:
            bool: Whether the value can be used for the filterable string or not
        """

        if not isinstance(value, str):
            return False

        return True


Filterable.register_type_handler(FilterableString)


class FilterableNumber(Filterable):
    """A class to represent filterable numbers"""

    _type = FilterableType.NUMBER

    min_val: t.Union[int, float]
    max_val: t.Union[int, float]
    is_float: bool = False

    def __init__(self, name: str, path: t.Tuple[str, ...], options: t.Dict[str, t.Any]):
        """Initializes a new FilterableNumber object

        Args:
            name (str): The name of the filterable
            path (t.Tuple[str, ...]): The path to the filterable
            options (t.Dict[str, t.Any]): The options for the filterable
                Required options:
                    min (int or float): The minimum value
                    max (int or float): The maximum value
                Optional options:
                    is_float (bool): Whether the number is a float or not. Defaults to False
        """

        super().__init__(name, path, options)

        self.min_val = self.options['min']
        self.max_val = self.options['max']
        self.is_float = self.options.get('is_float', False)

    def min(self) -> t.Union[float, int]:
        """Returns the minimum value"""
        return self.min_val if self.is_float else int(self.min_val)

    def max(self) -> t.Union[float, int]:
        """Returns the maximum value"""
        return self.max_val if self.is_float else int(self.max_val)

    def validate(self, value: t.Any) -> bool:
        """Validates a value against the minimum and maximum values

        Args:
            value (t.Any): The value to validate

        Returns:
            bool: Whether the value is valid or not
        """
        if type(value) not in [int, float]:
            return False

        if self.is_float:
            return self.min_val <= value <= self.max_val

        return self.min_val <= int(value) <= self.max_val

    @classmethod
    def _validate_options(cls, options: t.Dict[str, t.Any]) -> None:
        """Validates the options for the filterable number

        Args:
            options (t.Dict[str, t.Any]): The options to validate

        Raises:
            KeyError: If a required option is missing
            TypeError: If an option is the wrong type
        """

        super()._validate_options(options)

        try:
            min_val = options.get('min')
            max_val = options.get('max')
        except KeyError as err:
            raise KeyError(f"Missing required option {err}") from err

        is_float = options.get('is_float', False)

        if not isinstance(is_float, bool):
            raise TypeError(f"Expected is_float to be a bool, got {type(is_float)}")

        if not isinstance(min_val, (int, float)):
            raise TypeError(f"Expected min to be a number, got {type(min_val)}")

        if not isinstance(max_val, (int, float)):
            raise TypeError(f"Expected max to be a number, got {type(max_val)}")

        if min_val > max_val:  # type: ignore
            raise ValueError(f"min ({min_val}) cannot be greater than max ({max_val})")

    @classmethod
    def _modify_options_from_dict(cls, options: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Modifies the options from a _validated_ dict, pre init.

        Args:
            options (t.Dict[str, t.Any]): The options to modify

        Returns:
            t.Dict[str, t.Any]: The modified options
        """

        options = super()._modify_options_from_dict(options)

        options['is_float'] = options.get('is_float', False)

        if options['is_float']:
            options['min'] = float(options['min'])
            options['max'] = float(options['max'])
        else:
            options['min'] = int(options['min'])
            options['max'] = int(options['max'])

        return options


Filterable.register_type_handler(FilterableNumber)


class FilterableDate(Filterable):
    """A class to represent filterable dates"""

    _type = FilterableType.DATE

    min_val: datetime
    max_val: datetime

    def __init__(self, name: str, path: t.Tuple[str, ...], options: t.Dict[str, t.Any]):
        """Initializes a new FilterableDate object

        Args:
            name (str): The name of the filterable
            path (t.Tuple[str, ...]): The path to the filterable
            options (t.Dict[str, t.Any]): The options for the filterable
                Required options:
                    min (datetime,str): The minimum value datetime, or isoformat string
                    max (datetime,str): The maximum value datetime, or isoformat string
        """

        super().__init__(name, path, options)

        self.min_val = self.options['min']
        self.max_val = self.options['max']

    def min(self) -> datetime:
        """Returns the minimum value"""
        return self.min_val

    def max(self) -> datetime:
        """Returns the maximum value"""
        return self.max_val

    def validate(self, value: t.Any) -> bool:
        """Validates a value against the minimum and maximum values

        Args:
            value (datetime): The value to validate

        Returns:
            bool: Whether the value is valid or not
        """
        if not isinstance(value, datetime):
            if not isinstance(value, str):
                return False
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return False

        return self.min_val <= value <= self.max_val

    @classmethod
    def _validate_options(cls, options: t.Dict[str, t.Any]) -> None:
        """Validates the options for the filterable number

        Args:
            options (t.Dict[str, t.Any]): The options to validate

        Raises:
            KeyError: If a required option is missing
            TypeError: If an option is the wrong type
        """

        super()._validate_options(options)

        try:
            min_val = options.get('min')
            max_val = options.get('max')
        except KeyError as err:
            raise KeyError(f"Missing required option {err}") from err

        if not isinstance(min_val, datetime):
            if not isinstance(min_val, str):
                raise TypeError(
                    f"Expected min to be a datetime or isoformat string, got {type(min_val)}")
            try:
                datetime.fromisoformat(min_val)
            except Exception as exc:
                raise TypeError(f"{min_val} is not a valid isoformat string") from exc

        if not isinstance(max_val, datetime):
            if not isinstance(max_val, str):
                raise TypeError(
                    f"Expected max to be a datetime or isoformat string, got {type(max_val)}")
            try:
                datetime.fromisoformat(max_val)
            except Exception as exc:
                raise TypeError(f"{max_val} is not a valid isoformat string") from exc

        if min_val > max_val:  # type: ignore
            raise ValueError(f"min ({min_val}) cannot be greater than max ({max_val})")

    @classmethod
    def _modify_options_from_dict(cls, options: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Modifies the options from a dict

        Args:
            options (t.Dict[str, t.Any]): The options to modify

        Returns:
            t.Dict[str, t.Any]: The modified options
        """
        options = super()._modify_options_from_dict(options)
        if isinstance(options['min'], str):
            options['min'] = datetime.fromisoformat(options['min'])
        if isinstance(options['max'], str):
            options['max'] = datetime.fromisoformat(options['max'])

        return options

    def _modify_options_to_dict(self, options: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Modifies the options to a dict

        Args:
            options (t.Dict[str, t.Any]): The options to modify

        Returns:
            t.Dict[str, t.Any]: The modified options
        """
        options = super()._modify_options_to_dict(options)
        options['min'] = options['min'].isoformat()
        options['max'] = options['max'].isoformat()

        return options


Filterable.register_type_handler(FilterableDate)


class FilterableBoolean(Filterable):
    """A class to represent filterable booleans"""

    _type = FilterableType.BOOLEAN

    def validate(self, value: t.Any) -> bool:
        """Validates a value against the minimum and maximum values

        Args:
            value (bool): The value to validate

        Returns:
            bool: Whether the value is valid or not
        """
        if not isinstance(value, bool):
            return False

        return True


Filterable.register_type_handler(FilterableBoolean)
