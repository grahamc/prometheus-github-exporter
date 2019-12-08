#!/usr/bin/env python3

from prometheus_client import start_http_server, Histogram, Counter, Gauge
import requests
import datetime
from pprint import pprint
from time import sleep
import sys
import json


REQUEST_TIME = Histogram(
    "github_issue_search_seconds", "Time taken searching GitHub Issues"
)
REQUEST_FAILURE = Counter(
    "github_issue_search_failures", "Count of failures to search issues"
)
SCRAPES = Counter("github_issue_scrapes", "Count of scrapes", ["repo"])


def labelval(param):
    return param.split(":")[1]


@REQUEST_FAILURE.count_exceptions()
def count_search_results(q):
    # the rate limit gives us 1 request every 6 seconds
    # (10 requests a minute.) Bump up to a delay of 7 seconds to
    # ensure we don't race that final request.
    sleep(7)
    with REQUEST_TIME.time():
        return requests.get(
            "https://api.github.com/search/issues", params={"q": q, "per_page": 1}
        ).json()["total_count"]


prs = Gauge(
    "github_prs",
    "Count of GitHub issues",
    ["repo", "state", "merged", "status", "review"],
)


def scrape_repo_prs(repo):
    state_q = ["is:open", "is:closed"]
    merge_q = ["is:merged", "is:unmerged"]
    status_q = ["status:pending", "status:success", "status:failure"]
    review_q = [
        "review:none",
        "review:required",
        "review:approved",
        "review:changes_requested",
    ]
    for state in state_q:
        for merge in merge_q:
            for status in status_q:
                for review in review_q:
                    if merge == "is:merged" and state == "is:open":
                        # a merged PR will never be open
                        continue
                    else:
                        q = f"repo:{repo} is:pr {state} {merge} {status} {review}"
                        prs.labels(
                            repo,
                            labelval(state),
                            labelval(merge),
                            labelval(status),
                            labelval(review),
                        ).set(count_search_results(q))


issues = Gauge("github_issues", "Count of GitHub issues", ["repo", "state"])


def scrape_repo_issues(repo):
    state_q = ["is:open", "is:closed"]
    for state in state_q:
        q = f"repo:{repo} is:issue {state}"
        issues.labels(repo, labelval(state)).set(count_search_results(q))


if __name__ == "__main__":
    with open(sys.argv[1]) as config_file:
        config = json.load(config_file)
        port = config["port"]
        repos = config["repos"]
    start_http_server(port)

    while True:
        for repo in repos:
            scrape_repo_issues(repo)
            scrape_repo_prs(repo)
            SCRAPES.labels(repo).inc()
