import importlib
from pathlib import Path

from moneywizimport.helpers.fs_helper import get_file_suffix
from moneywizimport.resolvers.BaseResolver import BaseResolver


def create_resolver(label: str, file_path: Path) -> BaseResolver:
    suffix = get_file_suffix(file_path)
    class_name = f"{label.capitalize()}{suffix.capitalize()}Resolver"
    module_name = f".{class_name}"
    package = __package__

    try:
        module = importlib.import_module(module_name, package=package)
        resolver_class = getattr(module, class_name)

        if not issubclass(resolver_class, BaseResolver):
            raise TypeError(f"{class_name} is not a subclass of BaseResolver")

        return resolver_class(file_path)
    except Exception as e:
        raise ValueError(f"Cannot create resolver for {label} ({class_name})") from e
