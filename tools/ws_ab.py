"""Voice A/B probe over the ElevenLabs Conversational AI WebSocket.

Delegates to ``python -m consent_lab probe``. This spends credits. It refuses
to run unless LIVE_ENABLED=1. The key and the agent id come from the environment.
"""

from __future__ import annotations

import sys

from consent_lab.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["probe", *sys.argv[1:]]))
