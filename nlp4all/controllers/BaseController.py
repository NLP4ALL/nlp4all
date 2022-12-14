"""For providing a base controller for all controllers to inherit from."""  # pylint: disable=invalid-name

import typing as t
from flask import Blueprint, render_template


class BaseController:  # pylint: disable=too-few-public-methods
    """Base controller for all controllers to inherit from."""

    view_subdir = None
    blueprint: Blueprint

    @classmethod
    def render_template(cls, template_name: str, **context: t.Any) -> str:
        """Render a template, wraps flask render to easily organize views."""
        if cls.view_subdir:
            return render_template(cls.view_subdir + '/' + template_name, **context)
        raise TypeError("No view_subdir set for this controller")
