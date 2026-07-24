# suburb-insights-kb

Markdown knowledge base for [Suburb Insights](https://suburb-insights-six.vercel.app) — optimised for AI-agent consumption, modelled on the [ServiceNowDocs](https://github.com/ServiceNow/ServiceNowDocs) pattern.

## Contents

- `markdown/suburbs/{nsw,qld,vic}/` — per-suburb "At a glance" profiles (one `.md` per suburb, named `<slug>-<state>.md`).
- `markdown/schools/{nsw,qld,vic}/` — per-school in-depth reviews (one `.md` per school).
- `llms.txt` — directory of all files grouped by category/state. Agents should read this first.

## How an agent consumes this

1. Read `llms.txt` to discover what is available.
2. Fetch a specific file via its raw URL, e.g.
   `https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/markdown/suburbs/vic/truganina-vic.md`
3. Each suburb `.md` begins with `# <Name> (<STATE>)` then the post body.
   Each school `.md` is the original generated review, ending with a `Sources` list.

## Refresh cadence

Updated whenever the suburb-research-memes regeneration pipeline produces new posts. New files are added with the same naming convention; superseded files are overwritten in place.

## Stats

- Suburbs: 1806 (nsw: 1466, qld: 315, sa: 5, vic: 11, wa: 9)
- Schools: 1714 (qld: 584, nsw: 1091, vic: 39)
