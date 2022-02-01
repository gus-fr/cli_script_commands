"""
utility functions to render a cli menu based on the function docstring.
basically adds 1 menu option per function added
"""
import argparse
from typing import Callable, Dict
import builtins
from docstring_parser import parse


class NoArgumentsPassed(Exception):
    """missing args Exception"""


class ScriptCommands:
    """
    Helper class that sets up the commands and arguments that can be used in the script.
    commands are meant to be set up via a function signature, with an appropriate docstring.
    It basically parses the command line arguments and throws errors when something is not right
    """

    def __init__(self):
        self._parser = argparse.ArgumentParser()
        self._subparsers = self._parser.add_subparsers(
            dest="cmd", title="subcommands", description="valid subcommands"
        )
        self._args = None

    def add_function(self, function: Callable) -> None:
        """
        adds an interface to the cli command based on the function docstring
        """
        parsed_doc_string = parse(function.__doc__)
        func_spec = {
            "name": function.__name__,
            "help": parsed_doc_string.short_description,
            "long_help": parsed_doc_string.long_description
            or parsed_doc_string.short_description,
            "function": function,
            "args": [
                {
                    "name": f"{'--' if pa.is_optional else ''}{pa.arg_name}",
                    "type": getattr(builtins, pa.type_name),
                    "help": pa.description,
                }
                for pa in parsed_doc_string.params
            ],
        }

        self._add_command(func_spec)

    def render_menu(self):
        """
        parses the arguments that have been passed to the cli
        """
        self._args = self._parser.parse_args()
        if not self._args.cmd:
            print("no arguments passed to cli")
            self._parser.print_help()
            raise NoArgumentsPassed()

    def execute(self):
        """
        Executes the function based on the cli command, and arguments passed
        """

        # make a dict of arguments only (exclude the command, and function)
        arg_dict = {
            k: v
            for (k, v) in vars(self._args).items()
            if k not in ("cmd", "func") and v is not None
        }
        return self._args.func(**arg_dict)

    def _add_command(self, command_settings: Dict) -> None:
        """
        Adds a function to the CLI.

        Adds an argument to be parsed by argparse
        it picks up the settings in the command_settings dict and sets up the command appropriately
        (name, params, function call) based on these settings
        """
        subparser = self._subparsers.add_parser(
            command_settings.get("name"),
            help=command_settings.get("help"),
            description=command_settings.get("long_help"),
        )

        # render all the arguments of a function
        # (until there are no more args)
        args = command_settings.get("args", [])
        for arg in args:
            if arg.get("type") == bool:
                optional_params = {"action": "store_true"}
            elif arg.get("type") == list:
                optional_params = {"nargs": "+", "type": str}
            else:
                optional_params = {"nargs": "?", "type": arg.get("type")}
            subparser.add_argument(
                arg.get("name"), help=arg.get("help"), **optional_params
            )

        subparser.set_defaults(func=command_settings.get("function"))
