#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup, Tag

BASE = "https://www.apkmirror.com"

ARCHITECTURE_PATTERN = re.compile(
    r"\b(universal|arm64-v8a|armeabi-v7a|x86_64|x86)\b",
    re.IGNORECASE,
)
DPI_PATTERN = re.compile(r"\b(?:\d+-\d+dpi|nodpi)\b", re.IGNORECASE)


@dataclass
class Version:
    version: str
    link: str


@dataclass
class Variant:
    is_bundle: bool
    architecture: str
    dpi: str
    link: str


_scraper = None


def scraper():
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper()
        _scraper.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/156.0.0.0 Safari/537.36"
                )
            }
        )
    return _scraper


def get(url: str):
    response = scraper().get(url, timeout=60)
    response.raise_for_status()
    return response


def version_from_string(version: str) -> Version:
    slug = version.replace(".", "-")
    return Version(version, f"{BASE}/apk/x-corp/twitter/x-{slug}-release/")


def get_variants(version: Version) -> list[Variant]:
    soup = BeautifulSoup(get(version.link).content, "html.parser")
    table = soup.find("div", class_="table")
    if table is None:
        raise RuntimeError(f"Could not find variant table for {version.version}")

    variants: list[Variant] = []
    rows = cast(Tag, table).find_all("div", recursive=False)[1:]
    for row in rows:
        cells = row.find_all("div", class_="table-cell", recursive=False)
        if len(cells) < 2:
            continue
        badge = row.find("span", class_="apkm-badge")
        anchor = row.find("a", class_="accent_color", href=True)
        if anchor is None:
            continue

        cell_texts = [cell.get_text(" ", strip=True) for cell in cells]
        architecture = next(
            (text for text in cell_texts if ARCHITECTURE_PATTERN.search(text)),
            cell_texts[1],
        )
        dpi = next((text for text in cell_texts if DPI_PATTERN.search(text)), "")

        variants.append(
            Variant(
                is_bundle=badge is not None and badge.get_text(strip=True) == "BUNDLE",
                architecture=architecture,
                dpi=dpi,
                link=urljoin(BASE, cast(Tag, anchor)["href"]),
            )
        )
    return variants


def bundle_score(variant: Variant) -> tuple[int, int, int, int]:
    """Prefer ARM bundles with both ABIs, then modern phone DPI buckets."""
    architecture = variant.architecture.lower()
    dpi = variant.dpi.lower()

    has_arm = int("arm64-v8a" in architecture or "armeabi-v7a" in architecture)
    has_both_arm_abis = int(
        "arm64-v8a" in architecture and "armeabi-v7a" in architecture
    )
    preferred_dpi = int("480-640" in dpi or "640" in dpi)
    has_arm64 = int("arm64-v8a" in architecture)
    return has_arm, has_both_arm_abis, preferred_dpi, has_arm64


def choose_source_bundle(version: Version) -> Variant:
    variants = get_variants(version)

    for variant in variants:
        if variant.is_bundle and "universal" in variant.architecture.lower():
            return variant

    bundles = [variant for variant in variants if variant.is_bundle]
    if not bundles:
        raise RuntimeError(
            f"Could not find an APKM bundle for X {version.version}. "
            f"Found: {[(v.architecture, v.dpi, v.is_bundle) for v in variants]}"
        )

    return max(bundles, key=bundle_score)


def download_bundle(version: Version, output: Path) -> None:
    variant = choose_source_bundle(version)
    page = BeautifulSoup(get(variant.link).content, "html.parser")
    button = page.find("a", class_="downloadButton", href=True)
    if button is None:
        raise RuntimeError("Could not find APKMirror download button")

    download_page_url = urljoin(BASE, cast(Tag, button)["href"])
    download_page = BeautifulSoup(get(download_page_url).content, "html.parser")
    direct = download_page.find("a", rel="nofollow", href=True)
    if direct is None:
        raise RuntimeError("Could not find APKMirror direct download link")

    direct_url = urljoin(BASE, cast(Tag, direct)["href"])
    print(f"Downloading {version.version} from {direct_url}", file=sys.stderr)
    with scraper().get(
        direct_url,
        headers={"Referer": download_page_url},
        timeout=120,
        stream=True,
    ) as response:
        response.raise_for_status()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    download = sub.add_parser("download")
    download.add_argument("version")
    download.add_argument("output", type=Path)

    args = parser.parse_args()
    if args.command == "download":
        download_bundle(version_from_string(args.version), args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
