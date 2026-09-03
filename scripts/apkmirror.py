#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup, Tag

BASE = "https://www.apkmirror.com"
APP_URL = f"{BASE}/apk/x-corp/twitter/"


@dataclass
class Version:
    version: str
    link: str


@dataclass
class Variant:
    is_bundle: bool
    architecture: str
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
                    "Chrome/152.0.0.0 Safari/537.36"
                )
            }
        )
    return _scraper


def get(url: str):
    response = scraper().get(url, timeout=60)
    response.raise_for_status()
    return response


def get_versions() -> list[Version]:
    soup = BeautifulSoup(get(APP_URL).text, "html.parser")
    widget = soup.find("div", class_="listWidget")
    if widget is None:
        raise RuntimeError("Could not find APKMirror version list")

    versions: list[Version] = []
    for row in cast(Tag, widget).find_all("div", recursive=False)[1:]:
        value = row.find("span", class_="infoSlide-value")
        anchor = row.find("a", href=True)
        if value is None or anchor is None:
            continue
        text = value.get_text(strip=True)
        versions.append(Version(text, urljoin(BASE, cast(Tag, anchor)["href"])))
    return versions


def latest_release() -> Version:
    for item in get_versions():
        if "release" in item.version.lower():
            return item
    raise RuntimeError("Could not find an X release build on APKMirror")


def version_from_string(version: str) -> Version:
    for item in get_versions():
        if item.version == version:
            return item

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
        architecture = cells[1].get_text(" ", strip=True)
        variants.append(
            Variant(
                is_bundle=badge is not None and badge.get_text(strip=True) == "BUNDLE",
                architecture=architecture,
                link=urljoin(BASE, cast(Tag, anchor)["href"]),
            )
        )
    return variants


def choose_universal_bundle(version: Version) -> Variant:
    variants = get_variants(version)
    for variant in variants:
        if variant.is_bundle and "universal" in variant.architecture.lower():
            return variant
    raise RuntimeError(
        f"Could not find a universal APKM bundle for X {version.version}. "
        f"Found: {[(v.architecture, v.is_bundle) for v in variants]}"
    )


def download_bundle(version: Version, output: Path) -> None:
    variant = choose_universal_bundle(version)
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

    sub.add_parser("latest")

    download = sub.add_parser("download")
    download.add_argument("version")
    download.add_argument("output", type=Path)

    args = parser.parse_args()
    if args.command == "latest":
        print(latest_release().version)
        return 0

    if args.command == "download":
        download_bundle(version_from_string(args.version), args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
