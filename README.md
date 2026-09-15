# Numerical Validation Datasets

A small catalog and command-line downloader for numerical validation data.

The repository contains dataset descriptions and direct download links. The
data itself is downloaded from its original source and is not committed here.

## Available datasets

- **CFD:** cavity flow, airfoils, jets, separated flows, turbomachinery, and heat transfer
- **DEM:** particle packing and rolling-clump validation
- **FEM:** Poisson and elasticity examples
- **Linear algebra:** sparse matrices and linear systems
- **ODE/DAE:** simulator conformance tests with expected results
- **Optimization:** mixed-integer, quadratic, and semidefinite problems
- **Statistics:** certified regression reference data

```bash
./download.sh list
./download.sh download --name onera_m6
./download.sh download --all
```

## Requirements

- Bash
- Python 3
- Internet access

No Python packages are required.

## Browse the catalog

List every dataset:

```bash
./download.sh list
```

Filter by category or search the catalog:

```bash
./download.sh list --category cfd
./download.sh list --search turbulence
./download.sh list --category cfd --search turbulence
```

Show one dataset in detail:

```bash
./download.sh list --name onera_m6
```

## Download

Download one dataset:

```bash
./download.sh download --name onera_m6
```

Download a category:

```bash
./download.sh download --category linear_algebra
```

Download everything:

```bash
./download.sh download --all
```

The command prints the files, sources, destination, and total size before it
downloads. Existing local files are overwritten.

Downloads are written to:

```text
datasets/<category>/<name>/
```

That directory is ignored by Git. Each download also creates a local
`source.md` from the catalog entry.

## Check links

Check every direct download link without keeping the files:

```bash
./download.sh check
```

Check one category or dataset:

```bash
./download.sh check --category cfd
./download.sh check --name onera_m6
```

## Repository structure

```text
catalog/                 one JSON file per dataset
scripts/download.py      catalog and download logic
download.sh              command-line entry point
datasets/                local downloads, ignored by Git
```

Current catalog categories are `cfd`, `dem`, `fem`, `linear_algebra`, `ode_dae`,
`optimization`, and `statistics`.

## Add a dataset

Create one JSON file under `catalog/<category>/`:

```json
{
  "name": "example",
  "category": "cfd",
  "title": "Example dataset",
  "type": "Experimental validation",
  "summary": "A short description.",
  "sources": [
    {
      "label": "Project page",
      "url": "https://example.org/dataset"
    }
  ],
  "files": [
    {
      "name": "results.dat",
      "url": "https://example.org/results.dat",
      "size_bytes": 1234,
      "description": "Reference results."
    }
  ]
}
```

Only these fields are required:

- Dataset: `name`, `category`, `title`, `summary`, and `files`
- Each file: `name` and `url`

Everything else, including sizes, descriptions, sources, type, DOI, license, and
notes, is optional. The downloader discovers JSON files automatically, so no
code change is needed.

## Inclusion rule

Every listed file must be downloadable non-interactively through a direct HTTP
or HTTPS URL. A dataset must not require a login, API key, browser interaction,
cookies, special client, or additional Python package.

Dataset ownership, credit, licensing, and terms remain with the original
publishers. Follow the source links in each catalog entry before using or
redistributing downloaded data.
