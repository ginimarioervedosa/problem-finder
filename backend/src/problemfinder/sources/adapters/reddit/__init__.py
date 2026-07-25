"""Reddit posts via the official Data API (application-only OAuth).

Subreddits are configured in sources.toml; each work item is one page of a
subreddit's /new listing, and one signal is one post: a person describing a
problem in their own words. Credentials live in .env and are never committed.
"""
