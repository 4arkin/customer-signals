#!/bin/sh
# One unattended cycle: notes for new calls → check → match → apply, through the agent in CS_AGENT_CMD.
# Point cron or launchd at this file. Output goes to stdout; redirect it to data/run.log.
cd "$(dirname "$0")/.." || exit 1
# Schedulers start with a minimal PATH; agent CLIs usually live in one of these.
PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PATH
echo "== $(date -u +%Y-%m-%dT%H:%M:%SZ) customer-signals run"
python3 bin/cs run
rc=$?
echo "== exit $rc"
exit $rc
