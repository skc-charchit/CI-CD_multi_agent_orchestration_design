# Project guide feature

This is an independent React feature package. It is **not imported by or
included in the portfolio app**. The main site can be built and hosted as a
static app without this feature or the FastAPI backend.

## Current behavior

`ProjectChat` accepts project summaries with `id`, `name`, `full_name`,
`description`, `html_url`, `language`, and `default_branch`. It fetches a
selected public GitHub repository's README in the browser and returns relevant
README sections with a source link. It does not call an AI model, and it
reports when the README does not cover a question. No provider key or other
secret is required.

## Local checks

From this directory:

```bash
npm install
npm run build
```

## Future integration

The public component is exported from `src/ProjectChat.tsx`; the project input
contract is `ProjectSummary` in `src/github-readme.ts`. When integrating it
into the main frontend, install/link this package and pass project summaries
from the portfolio's project source. The current README retrieval can later be
replaced with a typed backend client to the Agentic AI feature. Keep model
credentials and provider calls on the server; do not add them to this package.
