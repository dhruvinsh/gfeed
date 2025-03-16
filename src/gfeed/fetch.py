import argparse
import asyncio
import os
import sys
from typing import TYPE_CHECKING

import httpx
import yaml
from loguru import logger
from opml import OpmlDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from httpx import AsyncClient


class StarredRepo(BaseModel):
    """Data store for stared repo with minimal information."""

    name: str
    full_name: str
    url: str


class ReleaseData(BaseModel):
    """Data store for release information and rss feed."""

    full_name: str
    name: str
    html_url: str
    tag_name: str
    atom: str


async def fetch_star_repo(
    client: "AsyncClient", url: str
) -> tuple[list[dict[str, str]], str | None]:
    """Fetch star repository for user."""
    logger.info(f"Fetching {url}")
    resp = await client.get(url)
    return resp.json(), resp.links.get("next", {}).get("url")


def transform_repo_data(data: list[dict[str, str]]) -> list[StarredRepo]:
    """Transform repository data to StarredRepo model."""
    return [
        StarredRepo(name=repo["name"], full_name=repo["full_name"], url=repo["url"])
        for repo in data
    ]


async def get_star_repo(client: "AsyncClient") -> list[StarredRepo]:
    """Get star repository for user."""
    sr: list[StarredRepo] = []
    url: str | None = "https://api.github.com/user/starred?per_page=100"

    while url:
        data, url = await fetch_star_repo(client, url)
        sr.extend(transform_repo_data(data))
        return sr

    return sr


async def fetch_latest_release(
    client: "AsyncClient", repo: StarredRepo
) -> dict[str, str] | None:
    """Fetch latest release for a repository."""
    url = repo.url + "/releases/latest"
    logger.debug(f"Fetching latest release: {url}")
    resp = await client.get(url)
    if resp.status_code == 404:
        return None

    return resp.json()


def transform_release_data(
    data: dict[str, str], repo: StarredRepo
) -> ReleaseData | None:
    """Transform release data to ReleaseData model."""
    try:
        return ReleaseData(
            full_name=repo.full_name,
            name=data["name"] or repo.full_name,
            html_url=data["html_url"],
            tag_name=data["tag_name"],
            atom=f"https://github.com/{repo.full_name}/releases.atom",
        )
    except KeyError as e:
        logger.error(f"Error paring release data for {repo.full_name}: {e}")
        return None


async def latest_release(
    client: "AsyncClient", repo: StarredRepo
) -> ReleaseData | None:
    """Get latest release for a repository."""
    data = await fetch_latest_release(client, repo)
    if data is None:
        return None

    return transform_release_data(data, repo)


async def main(osmos: bool, opml: bool):
    token = os.environ.get("GITHUB_TOKEN")
    if token is None:
        raise ValueError("Please set GITHUB_TOKEN environment variable")

    headers = httpx.Headers(
        {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        repos = await get_star_repo(client)
        tasks = [latest_release(client, repo) for repo in repos]
        releases = await asyncio.gather(*tasks)

    feed = []
    feed_opml = OpmlDocument()
    for release in releases:
        if release is not None:
            feed.append({"href": release.atom})
            feed_opml.add_rss(
                text=f"Release from {release.full_name}",
                xml_url=release.atom,
                html_url=release.html_url,
                title=f"Release from {release.full_name}",
            )

    if osmos:
        with open("osmosfeed.yaml", "w") as fp:
            yaml.dump({"sources": feed}, fp)

    if opml:
        with open("feed.opml", "wb") as fp:
            feed_opml.dump(fp, pretty=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--osmos", action="store_true", help="Export github star repo(s) for osmosfeed."
    )
    group.add_argument(
        "--opml",
        action="store_true",
        help="Export github star repo(s) for RSS application as opml file.",
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="More verbose output."
    )

    args = parser.parse_args()

    logger.remove()
    if args.debug:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

    asyncio.run(main(args.osmos, args.opml))
