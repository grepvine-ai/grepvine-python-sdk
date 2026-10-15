"""Build the API documentation site with pdoc and the Grepvine theme."""

import argparse
import functools
import importlib
import inspect
import pkgutil
import re
import shutil
import typing
import warnings
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[1]
TEMPLATES = PACKAGE / "docs/theme/templates"
OUTPUT = PACKAGE / "site"
ROOT_MODULE = "grepvine"
PRIVATE = "grepvine._"
REPOSITORY_URL = "https://github.com/grepvine-ai/grepvine-python-sdk"
# The guide's sections, in the order every Grepvine SDK uses.
GUIDE_SECTIONS = [
    "Installation",
    "Authentication",
    "Organizations",
    "Indexes",
    "Search",
    "Documents",
    "Pagination",
    "Errors",
    "Asynchronous use",
    "API keys",
    "Account",
    "Device login",
]
# The reference on the landing page, by resource, in the guide's order. Every name the package
# exports must appear exactly once, apart from `models`, which has its own page.
REFERENCE_GROUPS = {
    "Clients and configuration": ["Client", "AsyncClient", "RetryPolicy"],
    "Organizations": ["Organizations", "AsyncOrganizations", "Members", "AsyncMembers"],
    "Indexes": ["Indexes", "AsyncIndexes"],
    "Search": ["Search", "AsyncSearch"],
    "Documents": ["Documents", "AsyncDocuments", "DocumentInput", "MetadataValue"],
    "Pagination": ["paginate"],
    "Errors": [
        "GrepvineError",
        "APIError",
        "InvalidRequestError",
        "InvalidPageError",
        "AuthenticationError",
        "PermissionDeniedError",
        "NotFoundError",
        "ConflictError",
        "PreconditionFailedError",
        "PayloadTooLargeError",
        "RangeNotSatisfiableError",
        "RateLimitedError",
        "ServerError",
        "ConfigurationError",
        "TransportError",
        "PartialBatchError",
    ],
    "API keys": ["APIKeys", "AsyncAPIKeys"],
    "Account": ["Account", "AsyncAccount"],
    "Device login": ["DeviceLogin", "AsyncDeviceLogin"],
}
# Words the published site never uses: whether code is generated is not the reader's concern.
# "raw HTML" in the API's own descriptions is not about the SDK.
AVOIDED_WORDS = re.compile(
    r"\b(generated|raw(?! HTML)|convenience|wrappers?|layers?)\b", re.IGNORECASE
)


def guide() -> tuple[str, str]:
    """Return the README title and body, checking its sections are the guide's."""
    title, _, body = (PACKAGE / "README.md").read_text().partition("\n")
    if not title.startswith("# "):
        raise SystemExit("README.md must start with a level-one heading")
    headings = re.findall(r"^## (.+)$", body, flags=re.MULTILINE)
    if headings[: len(GUIDE_SECTIONS)] != GUIDE_SECTIONS:
        raise SystemExit(f"README.md sections must start with {GUIDE_SECTIONS}, not {headings}")
    return title.removeprefix("# ").strip(), body


def reference_groups() -> list[tuple[str, list[str]]]:
    """The landing page's reference groups, checked against the package's exports."""
    root = importlib.import_module(ROOT_MODULE)
    exported = [name for name in root.__all__ if not name.startswith("__") and name != "models"]
    grouped = [name for names in REFERENCE_GROUPS.values() for name in names]
    if sorted(grouped) != sorted(exported):
        missing = sorted(set(exported) - set(grouped))
        extra = sorted(set(grouped) - set(exported))
        raise SystemExit(f"REFERENCE_GROUPS is out of date: missing {missing}, unknown {extra}")
    return list(REFERENCE_GROUPS.items())


def models_by_resource() -> str:
    """The models each resource's methods take and return, found from their signatures."""
    root = importlib.import_module(ROOT_MODULE)
    models = importlib.import_module(f"{ROOT_MODULE}.models")
    exported = [getattr(models, name) for name in models.__all__]

    def found(annotation: object) -> set[str]:
        names = (
            {annotation.__name__}
            if isinstance(annotation, type) and annotation in exported
            else set()
        )
        arguments = annotation if isinstance(annotation, list) else typing.get_args(annotation)
        for argument in arguments:
            names |= found(argument)
        return names

    lines = ["The request and response models, by the resource whose methods use them:", ""]
    for title, names in REFERENCE_GROUPS.items():
        used: set[str] = set()
        for name in names:
            resource = getattr(root, name)
            if isinstance(resource, type) and issubclass(resource, Exception | dict):
                continue
            for method_name, method in inspect.getmembers(resource, inspect.isfunction):
                if not method_name.startswith("_"):
                    for hint in typing.get_type_hints(method).values():
                        used |= found(hint)
        if used:
            listed = ", ".join(f"`{name}`" for name in sorted(used - {"File", "Unset"}))
            lines.append(f"- **{title}:** {listed}")
    return "\n".join(lines)


