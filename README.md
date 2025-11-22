# autopsy

AI-powered RCA generator for AWS incidents. Feed it a CloudWatch log group, a time window, and the alert that fired — it pulls the logs, correlates recent GitHub Actions deploys, and drafts a structured postmortem using Claude.

Built because writing RCAs manually at 3am after a 2-hour incident is one of the worst parts of on-call.

---

## What it does

1. Fetches CloudWatch log events for the incident window (plus 10 min pre-window for context)
2. Pulls GitHub Actions workflow runs from the 24h before the incident
3. Filters health check noise automatically
4. Sends everything to Claude with a structured RCA prompt
5. Outputs a markdown postmortem with timeline, root cause, deploy correlation, contributing factors, and action items

---

## Example output

```markdown
# ECS Service Crash — Connection Pool Exhaustion

| Field | Value |
|---|---|
| Severity | P1 |
| Start | 2026-04-08T02:00:00 |
| Duration | 45 minutes |
| Alert | ECS TaskCount dropped below threshold |

## Root Cause
DB connection pool limit (max_connections=20) was not increased when the deploy
doubled service instances from 4 to 8, exhausting available connections.

## Deploy Correlation
Commit abc12345 deployed 30 minutes before incident attempted to fix pool size
but used the wrong config key.

## Action Items
| Priority | Action | Owner |
|---|---|---|
| HIGH | Add pre-deploy check for DB connection pool headroom | platform-team |
| HIGH | Align staging DB config with production | infra |
```

---

## Setup

```bash
git clone https://github.com/Sage-Canty/autopsy
cd autopsy
pip install -r requirements.txt
```

Set environment variables:

```bash
export ANTHROPIC_API_KEY=your_key_here
export GITHUB_TOKEN=your_github_token      # optional, for deploy history
```

AWS credentials via standard boto3 chain (`~/.aws/credentials`, env vars, or instance profile).

---

## Usage

```bash
# Basic — logs only
python src/main.py \
  --log-group /aws/ecs/payment-service \
  --start-time 2026-04-08T02:00:00 \
  --end-time 2026-04-08T03:00:00 \
  --alert "ECS TaskCount dropped below threshold"

# With deploy history
python src/main.py \
  --log-group /aws/ecs/payment-service \
  --start-time 2026-04-08T02:00:00 \
  --end-time 2026-04-08T03:00:00 \
  --alert "ECS TaskCount dropped below threshold" \
  --repo your-org/your-app

# Dry run — see what data was collected without calling Claude
python src/main.py \
  --log-group /aws/ecs/payment-service \
  --start-time 2026-04-08T02:00:00 \
  --end-time 2026-04-08T03:00:00 \
  --alert "ECS TaskCount dropped below threshold" \
  --repo your-org/your-app \
  --dry-run

# Custom output file
python src/main.py \
  --log-group /aws/ecs/payment-service \
  --start-time 2026-04-08T02:00:00 \
  --end-time 2026-04-08T03:00:00 \
  --alert "ECS TaskCount dropped below threshold" \
  --output incidents/2026-04-08-payment-outage.md
```

---

## Running tests

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Stack

- **Python** — CLI and data ingestion
- **boto3** — CloudWatch Logs
- **GitHub REST API** — Actions workflow history
- **Claude API** — RCA synthesis (claude-sonnet-4)

---

## Why this exists

Every team doing incident response writes RCAs manually — digging through logs, reconstructing timelines, correlating deploys. It's slow, tedious, and happens when you're already exhausted from the incident itself. This tool does the first draft so engineers can focus on validating and improving it instead of building it from scratch at 3am.
## Related

The runbooks and postmortem templates that informed this tool live in [Platform-Runbooks](https://github.com/Sage-Canty/Platform-Runbooks) — severity levels, escalation paths, and triage steps for AWS/ECS incidents.
