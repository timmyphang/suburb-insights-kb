# Post-VIC School Batch — Next Steps

## Context

A DeerFlow agent on the GCP e2-micro VM (`telegram-speaker-bot`) is running
`run_vic_batch.py` against all 1,087 Primary + Combined schools in
`vic_schools.csv`. Each completed school profile is written as a markdown
file directly into the `suburb-insights-kb` GitHub repo and pushed.

The batch is **resumable** — if it crashes or the VM reboots, re-running the
script skips schools whose `.md` already exists in the repo.

## How to check if the batch has finished

```bash
# SSH to VM
~/google-cloud-sdk/bin/gcloud compute ssh telegram-speaker-bot --zone us-central1-a

# On the VM:
ps aux | grep run_vic | grep -v grep        # empty = finished
tail -20 ~/vic_batch.log                     # look for final summary line:
                                             #   [batch] done. ok=N skipped=N failed=N elapsed=NNm
git -C ~/suburb-insights-kb log --oneline -5 # recent commits
ls ~/suburb-insights-kb/markdown/schools/vic/ | wc -l  # should be ~1087-ish
```

**Throughput**: ~10-15 min per school on e2-micro. 1,087 schools ≈ 9-11 days.

---

## Step 1 — Retry failed/stub schools (if any)

The batch discards outputs under 2,000 chars (content-filter stubs) and counts
them as failures. To retry just those:

```bash
# On the VM — re-run the batch. It auto-skips completed schools and retries
# any that were STUB/FAILED since their .md was never written:
bash ~/run_vic_wrapper.sh
```

If the failure count is high (>50), inspect the log for patterns:

```bash
grep "STUB\|FAILED" ~/vic_batch.log | tail -30
```

Common causes:
- Azure content-filter trips on religious-school terminology
  (the `pi_coder_search/sanitize.py` adapter handles most cases, but edge
  cases exist). See `deerflow/README.md` → "Religious-school content-filter fix".
- Transient Azure API rate limits — just re-run.

---

## Step 2 — Rebuild `llms.txt` and `README.md` in the KB repo

The batch script only writes individual school `.md` files — it does **not**
update `llms.txt` or `README.md`. After the batch completes, regenerate them
from your local machine (the VM does not have the build script):

```bash
# On THIS machine (~/), not the VM:
python3 /tmp/build_kb.py
```

This script (`/tmp/build_kb.py`) reads from `~/suburb-insights/` source data
and rewrites the entire `~/suburb-insights-kb/` tree including `llms.txt`
and `README.md`. It preserves existing files and adds new ones.

**Important**: The build script reads the *local* copy of `suburb-insights-kb`.
Pull the VM's commits first:

```bash
git -C ~/suburb-insights-kb pull origin main
python3 /tmp/build_kb.py
git -C ~/suburb-insights-kb add -A
git -C ~/suburb-insights-kb commit -m "Rebuild llms.txt + README with VIC school profiles"
git -C ~/suburb-insights-kb push origin main
```

**Verify** the new file counts appear in `llms.txt`:

```bash
grep "^### " ~/suburb-insights-kb/llms.txt
# Expect: Schools / VIC (NNNN files) where NNNN ≈ 1087
```

---

## Step 3 — Verify the KB repo on GitHub

Spot-check that raw URLs resolve for newly-generated VIC schools:

```bash
# Pick a few new VIC school slugs
curl -sI https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/llms.txt | head -1
curl -sI https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/markdown/schools/vic/virtual-school-victoria.md | head -1
```

---

## Step 4 — (Optional) Generate VIC suburb profiles

The suburb posts on Google Drive (`gdrive:suburb-research-memes-output/posts/`)
have only **11 VIC-suffixed entries** out of 1,806 total. Most VIC suburbs
(e.g. Truganina) have no profile at all.

If you want VIC suburb profiles generated, the `run_qld_batch.py` pattern
in `~/naplan-data/suburb_research/deerflow/` can be adapted — but that
requires a suburb CSV input and a suburb-specific research prompt
(different from the school prompt). This is **not** part of the current
batch and should be scoped separately.

---

## Step 5 — Build the prompt assembler on Vercel

This is the original goal: a Next.js route on the suburb-insights Vercel
site that assembles a prompt and sends it to an agent which searches the
KB repo. The repo is now ready at:

- **Repo**: https://github.com/timmyphang/suburb-insights-kb
- **Agent entry point**: `https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/llms.txt`
- **Sample file URL**: `https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/markdown/suburbs/nsw/truganina-nsw.md`

The Vercel side needs:
1. A serverless API route (e.g. `/api/agent`) that accepts a user query.
2. Fetches `llms.txt` to discover available files.
3. Sends the user query + relevant MD context to an LLM (Azure OpenAI or
   similar) with instructions to answer using the KB.
4. Returns the response to the user.

**Note**: The suburb-insights Next.js app (`~/suburb-insights/`) has
`revalidate = 86400` (ISR, 24-hour cache) on suburb pages. The agent route
should be a separate dynamic API route, not ISR-cached.

**Important**: Read `~/suburb-insights/AGENTS.md` before writing Next.js
code — this Next.js version has breaking changes from standard conventions.
Check `node_modules/next/dist/docs/` for the correct APIs.

---

## Key files and locations

| File | Location | Purpose |
|---|---|---|
| `run_vic_batch.py` | `~/naplan-data/suburb_research/deerflow/` (local + VM) | VIC school batch script |
| `run_vic_wrapper.sh` | `~/run_vic_wrapper.sh` (VM only) | Env-loading wrapper for nohup |
| `build_kb.py` | `/tmp/build_kb.py` (local only) | Rebuilds `llms.txt` + `README.md` |
| `vic_schools.csv` | `~/naplan-data/states/vic/vic_schools.csv` (local + VM) | Input: 1,080 VIC schools |
| `vic_batch.log` | `~/vic_batch.log` (VM only) | Batch run log |
| KB repo | `~/suburb-insights-kb/` (local + VM) | The markdown knowledge base |
| DeerFlow config | `~/naplan-data/suburb_research/deerflow/config.yaml` | Agent config (gpt-5-mini, pi-coder search) |
| Azure key | `~/deer-flow/.env` (VM only) | `AZURE_OPENAI_API_KEY` |

## VM access

```bash
# From this machine:
~/google-cloud-sdk/bin/gcloud compute ssh telegram-speaker-bot --zone us-central1-a

# Project: polar-reef-486402-q3
# Zone: us-central1-a
# Instance: telegram-speaker-bot (e2-micro, 2 vCPU, 958 MB RAM + 2 GB swap)
# User: tim
# NEVER use `gcloud compute ssh` without the --command flag for long-running
# tasks — it stays attached. Use nohup with </dev/null redirect.
```
