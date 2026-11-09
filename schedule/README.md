# Scheduling

Signals are worth most when new calls land every week without anyone remembering. Pick one way below.

## Who does the judgment steps

Each run needs an agent twice: to write a note per new call, and to match notes to signals.

- **The scheduler is an agent session** (a scheduled task in your agent app, or any agent that runs a prompt on a timer). Give it this prompt:
  ```
  In <path to customer-signals>, fetch the calls since the last run from <recorder>,
  add them with bin/cs add, then follow AGENTS.md § Each run and tell me what is new.
  ```
  This is the best option when calls come from a recorder connector, because the session can fetch them.
- **A headless agent CLI** does it, when calls already land in a folder. Put the command in `data/.env`:
  ```
  CS_AGENT_CMD=claude -p --model sonnet
  ```
  `codex exec` and `gemini -p` work the same way: prompt as the last argument, answer on stdout. `bin/cs run` sends each call alone, checks the note, retries once with the errors, then matches and applies. Then add your files and run `schedule/run-cycle.sh`.

## Schedulers for `run-cycle.sh`

### macOS: launchd

cron on macOS often cannot reach the keychain where agent CLIs keep their login; launchd runs as you. Save as `~/Library/LaunchAgents/dev.customer-signals.plist`, with the paths replaced. This runs every Monday at 07:00:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>dev.customer-signals</string>
  <key>ProgramArguments</key><array><string>/ABSOLUTE/PATH/customer-signals/schedule/run-cycle.sh</string></array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/ABSOLUTE/PATH/customer-signals/data/run.log</string>
  <key>StandardErrorPath</key><string>/ABSOLUTE/PATH/customer-signals/data/run.log</string>
</dict></plist>
```

Load it: `launchctl load ~/Library/LaunchAgents/dev.customer-signals.plist`.

### Linux: cron

```
0 7 * * 1 /ABSOLUTE/PATH/customer-signals/schedule/run-cycle.sh >> /ABSOLUTE/PATH/customer-signals/data/run.log 2>&1
```

### No scheduler

A weekly calendar reminder that says "run customer signals" works. The agent does the rest.

## Check it

After the first scheduled run, read `data/run.log`. The last lines are `RUN <date>: ok` and `== exit 0`. A failure names the call or the step. Pause any time with `bin/cs pause`.
