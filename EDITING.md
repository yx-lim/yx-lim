# Editing your profile

Edit `README.md` to update your introduction, stack, links, and project descriptions.
The bracketed text is intentionally left for you to personalize. Public repository
descriptions were used for the initial project list; they do not imply authorship of
upstream projects.

Edit `DISPLAY_NAME`, `USERNAME`, or the colors near the top of
`scripts/generate_graphics.py` to change the identity graphic and visual theme.
The YX monogram is an original character-grid design; no portrait is required.
The graphics adapt to light and dark color schemes and use a system monospace font.

The daily workflow updates only `assets/`; it never overwrites your README copy.
You can also run it from Actions > Refresh profile graphics > Run workflow.
Daily runs are scheduled at 06:17 UTC, but GitHub may delay scheduled jobs.
GitHub can disable scheduled workflows after 60 days of repository inactivity;
re-enable the workflow in Actions if that happens.

Repository totals cover public repositories. Original repositories exclude forks
and the profile repository. Stars are summed across those original repositories.
Language graphics sum GitHub's language-byte totals, excluding forks and the profile.
The contribution calendar follows GitHub's visible contribution data and may include
anonymous private contribution counts if you have enabled them on your profile.
No private repository names, content, or contact information are collected.

To regenerate locally, authenticate the GitHub CLI and run:

```sh
python3 scripts/generate_graphics.py
```

Alternatively, provide `GITHUB_TOKEN` and `GH_LOGIN` through your environment.
The script uses Python's standard library and needs no additional packages.
