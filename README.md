# Gfeed

Convert your GitHub starred repositories into RSS feeds for easy tracking of updates.

## Overview

Gfeed allows you to follow updates from all your GitHub starred repositories by converting them into RSS feed formats. This makes it easy to track the latest releases, updates, and changes from projects you're interested in without having to manually check each repository.

This tool can export your GitHub stars in two formats:
- OPML format for importing into RSS readers like FreshRSS, MiniFlux, Feedly, etc.
- Configuration for [osmosfeed](https://github.com/osmoscraft/osmosfeed) static RSS reader (Not recommended)

## Installation

### Option 1: Download Binary

Pre-built binary files are available in the [releases page](https://github.com/yourusername/gfeed/releases).

### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/gfeed.git
cd gfeed

# Install dependencies (if needed)
uv sync

# Run from source
uv run gfeed --opml
```

## Usage

```bash
usage: gfeed.py [-h] (--osmos | --opml) [--debug]

options:
  -h, --help  show this help message and exit
  --osmos     Export GitHub starred repositories for osmosfeed.
  --opml      Export GitHub starred repositories as OPML file for RSS applications.
  --debug     More verbose output.
```

### Examples

Export to OPML format:
```bash
gfeed --opml
```

Export for osmosfeed (Not recommended):
```bash
gfeed --osmos
```

## Supported RSS Applications

You can use the generated OPML file with various RSS readers including:
- [FreshRSS](https://freshrss.org/)
- [MiniFlux](https://miniflux.app/)
- [Feedly](https://feedly.com/)
- [Inoreader](https://www.inoreader.com/)
- And most other RSS readers that support OPML imports

## Note About Windows Security

> [!IMPORTANT]
> Windows systems might flag the executable binary as a virus, but it is not. This is a common false positive with `pyinstaller`-generated binaries.

![virus](./assets/virus.png)
