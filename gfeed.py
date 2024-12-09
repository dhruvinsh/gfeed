import asyncio
import os
from typing import TYPE_CHECKING

import httpx
import yaml
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


async def get_star_repo(client: "AsyncClient") -> list[StarredRepo]:
    """Get star repository for user."""
    sr: list[StarredRepo] = []
    url = "https://api.github.com/user/starred?per_page=100"

    while True:
        print(f"Fetching {url}")
        resp = await client.get(url)
        data = resp.json()
        for repo in data:
            sr.append(
                StarredRepo(
                    name=repo["name"], full_name=repo["full_name"], url=repo["url"]
                )
            )

        try:
            url = resp.links["next"]["url"]
        except KeyError:
            break

    return sr


async def latest_release(
    client: "AsyncClient", repo: StarredRepo
) -> ReleaseData | None:
    """Get latest release for a repository."""
    resp = await client.get(repo.url + "/releases/latest")
    if resp.status_code == 404:
        return None

    data = resp.json()

    try:
        release = ReleaseData(
            full_name=repo.full_name,
            name=data["name"] or repo.full_name,
            html_url=data["html_url"],
            tag_name=data["tag_name"],
            atom=f"https://github.com/{repo.full_name}/releases.atom",
        )
    except Exception:
        print(f"Error: {repo.full_name}")
        return None

    return release


async def main():
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

    with open("osmosfeed.yaml", "w") as fp:
        yaml.dump({"sources": feed}, fp)

    with open("feed.opml", "wb") as fp:
        feed_opml.dump(fp)


if __name__ == "__main__":
    asyncio.run(main())
