from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?(?:\.post\d+)?(?:\.dev\d+)?$")


@dataclass(frozen=True)
class Package:
    dist_name: str
    import_name: str
    path: str
    public: bool
    internal_dependencies: tuple[str, ...] = ()


PACKAGES = [
    Package("zeroshot-commons", "zeroshot_commons", "packages/commons", True),
    Package(
        "zeroshot-commons-injectors",
        "zeroshot_commons_injectors",
        "packages/commons-injectors",
        True,
        ("zeroshot-commons",),
    ),
    Package(
        "zeroshot-commons-testing",
        "zeroshot_commons_testing",
        "packages/commons-testing",
        True,
        ("zeroshot-commons",),
    ),
    Package(
        "zeroshot-agentic-workflows",
        "zeroshot_agentic_workflows",
        "packages/agentic-workflows",
        True,
        ("zeroshot-commons",),
    ),
    Package(
        "zeroshot-openai-utils",
        "zeroshot_openai_utils",
        "packages/openai-utils",
        True,
        ("zeroshot-commons",),
    ),
    Package(
        "zeroshot-sql-decorators",
        "zeroshot_sql_decorators",
        "packages/sql-decorators",
        True,
        ("zeroshot-commons",),
    ),
    Package(
        "zeroshot-agent-experiments",
        "zeroshot_agent_experiments",
        "packages/agent-experiments",
        False,
        (
            "zeroshot-agentic-workflows",
            "zeroshot-commons-testing",
            "zeroshot-commons",
        ),
    ),
]

INTERNAL_PACKAGE_NAMES = {package.dist_name for package in PACKAGES}
PACKAGE_BY_NAME = {package.dist_name: package for package in PACKAGES}


def iter_packages(scope: str) -> list[Package]:
    if scope == "all":
        return PACKAGES
    if scope == "public":
        return [package for package in PACKAGES if package.public]
    if scope == "private":
        return [package for package in PACKAGES if not package.public]
    raise ValueError(f"unsupported scope: {scope}")


def package_matrix(scope: str) -> list[dict[str, str | bool]]:
    packages = iter_packages(scope)
    return [
        {
            "dist_name": package.dist_name,
            "import_name": package.import_name,
            "path": package.path,
            "public": package.public,
        }
        for package in packages
    ]


def replace_version(text: str, version: str) -> str:
    return re.sub(r'(?m)^version = "[^"]+"$', f'version = "{version}"', text, count=1)


def replace_internal_dependencies(text: str, version: str) -> str:
    pattern = re.compile(r"dependencies = \[(?P<body>.*?)\]", re.DOTALL)
    match = pattern.search(text)
    if not match:
        return text

    body = match.group("body")
    for package_name in sorted(INTERNAL_PACKAGE_NAMES, key=len, reverse=True):
        body = re.sub(
            rf'"{re.escape(package_name)}(?:[^"]*)"',
            f'"{package_name}=={version}"',
            body,
        )
    return text[: match.start("body")] + body + text[match.end("body") :]


def write_version(version: str) -> None:
    if not VERSION_PATTERN.match(version):
        raise SystemExit(f"unsupported version format: {version}")

    root_pyproject = ROOT / "pyproject.toml"
    root_pyproject.write_text(replace_version(root_pyproject.read_text(), version))

    for package in PACKAGES:
        pyproject = ROOT / package.path / "pyproject.toml"
        text = pyproject.read_text()
        text = replace_version(text, version)
        text = replace_internal_dependencies(text, version)
        pyproject.write_text(text)


def read_version(path: Path) -> str:
    match = re.search(r'(?m)^version = "(?P<version>[^"]+)"$', path.read_text())
    if not match:
        raise SystemExit(f"could not find version in {path}")
    return match.group("version")


def check_version(version: str) -> None:
    expected = version
    root_version = read_version(ROOT / "pyproject.toml")
    if root_version != expected:
        raise SystemExit(f"root version mismatch: expected {expected}, found {root_version}")

    for package in PACKAGES:
        pyproject = ROOT / package.path / "pyproject.toml"
        package_version = read_version(pyproject)
        if package_version != expected:
            raise SystemExit(
                f"{package.dist_name} version mismatch: expected {expected}, found {package_version}"
            )
        text = pyproject.read_text()
        dependencies_match = re.search(r"dependencies = \[(?P<body>.*?)\]", text, re.DOTALL)
        dependencies_body = dependencies_match.group("body") if dependencies_match else ""
        for internal_name in package.internal_dependencies:
            expected_dep = f'"{internal_name}=={expected}"'
            if expected_dep not in dependencies_body:
                raise SystemExit(
                    f"{package.dist_name} is missing expected internal dependency {expected_dep}"
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Workspace metadata and release helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List package names.")
    list_parser.add_argument("--scope", choices=("all", "public", "private"), default="all")
    list_parser.add_argument("--json", action="store_true")

    matrix_parser = subparsers.add_parser("matrix", help="Emit package metadata for CI.")
    matrix_parser.add_argument("--scope", choices=("all", "public", "private"), default="all")

    set_version_parser = subparsers.add_parser("set-version", help="Set the lockstep version.")
    set_version_parser.add_argument("version")

    check_version_parser = subparsers.add_parser(
        "check-version", help="Validate that all package versions match."
    )
    check_version_parser.add_argument("version")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "list":
        names = [package.dist_name for package in iter_packages(args.scope)]
        if args.json:
            print(json.dumps(names))
        else:
            print("\n".join(names))
        return 0

    if args.command == "matrix":
        print(json.dumps(package_matrix(args.scope)))
        return 0

    if args.command == "set-version":
        write_version(args.version)
        return 0

    if args.command == "check-version":
        check_version(args.version)
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
