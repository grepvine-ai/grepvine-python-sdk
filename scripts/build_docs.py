"""Build the API documentation site with pdoc and the Grepvine theme."""

import argparse
import importlib
import pkgutil
import re
import shutil
import warnings
from importlib.metadata import version
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
TEMPLATES = PACKAGE / "docs/theme/templates"
OUTPUT = PACKAGE / "site"
ROOT_MODULE = "grepvine"
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
# exports must appear exactly once.
REFERENCE_GROUPS = {
    "Clients and configuration": [
        "Client",
        "AsyncClient",
        "ClientConfig",
        "RetryPolicy",
        "configure",
        "default_client",
        "organizations",
        "indexes",
    ],
    "Organizations": [
        "Organizations",
        "AsyncOrganizations",
        "Organization",
        "Members",
        "AsyncMembers",
        "Member",
    ],
    "Indexes": ["Indexes", "AsyncIndexes", "Index", "AsyncIndex", "IndexData"],
    "Search": ["SearchResult", "Match", "ContextLine", "Span"],
    "Documents": [
        "Documents",
        "AsyncDocuments",
        "Document",
        "DocumentSummary",
        "MutationResult",
        "DocumentError",
        "ContentRange",
    ],
    "Pagination": ["Paginator", "AsyncPaginator", "Page"],
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
    "API keys": ["APIKeys", "AsyncAPIKeys", "APIKey", "APIKeyCreated"],
    "Account": ["Account", "AsyncAccount", "User"],
    "Device login": ["DeviceLogin", "AsyncDeviceLogin", "DeviceAuthorization"],
}
# Words the published site never uses: whether code is generated is not the reader's concern.
AVOIDED_WORDS = re.compile(r"\b(generated|raw|convenience|wrappers?|layers?)\b", re.IGNORECASE)


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
    exported = [name for name in root.__all__ if not name.startswith("__")]
    grouped = [name for names in REFERENCE_GROUPS.values() for name in names]
    if sorted(grouped) != sorted(exported):
        missing = sorted(set(exported) - set(grouped))
        extra = sorted(set(grouped) - set(exported))
        raise SystemExit(f"REFERENCE_GROUPS is out of date: missing {missing}, unknown {extra}")
    return list(REFERENCE_GROUPS.items())


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
