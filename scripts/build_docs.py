"""Build the API documentation site with pdoc and the Grepvine theme."""

import argparse
import importlib
import os
import pkgutil
import re
import shutil
import warnings
from importlib.metadata import version
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
TEMPLATES = PACKAGE / "docs/theme/templates"
# A checkout of grepvine-ai/grepvine-design-system at the commit in design-system.ref.
DESIGN_SYSTEM_REF = PACKAGE / "docs/theme/design-system.ref"
DESIGN_SYSTEM_DEFAULT = PACKAGE.parent / "grepvine-design-system"
OUTPUT = PACKAGE / "site"
ROOT_MODULE = "grepvine_sdk"
REPOSITORY_URL = "https://github.com/grepvine-ai/grepvine-python-sdk"
# README sections about maintaining this repository rather than using the SDK.
CONTRIBUTOR_SECTIONS = {"Generation and development", "Repository automation"}


def guide() -> tuple[str, str]:
    """Return the README title and its user-facing sections as the landing-page guide."""
    title, _, body = (PACKAGE / "README.md").read_text().partition("\n")
    if not title.startswith("# "):
        raise SystemExit("README.md must start with a level-one heading")
    intro, *sections = re.split(r"^(?=## )", body, flags=re.MULTILINE)
    by_heading = {s.partition("\n")[0].removeprefix("## ").strip(): s for s in sections}
    if missing := CONTRIBUTOR_SECTIONS - by_heading.keys():
        raise SystemExit(f"README.md no longer has the sections {sorted(missing)}")
    kept = [s for heading, s in by_heading.items() if heading not in CONTRIBUTOR_SECTIONS]
    return title.removeprefix("# ").strip(), "".join([intro, *kept])


def design_system() -> Path:
    """Return the design-system checkout named by GREPVINE_DESIGN_SYSTEM or the sibling clone."""
    path = Path(os.environ.get("GREPVINE_DESIGN_SYSTEM") or DESIGN_SYSTEM_DEFAULT).resolve()
    if not (path / "tokens.css").is_file():
        ref = DESIGN_SYSTEM_REF.read_text().strip()
        raise SystemExit(
            f"No Grepvine design system at {path}. Clone "
            "https://github.com/grepvine-ai/grepvine-design-system there and check out "
            f"{ref}, or set GREPVINE_DESIGN_SYSTEM to an existing checkout."
        )
    return path


def module_specs() -> list[str]:
    """Return pdoc specs covering every public module.

    pdoc does not descend into submodules a package leaves out of its `__all__`, such as
    `grepvine_sdk.generated`, so those are added as specs of their own.
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT, help="output directory")
    output = parser.parse_args().output
    # Any pdoc warning (an unresolved reference, a module that fails to import) fails the build.
    warnings.simplefilter("error")

    import jinja2
    import pdoc
    import pdoc.render

    title, body = guide()
    theme = design_system()
    pdoc.render.configure(
        docformat="google",
        footer_text=f"grepvine-sdk {version('grepvine-sdk')}",
        search=True,
        show_source=True,
        template_directory=TEMPLATES,
    )
    # Templates include the design system's stylesheets and SVGs by their paths in that repo.
    assert pdoc.render.env.loader is not None
    pdoc.render.env.loader = jinja2.ChoiceLoader(
        [pdoc.render.env.loader, jinja2.FileSystemLoader(theme)]
    )
    pdoc.render.env.globals.update(guide=body, guide_title=title, repository_url=REPOSITORY_URL)
    shutil.rmtree(output, ignore_errors=True)
    pdoc.pdoc(*module_specs(), output_directory=output)
    # GitHub Pages must serve the files as they are, without a Jekyll build.
    (output / ".nojekyll").touch()
    print(f"Documentation written to {output}")


if __name__ == "__main__":
    main()
