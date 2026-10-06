"""Deploy OracleGuard to StudioNet with three real, independent JSON sources.

The signer is disposable because the deployed charter is immutable and has no
owner-only methods. This script never writes the private key to disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from eth_account import Account
from eth_utils import to_checksum_address
from genlayer_py import create_client
from genlayer_py.assertions import tx_execution_succeeded
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "contracts" / "OracleGuard.py"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", default="ETH-USD")
    parser.add_argument("--feed-url", required=True)
    parser.add_argument("--reference-a-url", required=True)
    parser.add_argument("--reference-b-url", required=True)
    parser.add_argument("--max-age-seconds", type=int, default=600)
    parser.add_argument("--max-reference-spread-bps", type=int, default=200)
    parser.add_argument("--trigger-deviation-bps", type=int, default=1000)
    parser.add_argument("--max-pause-seconds", type=int, default=1800)
    parser.add_argument("--record", default="studionet.json", help="Filename under deployments/")
    return parser.parse_args()


def validate_urls(urls: list[str]) -> None:
    hosts = []
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise SystemExit("All sources must be public HTTPS URLs without credentials")
        if "." not in parsed.hostname or parsed.hostname.endswith(".local"):
            raise SystemExit("All sources must have public DNS hostnames")
        if "example." in parsed.hostname:
            raise SystemExit("Replace illustrative example.* URLs with real sources")
        hosts.append(parsed.hostname.lower())
    if len(set(hosts)) != 3:
        raise SystemExit("The three sources need distinct hostnames")


def tx_hex(value: object) -> str:
    rendered = str(value)
    return rendered if rendered.startswith("0x") else "0x" + bytes(value).hex()


def main() -> None:
    options = arguments()
    if Path(options.record).name != options.record or not options.record.endswith(".json"):
        raise SystemExit("--record must be a .json filename")
    record_path = ROOT / "deployments" / options.record
    urls = [options.feed_url, options.reference_a_url, options.reference_b_url]
    validate_urls(urls)
    source = SOURCE.read_text(encoding="utf-8")
    signer = Account.create()
    client = create_client(chain=studionet, account=signer)
    args = [
        options.pair, *urls, options.max_age_seconds,
        options.max_reference_spread_bps, options.trigger_deviation_bps,
        options.max_pause_seconds,
    ]
    tx = client.deploy_contract(code=source, account=signer, args=args)
    hash_value = tx_hex(tx)
    print(json.dumps({"step": "deploy_submitted", "transaction": hash_value}), flush=True)
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=hash_value,
        status=TransactionStatus.FINALIZED,
        interval=5_000,
        retries=120,
        full_transaction=True,
    )
    if (receipt.get("status_name") or receipt.get("statusName")) != TransactionStatus.FINALIZED.value:
        raise RuntimeError("Deployment did not finalize")
    if not tx_execution_succeeded(receipt):
        raise RuntimeError("Deployment execution failed: " + json.dumps(receipt, default=str))
    address = None
    for field in ("tx_data_decoded", "data"):
        entry = receipt.get(field)
        if isinstance(entry, dict) and entry.get("contract_address"):
            address = to_checksum_address(str(entry["contract_address"]))
            break
    if address is None:
        raise RuntimeError("Finalized receipt has no contract address")
    policy = client.read_contract(
        address=address,
        function_name="get_policy",
        args=[],
        transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
    )
    if not isinstance(policy, dict) or policy.get("pair") != options.pair.upper():
        raise RuntimeError("Finalized policy readback failed")
    if [policy.get("feed_url"), policy.get("reference_a_url"), policy.get("reference_b_url")] != urls:
        raise RuntimeError("Finalized source readback differs from deployment request")
    record = {
        "network": "studionet",
        "deployed_at_utc": datetime.now(timezone.utc).isoformat(),
        "address": address,
        "deployment_transaction": hash_value,
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "policy": policy,
        "signer": signer.address,
        "note": "Immutable charter; signer private key discarded; no owner-only methods.",
    }
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"step": "finalized", "address": address, "record": str(record_path)}))


if __name__ == "__main__":
    main()
