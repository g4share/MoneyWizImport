import importlib
from pathlib import Path

from moneywizimport.converters.RawConverter import RawConverter
from moneywizimport.helpers.fs_helper import get_file_suffix


def create_converter(raw_statement_path: Path) -> RawConverter:
    suffix = get_file_suffix(raw_statement_path)
    class_name = f"{suffix.capitalize()}Converter"
    module_name = f".{class_name}"
    package = __package__

    try:
        module = importlib.import_module(module_name, package=package)
        converter_class = getattr(module, class_name)

        if not issubclass(converter_class, RawConverter):
            raise TypeError(f"{class_name} is not a subclass of RawConverter")

        return converter_class(raw_statement_path)
    except Exception as e:
        raise ValueError(f"Cannot create converter for {suffix} ({class_name})") from e