def relocate() -> None:
    """Document every exported class where users import it from, without its private origins.

    Each class, and each private base class, takes the public module and name; annotations are
    resolved in the namespace they were written in, and the source is read before the move. A
    resource's constructor, which only the client calls, is hidden. This changes the imported
    objects for the build only.
    """
    import pdoc.doc
    import pdoc.doc_ast

    models = importlib.import_module(f"{ROOT_MODULE}.models")
    for module in (importlib.import_module(ROOT_MODULE), models):
        for name in module.__all__:
            item = getattr(module, name)
            # A TypedDict keeps its module: pdoc finds its keys there.
            if not isinstance(item, type) or issubclass(item, dict):
                continue
            for owner in item.__mro__:
                if not owner.__module__.startswith(PRIVATE):
                    continue
                pdoc.doc_ast.get_source(owner)
                owner.__annotations__ = typing.get_type_hints(owner, localns=vars(models))
                for _, function in inspect.getmembers(owner, inspect.isfunction):
                    if function.__module__.startswith(PRIVATE):
                        hints = typing.get_type_hints(function, localns=vars(models))
                        function.__annotations__ = hints
                owner.__module__, owner.__qualname__ = module.__name__, item.__qualname__
            if "__attrs_attrs__" in vars(item):
                item.__init__.__doc__ = f"Create a `{name}`."  # type: ignore[misc]
            elif not issubclass(item, Exception) and "client" in inspect.signature(item).parameters:
                item.__init__.__doc__ = "@private"  # type: ignore[misc]
    models.Unset.__repr__ = lambda self: "UNSET"  # type: ignore[method-assign]

    def bases(self: pdoc.doc.Class) -> list[tuple[str, str, str]]:
        own = (self.modulename, self.qualname)
        return [base for base in bases_of(self) if base[:2] != own]

    def source(self: pdoc.doc.Module) -> str:
        # The models page lists the models rather than the module's import statements.
        return "" if self.modulename == models.__name__ else source_of(self)

    bases_of = inspect.getattr_static(pdoc.doc.Class, "bases").func
    source_of = inspect.getattr_static(pdoc.doc.Module, "source").func
    patches: list[tuple[type, str, Callable[[Any], Any]]] = [
        (pdoc.doc.Class, "bases", bases),
        (pdoc.doc.Module, "source", source),
    ]
    for owner, name, replacement in patches:
        patched = functools.cached_property(replacement)
        patched.__set_name__(owner, name)
        setattr(owner, name, patched)


def module_specs() -> list[str]:
    """Return pdoc specs covering every public module.

    Private modules such as `_generated` stay out of the site.
    """
    from pdoc.extract import walk_specs

    root = importlib.import_module(ROOT_MODULE)
    specs = [ROOT_MODULE]
    covered = set(walk_specs(specs))
    for info in pkgutil.walk_packages(root.__path__, f"{ROOT_MODULE}."):
        public = not any(part.startswith("_") for part in info.name.split("."))
        if public and info.name not in covered:
            specs.append(info.name)
            covered.update(walk_specs([info.name]))
    return specs


def check_site(output: Path) -> None:
    """Fail when a page mentions the private package or a word the docs avoid."""
    problems = []
    for page in sorted(output.rglob("*.html")):
        text = page.read_text()
        if "_generated" in text:
            problems.append(f"{page.relative_to(output)} mentions _generated")
        visible = re.sub(r"<(script|style)\b.*?</\1>|<[^>]+>", " ", text, flags=re.DOTALL)
        for word in sorted({match.lower() for match in AVOIDED_WORDS.findall(visible)}):
            problems.append(f"{page.relative_to(output)} says {word!r}")
    if problems:
        raise SystemExit("\n".join(problems))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT, help="output directory")
    output = parser.parse_args().output
    # Any pdoc warning (an unresolved reference, a module that fails to import) fails the build.
    warnings.simplefilter("error")

    import pdoc
    import pdoc.render

    title, body = guide()
    relocate()
    models = importlib.import_module(f"{ROOT_MODULE}.models")
    models.__doc__ = f"{models.__doc__}\n\n{models_by_resource()}"
    pdoc.render.configure(
        docformat="google",
        footer_text=f"grepvine {version('grepvine')}",
        search=True,
        show_source=True,
        template_directory=TEMPLATES,
    )
    pdoc.render.env.globals.update(
        guide=body,
        guide_title=title,
        reference_groups=reference_groups(),
        repository_url=REPOSITORY_URL,
    )
    shutil.rmtree(output, ignore_errors=True)
    pdoc.pdoc(*module_specs(), output_directory=output)
    check_site(output)
    # GitHub Pages must serve the files as they are, without a Jekyll build.
    (output / ".nojekyll").touch()
    print(f"Documentation written to {output}")


if __name__ == "__main__":
    main()
