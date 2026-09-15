#!/usr/bin/env python3
"""Browse, download, and check cataloged numerical datasets."""

import argparse
import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
DATASETS = ROOT / "datasets"
USER_AGENT = "numerical-validation-datasets"


def load_catalog():
    datasets = []
    names = set()

    for path in sorted(CATALOG.rglob("*.json")):
        dataset = json.loads(path.read_text(encoding="utf-8"))

        for field in ("name", "category", "title", "summary", "files"):
            if field not in dataset:
                raise ValueError(f"{path}: missing required field '{field}'")
        if not dataset["files"]:
            raise ValueError(f"{path}: files cannot be empty")
        if dataset["name"] in names:
            raise ValueError(f"duplicate dataset name: {dataset['name']}")
        for file in dataset["files"]:
            if "name" not in file or "url" not in file:
                raise ValueError(f"{path}: every file needs 'name' and 'url'")

        names.add(dataset["name"])
        datasets.append(dataset)

    return datasets


def select_datasets(datasets, name=None, category=None, search=None):
    selected = datasets

    if name:
        selected = [dataset for dataset in selected if dataset["name"] == name]
    if category:
        selected = [dataset for dataset in selected if dataset["category"] == category]
    if search:
        query = search.lower()
        selected = [
            dataset
            for dataset in selected
            if query
            in " ".join(
                [
                    dataset["name"],
                    dataset["category"],
                    dataset["title"],
                    dataset.get("type", ""),
                    dataset["summary"],
                ]
            ).lower()
        ]

    return selected


def format_size(size):
    if size is None:
        return "unknown"

    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def dataset_size(dataset):
    sizes = [file.get("size_bytes") for file in dataset["files"]]
    if not all(isinstance(size, int) for size in sizes):
        return None
    return sum(sizes)


def print_table(datasets):
    print(f"{'CATEGORY':<16} {'NAME':<32} SIZE")
    for dataset in datasets:
        print(
            f"{dataset['category']:<16} "
            f"{dataset['name']:<32} "
            f"{format_size(dataset_size(dataset))}"
        )


def print_details(dataset):
    destination = DATASETS / dataset["category"] / dataset["name"]

    print(f"\nName:        {dataset['name']}")
    print(f"Category:    {dataset['category']}")
    if dataset.get("type"):
        print(f"Type:        {dataset['type']}")
    print(f"Size:        {format_size(dataset_size(dataset))}")
    print(f"Destination: {destination}")
    print(f"\n{dataset['summary']}")

    print("\nFiles:")
    for file in dataset["files"]:
        print(f"  {file['name']} ({format_size(file.get('size_bytes'))})")
        if file.get("description"):
            print(f"    {file['description']}")

    if dataset.get("sources"):
        print("\nSources:")
        for source in dataset["sources"]:
            if source.get("url"):
                print(f"  {source.get('label', 'Source')}: {source['url']}")

    if dataset.get("doi"):
        print(f"\nDOI: {dataset['doi']}")
    if dataset.get("license"):
        print(f"License: {dataset['license']}")
    if dataset.get("notes"):
        print("\nNotes:")
        for note in dataset["notes"]:
            print(f"  {note}")
    print()


def make_source_md(dataset):
    lines = [
        f"# {dataset['title']}",
        "",
        dataset["summary"],
    ]

    if dataset.get("type"):
        lines += ["", f"**Reference type:** {dataset['type']}"]
    if dataset.get("doi"):
        lines += ["", f"**DOI:** {dataset['doi']}"]
    if dataset.get("license"):
        lines += ["", f"**License:** {dataset['license']}"]

    if dataset.get("sources"):
        lines += ["", "## Sources", ""]
        for source in dataset["sources"]:
            if source.get("url"):
                lines.append(f"- [{source.get('label', 'Source')}]({source['url']})")

    lines += ["", "## Files", ""]
    for file in dataset["files"]:
        line = f"- `{file['name']}`"
        if file.get("description"):
            line += f": {file['description']}"
        lines.append(line)

    if dataset.get("notes"):
        lines += ["", "## Notes", ""]
        for note in dataset["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines) + "\n"


def download_file(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request) as source, destination.open("wb") as output:
        shutil.copyfileobj(source, output)


def download_dataset(dataset):
    print_details(dataset)
    destination = DATASETS / dataset["category"] / dataset["name"]
    destination.mkdir(parents=True, exist_ok=True)

    for file in dataset["files"]:
        print(f"Downloading {file['name']}")
        download_file(file["url"], destination / file["name"])

    (destination / "source.md").write_text(make_source_md(dataset), encoding="utf-8")


def check_datasets(datasets):
    failures = 0
    for dataset in datasets:
        for file in dataset["files"]:
            label = f"{dataset['name']}/{file['name']}"
            request = urllib.request.Request(
                file["url"],
                headers={"Range": "bytes=0-0", "User-Agent": USER_AGENT},
            )
            try:
                with urllib.request.urlopen(request, timeout=30):
                    print(f"[OK]   {label}")
            except (urllib.error.URLError, TimeoutError) as error:
                print(f"[FAIL] {label}: {error}")
                failures += 1
    return failures


def main():
    parser = argparse.ArgumentParser(description="Numerical validation dataset downloader")
    commands = parser.add_subparsers(dest="command", required=True)

    list_parser = commands.add_parser("list", help="browse the catalog")
    list_parser.add_argument("--name")
    list_parser.add_argument("--category")
    list_parser.add_argument("--search")

    download_parser = commands.add_parser("download", help="download datasets")
    download_choice = download_parser.add_mutually_exclusive_group(required=True)
    download_choice.add_argument("--name")
    download_choice.add_argument("--category")
    download_choice.add_argument("--all", action="store_true")

    check_parser = commands.add_parser("check", help="check direct download links")
    check_choice = check_parser.add_mutually_exclusive_group()
    check_choice.add_argument("--name")
    check_choice.add_argument("--category")

    args = parser.parse_args()
    datasets = load_catalog()
    selected = select_datasets(
        datasets,
        name=getattr(args, "name", None),
        category=getattr(args, "category", None),
        search=getattr(args, "search", None),
    )

    if not selected:
        parser.error("no matching datasets")

    if args.command == "list":
        if args.name:
            print_details(selected[0])
        else:
            print_table(selected)
    elif args.command == "download":
        for dataset in selected:
            download_dataset(dataset)
    else:
        raise SystemExit(1 if check_datasets(selected) else 0)


if __name__ == "__main__":
    main()
