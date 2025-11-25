# AI Coding Assistant Usage Monitor

Tools for monitoring usage statistics of AI coding assistants (Claude Code, Gemini CLI).

## Tools

| Tool | Description | Data Source |
|------|-------------|-------------|
| `claude-usage.py` | Claude CLI analyzer with ASCII charts | `~/.claude/projects/**/*.jsonl` |
| `claude-subscription-usage.py` | Claude real-time subscription quota | Claude Code `/usage` |
| `claude-tray-indicator.py` | Claude GNOME system tray indicator | `~/.claude/projects/**/*.jsonl` |
| `gemini-usage.py` | Gemini CLI analyzer with ASCII charts | `~/.gemini/tmp/chats/*.json` |

## Quick Start

```bash
# Claude token usage (last 7 days)
python3 claude-usage.py
python3 claude-usage.py --days 30

# Gemini token usage (last 7 days)
python3 gemini-usage.py
python3 gemini-usage.py --days 30

# Claude subscription quota (Claude Max)
pip install pexpect
python3 claude-subscription-usage.py
python3 claude-subscription-usage.py --compact  # for scripting

# Claude system tray indicator (GNOME)
sudo dnf install python3-gobject libappindicator-gtk3  # or apt equivalent
./claude-tray-indicator.py
```

## Output Examples

**Subscription usage:**
```
Current session           : ██                    4% used
Current week (all models) : ███                   7% used
Current week (Opus)       :                       0% used
```

**Tray indicator format:** `I: 32K  O: 5K  CI: 123M  CO: 5M`

## Data Sources

- **Claude token tools**: Parse `~/.claude/projects/**/*.jsonl`
- **Claude subscription tool**: Queries Claude Code CLI via `pexpect` (~10-15s per run)
- **Gemini token tool**: Parse `~/.gemini/tmp/chats/session-*.json`

## Tray Indicator Autostart

```bash
mkdir -p ~/.config/autostart
sed "s|/home/USER|$HOME|g" claude-usage-indicator.desktop > ~/.config/autostart/claude-usage-indicator.desktop
```
