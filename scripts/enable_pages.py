"""Enable GitHub Pages workflow publishing for this standalone repository."""

import json
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def credential() -> str:
    result = subprocess.run(["git", "credential", "fill"],
                            input="protocol=https\nhost=github.com\n\n",
                            text=True, capture_output=True, check=True)
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if not fields.get("password"):
        raise RuntimeError("No GitHub credential is available")
    return fields["password"]


def request(method: str, token: str, body: dict | None = None):
    url = "https://api.github.com/repos/Demigodd00/oracleguard/pages"
    payload = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=payload, method=method,
                  headers={"Authorization": f"Bearer {token}",
                           "Accept": "application/vnd.github+json",
                           "X-GitHub-Api-Version": "2022-11-28",
                           **({"Content-Type": "application/json"} if body else {})})
    try:
        with urlopen(req, timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read().decode())


def main() -> None:
    token = credential()
    status, data = request("GET", token)
    if status == 404:
        status, data = request("POST", token, {"build_type": "workflow"})
    if status not in {200, 201}:
        raise RuntimeError(f"GitHub Pages API returned {status}: {data.get('message', 'unknown error')}")
    print(json.dumps({"status": status, "url": data.get("html_url"),
                      "build_type": data.get("build_type")}))


if __name__ == "__main__":
    main()
