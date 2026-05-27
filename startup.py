"""
Railway entry point — writes YouTube OAuth files from env vars, then runs --draft.

Set these env vars in Railway dashboard before deploying:
  YOUTUBE_TOKEN_JSON          base64-encoded contents of youtube_token.json
  YOUTUBE_CLIENT_SECRET_JSON  base64-encoded contents of client_secret.json
"""

import base64, os, subprocess, sys


def _write_from_env(env_var: str, file_path: str) -> bool:
    value = os.environ.get(env_var, "").strip()
    if not value:
        print(f"[startup] {env_var} not set — skipping {file_path}")
        return False
    try:
        data = base64.b64decode(value)
    except Exception:
        data = value.encode()
    with open(file_path, "wb") as f:
        f.write(data)
    print(f"[startup] Wrote {file_path} from {env_var} ({len(data)} bytes)")
    return True


# Write YouTube OAuth token from env var so upload step can authenticate
token_file  = os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json")
secret_file = os.environ.get("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

_write_from_env("YOUTUBE_TOKEN_JSON", token_file)
_write_from_env("YOUTUBE_CLIENT_SECRET_JSON", secret_file)

# Run the orchestrator
cmd = [sys.executable, "studio/orchestrator.py", "--draft"]
print(f"[startup] Running: {' '.join(cmd)}")
result = subprocess.run(cmd)
sys.exit(result.returncode)
