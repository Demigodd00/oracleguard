"""Record a resumable, finalized StudioNet assessment for one deployed charter."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from eth_account import Account
from genlayer_py import create_client
from genlayer_py.assertions import tx_execution_succeeded
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus


ROOT = Path(__file__).resolve().parents[1]


def save(path: Path, record: dict) -> None:
    record["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read(client, address: str, method: str, args: list | None = None):
    return client.read_contract(address=address, function_name=method, args=args or [],
                                transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)


def write_step(client, address: str, path: Path, record: dict, step: str,
               method: str, args: list) -> None:
    entry = record["transactions"].get(step)
    if entry is None:
        entry = {"method": method, "args": args, "state": "prepared"}
        record["transactions"][step] = entry
        save(path, record)
    if entry["method"] != method or entry["args"] != args:
        raise RuntimeError(f"{step}: transaction intent changed")
    if entry["state"] == "checked":
        return
    if entry["state"] == "broadcasting" and not entry.get("hash"):
        raise RuntimeError(f"{step}: broadcast outcome unknown; inspect wallet history before retrying")
    if not entry.get("hash"):
        signer = Account.create()
        entry["sender"] = signer.address
        entry["state"] = "broadcasting"
        save(path, record)
        tx = client.write_contract(address=address, function_name=method, args=args, account=signer)
        entry["hash"] = str(tx)
        entry["state"] = "submitted"
        save(path, record)
        print(json.dumps({"step": step, "state": "submitted", "transaction": entry["hash"]}), flush=True)
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=entry["hash"], status=TransactionStatus.FINALIZED,
        interval=5_000, retries=120, full_transaction=True,
    )
    entry["status"] = receipt.get("status_name") or receipt.get("statusName")
    entry["consensus_result"] = receipt.get("result_name") or receipt.get("resultName")
    entry["leader_execution_succeeded"] = tx_execution_succeeded(receipt)
    entry["state"] = "checked" if (entry["status"] == "FINALIZED" and
        entry["consensus_result"] in {"AGREE", "MAJORITY_AGREE"} and
        entry["leader_execution_succeeded"]) else "failed"
    save(path, record)
    if entry["state"] != "checked":
        raise RuntimeError(f"{step}: finalized transaction did not succeed: {entry}")
    print(json.dumps({"step": step, "state": "finalized", "transaction": entry["hash"]}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment", default="studionet.json")
    parser.add_argument("--scenario", choices=["healthy", "synthetic_stale", "invalid_reference"], required=True)
    args = parser.parse_args()
    deployment_path = ROOT / "deployments" / Path(args.deployment).name
    deployment = json.loads(deployment_path.read_text(encoding="utf-8"))
    address = deployment["address"]
    journal = ROOT / "deployments" / f"acceptance_{args.scenario}.json"
    client = create_client(chain=studionet, account=Account.create())
    if journal.exists():
        record = json.loads(journal.read_text(encoding="utf-8"))
        if record["contract"] != address:
            raise RuntimeError("Existing journal refers to another contract")
    else:
        gate = read(client, address, "get_gate")
        record = {"network": "studionet", "contract": address,
                  "scenario": args.scenario, "starting_assessment_count": int(gate["assessment_count"]),
                  "transactions": {}, "checks": {},
                  "fixture_disclosure": (
                      "The stale source is a public synthetic fixture, not a real oracle incident."
                      if args.scenario == "synthetic_stale" else
                      "A commit-pinned missing reference URL deliberately returns 404 to test fail-safe behavior."
                      if args.scenario == "invalid_reference" else
                      "Three live independent market APIs.")}
        save(journal, record)
    number = record["starting_assessment_count"] + 1
    note = f"Review {args.scenario}: independently inspect committed sources"
    write_step(client, address, journal, record, "open", "open_assessment", [900, note])
    opened = read(client, address, "get_assessment", [number])
    if opened["status"] != "OPEN" or opened["note"] != note:
        raise RuntimeError("Opened assessment readback differs from request")
    record["checks"]["open_readback"] = True
    save(journal, record)
    write_step(client, address, journal, record, "evaluate", "evaluate_assessment", [number])
    assessment = read(client, address, "get_assessment", [number])
    gate = read(client, address, "get_gate")
    expected = "TRIGGER_CONFIRMED" if args.scenario == "synthetic_stale" else (
        "INSUFFICIENT_EVIDENCE" if args.scenario == "invalid_reference" else "NO_TRIGGER")
    record["assessment"] = assessment
    record["gate_after"] = gate
    record["checks"]["expected_decision"] = assessment["status"] == expected
    record["checks"]["evidence_snapshots_present"] = all(
        assessment.get("samples", {}).get(role, {}).get("sha256")
        for role in ("feed", "reference_a", "reference_b")
        if args.scenario != "invalid_reference" or role != "reference_b")
    record["checks"]["gate_effect"] = (
        int(assessment["pause_until"]) > int(assessment["assessed_at"])
        if args.scenario == "synthetic_stale" else not gate["closed"])
    if args.scenario == "invalid_reference":
        record["checks"]["missing_reference_recorded"] = (
            assessment.get("samples", {}).get("reference_b", {}).get("http_status") == 404)
    save(journal, record)
    if not all(record["checks"].values()):
        raise RuntimeError("Acceptance check failed: " + json.dumps(record["checks"]))
    print(json.dumps({"scenario": args.scenario, "status": assessment["status"],
                      "reason": assessment["reason"], "journal": str(journal)}), flush=True)


if __name__ == "__main__":
    main()
