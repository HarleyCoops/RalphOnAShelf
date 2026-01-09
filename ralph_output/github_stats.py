#!/usr/bin/env python3
"""
GitHub Stats CLI Tool
Fetches public repository statistics for a given GitHub username.
"""

import sys
import json
import requests
from typing import List, Dict, Any


def fetch_github_repos(username: str) -> List[Dict[str, Any]]:
    """
    Fetch all public repositories for a GitHub user.

    Args:
        username: GitHub username

    Returns:
        List of repository dictionaries
    """
    repos = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/users/{username}/repos"
        params = {
            "per_page": per_page,
            "page": page,
            "type": "public"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            page_repos = response.json()

            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            sys.exit(1)

    return repos


def calculate_total_stars(repos: List[Dict[str, Any]]) -> int:
    """
    Calculate total stars across all repositories.

    Args:
        repos: List of repository dictionaries

    Returns:
        Total star count
    """
    return sum(repo.get("stargazers_count", 0) for repo in repos)


def save_json_results(username: str, repos: List[Dict[str, Any]], total_stars: int) -> None:
    """
    Save results to github_stats.json.

    Args:
        username: GitHub username
        repos: List of repository dictionaries
        total_stars: Total star count
    """
    results = {
        "username": username,
        "total_repos": len(repos),
        "total_stars": total_stars,
        "repositories": [
            {
                "name": repo["name"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "language": repo["language"],
                "description": repo["description"],
                "url": repo["html_url"]
            }
            for repo in repos
        ]
    }

    with open("github_stats.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to github_stats.json")


def create_markdown_report(username: str, repos: List[Dict[str, Any]], total_stars: int) -> None:
    """
    Create a markdown summary report.

    Args:
        username: GitHub username
        repos: List of repository dictionaries
        total_stars: Total star count
    """
    # Sort repos by stars (descending)
    sorted_repos = sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)

    markdown = f"""# GitHub Stats Report for {username}

## Summary
- **Username**: {username}
- **Total Public Repositories**: {len(repos)}
- **Total Stars**: {total_stars}

## Top Repositories by Stars

"""

    # Add top 10 repositories
    for i, repo in enumerate(sorted_repos[:10], 1):
        stars = repo["stargazers_count"]
        forks = repo["forks_count"]
        name = repo["name"]
        language = repo["language"] or "N/A"
        description = repo["description"] or "No description"
        url = repo["html_url"]

        markdown += f"""### {i}. [{name}]({url})
- **Stars**: {stars}
- **Forks**: {forks}
- **Language**: {language}
- **Description**: {description}

"""

    # Add remaining repos if any
    if len(sorted_repos) > 10:
        markdown += "## Other Repositories\n\n"
        for repo in sorted_repos[10:]:
            name = repo["name"]
            stars = repo["stargazers_count"]
            url = repo["html_url"]
            markdown += f"- [{name}]({url}) - {stars} stars\n"

    with open("stats_report.md", "w") as f:
        f.write(markdown)

    print(f"Markdown report saved to stats_report.md")


def main():
    """Main entry point for the CLI tool."""
    if len(sys.argv) != 2:
        print("Usage: python github_stats.py <github_username>")
        sys.exit(1)

    username = sys.argv[1]

    print(f"Fetching repositories for user: {username}")
    repos = fetch_github_repos(username)

    if not repos:
        print(f"No public repositories found for user: {username}")
        sys.exit(1)

    total_stars = calculate_total_stars(repos)

    print(f"Found {len(repos)} repositories with {total_stars} total stars")

    save_json_results(username, repos, total_stars)
    create_markdown_report(username, repos, total_stars)

    print("Done!")


if __name__ == "__main__":
    main()
