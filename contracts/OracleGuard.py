# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from datetime import datetime
import hashlib
import json
import re


VERSION = "1.0.0"
MAX_BODY_BYTES = 4096
MAX_ASSESSMENTS_PAGE = 25
HTTPS_URL = re.compile(r"https://([a-z0-9][a-z0-9.-]*[a-z0-9])(/[A-Za-z0-9._~:/?&=%+-]*)?", re.I)


def _fail(code: str) -> None:
    raise gl.vm.UserError("[EXPECTED] " + code)


def _now() -> int:
    return int(datetime.fromisoformat(gl.message_raw["datetime"]).timestamp())


def _host(url: str) -> str:
    match = HTTPS_URL.fullmatch(url)
    if match is None or len(url) > 360 or ".." in match.group(1):
        _fail("invalid_https_url")
    host = match.group(1).lower()
    if "." not in host or host.endswith(".local") or re.fullmatch(r"[0-9.]+", host):
        _fail("public_host_required")
    return host


def _dump(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class OracleGuard(gl.Contract):
    owner: Address
    pair: str
    feed_url: str
    reference_a_url: str
    reference_b_url: str
    max_age_seconds: u256
    max_reference_spread_bps: u256
    trigger_deviation_bps: u256
    max_pause_seconds: u256
    assessment_count: u256
    borrow_count: u256
    suspended_until: u256
    assessments: TreeMap[str, str]
    borrowed_units: TreeMap[str, u256]

    def __init__(
        self,
        pair: str,
        feed_url: str,
        reference_a_url: str,
        reference_b_url: str,
        max_age_seconds: u256,
        max_reference_spread_bps: u256,
        trigger_deviation_bps: u256,
        max_pause_seconds: u256,
    ):
        clean_pair = pair.strip().upper()
        if re.fullmatch(r"[A-Z0-9]{2,12}-[A-Z0-9]{2,12}", clean_pair) is None:
            _fail("invalid_pair")
        hosts = [_host(feed_url), _host(reference_a_url), _host(reference_b_url)]
        if len(set(hosts)) != 3:
            _fail("independent_source_hosts_required")
        if not 60 <= int(max_age_seconds) <= 3600:
            _fail("max_age_out_of_bounds")
        if not 10 <= int(max_reference_spread_bps) <= 500:
            _fail("reference_spread_out_of_bounds")
        if not 500 <= int(trigger_deviation_bps) <= 5000:
            _fail("deviation_out_of_bounds")
        if int(trigger_deviation_bps) <= int(max_reference_spread_bps) * 2:
            _fail("deviation_must_exceed_reference_spread")
        if not 60 <= int(max_pause_seconds) <= 86400:
            _fail("pause_out_of_bounds")
        self.owner = gl.message.sender_address
        self.pair = clean_pair
        self.feed_url = feed_url
        self.reference_a_url = reference_a_url
        self.reference_b_url = reference_b_url
        self.max_age_seconds = max_age_seconds
        self.max_reference_spread_bps = max_reference_spread_bps
        self.trigger_deviation_bps = trigger_deviation_bps
        self.max_pause_seconds = max_pause_seconds
        self.assessment_count = u256(0)
        self.borrow_count = u256(0)
        self.suspended_until = u256(0)

    @gl.public.view
    def get_policy(self) -> dict:
        return {
            "version": VERSION,
            "owner": str(self.owner),
            "pair": self.pair,
            "feed_url": self.feed_url,
            "reference_a_url": self.reference_a_url,
            "reference_b_url": self.reference_b_url,
            "max_age_seconds": str(int(self.max_age_seconds)),
            "max_reference_spread_bps": str(int(self.max_reference_spread_bps)),
            "trigger_deviation_bps": str(int(self.trigger_deviation_bps)),
            "max_pause_seconds": str(int(self.max_pause_seconds)),
        }

    @gl.public.view
    def get_gate(self) -> dict:
        now = _now()
        return {
            "closed": now < int(self.suspended_until),
            "suspended_until": str(int(self.suspended_until)),
            "borrow_count": str(int(self.borrow_count)),
            "assessment_count": str(int(self.assessment_count)),
            "checked_at": str(now),
            "funds_held": False,
        }

    def _get_assessment(self, assessment_id: u256) -> dict:
        number = int(assessment_id)
        if number < 1 or number > int(self.assessment_count):
            _fail("assessment_missing")
        return json.loads(self.assessments[str(number)])

    @gl.public.view
    def get_assessment(self, assessment_id: u256) -> dict:
        return self._get_assessment(assessment_id)

    @gl.public.view
    def list_assessments(self, start: u256, limit: u256) -> dict:
        first = int(start)
        size = int(limit)
        total = int(self.assessment_count)
        if first < 0 or size < 1 or size > MAX_ASSESSMENTS_PAGE:
            _fail("invalid_page")
        items = []
        for number in range(first + 1, min(first + size, total) + 1):
            items.append(json.loads(self.assessments[str(number)]))
        return {"total": str(total), "items": items}

    @gl.public.write
    def open_assessment(self, duration_seconds: u256, note: str) -> u256:
        duration = int(duration_seconds)
        clean_note = note.strip()
        if duration < 60 or duration > int(self.max_pause_seconds):
            _fail("duration_out_of_bounds")
        if not clean_note or len(clean_note) > 280 or "\x00" in clean_note:
            _fail("invalid_note")
        number = int(self.assessment_count) + 1
        record = {
            "id": number,
            "status": "OPEN",
            "reason": "",
            "requester": str(gl.message.sender_address),
            "pair": self.pair,
            "feed_url": self.feed_url,
            "reference_a_url": self.reference_a_url,
            "reference_b_url": self.reference_b_url,
            "duration_seconds": duration,
            "note": clean_note,
            "opened_at": _now(),
            "assessed_at": 0,
            "pause_until": 0,
            "feed_price_e8": 0,
            "reference_mid_e8": 0,
            "deviation_bps": 0,
        }
        self.assessment_count = u256(number)
        self.assessments[str(number)] = _dump(record)
        return u256(number)

    def _sample(self, url: str, now: int) -> dict:
        try:
            response = gl.nondet.web.get(url)
        except Exception:
            return {"ok": False, "reason": "FETCH_FAILED"}
        if response.status != 200 or not response.body or len(response.body) > MAX_BODY_BYTES:
            return {"ok": False, "reason": "SOURCE_UNAVAILABLE"}
        try:
            body = json.loads(response.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {"ok": False, "reason": "INVALID_JSON"}
        if not isinstance(body, dict) or body.get("pair") != self.pair:
            return {"ok": False, "reason": "PAIR_MISMATCH"}
        price = body.get("price_e8")
        observed = body.get("observed_at")
        if type(price) is not int or type(observed) is not int or price <= 0 or price > 10**20:
            return {"ok": False, "reason": "INVALID_SAMPLE"}
        if observed > now + 30 or observed < now - 86400:
            return {"ok": False, "reason": "INVALID_TIMESTAMP"}
        return {
            "ok": True,
            "price": price,
            "observed_at": observed,
            "digest": hashlib.sha256(response.body).hexdigest(),
        }

    def _inspect(self, record: dict, now: int) -> dict:
        feed = self._sample(record["feed_url"], now)
        a = self._sample(record["reference_a_url"], now)
        b = self._sample(record["reference_b_url"], now)
        samples = (feed, a, b)
        if any(not item["ok"] for item in samples):
            return {"status": "INSUFFICIENT_EVIDENCE", "reason": "SOURCE_INVALID", "feed_price_e8": 0, "reference_mid_e8": 0, "deviation_bps": 0}
        max_age = int(self.max_age_seconds)
        if now - a["observed_at"] > max_age or now - b["observed_at"] > max_age:
            return {"status": "INSUFFICIENT_EVIDENCE", "reason": "REFERENCE_STALE", "feed_price_e8": feed["price"], "reference_mid_e8": 0, "deviation_bps": 0}
        mid = (a["price"] + b["price"]) // 2
        spread = abs(a["price"] - b["price"]) * 10000 // mid
        if spread > int(self.max_reference_spread_bps):
            return {"status": "INSUFFICIENT_EVIDENCE", "reason": "REFERENCES_CONFLICT", "feed_price_e8": feed["price"], "reference_mid_e8": mid, "deviation_bps": 0}
        deviation = abs(feed["price"] - mid) * 10000 // mid
        if now - feed["observed_at"] > max_age:
            status, reason = "TRIGGER_CONFIRMED", "FEED_STALE"
        elif deviation >= int(self.trigger_deviation_bps):
            status, reason = "TRIGGER_CONFIRMED", "PRICE_DEVIATION"
        else:
            status, reason = "NO_TRIGGER", "WITHIN_POLICY"
        return {"status": status, "reason": reason, "feed_price_e8": feed["price"], "reference_mid_e8": mid, "deviation_bps": deviation}

    @gl.public.write
    def evaluate_assessment(self, assessment_id: u256) -> str:
        record = self._get_assessment(assessment_id)
        if record["status"] != "OPEN":
            _fail("assessment_already_evaluated")
        now = _now()

        def inspect() -> dict:
            return self._inspect(record, now)

        def validate(leader: gl.vm.Result) -> bool:
            if not isinstance(leader, gl.vm.Return) or not isinstance(leader.calldata, dict):
                return False
            ours = inspect()
            theirs = leader.calldata
            if theirs.get("status") != ours["status"] or theirs.get("reason") != ours["reason"]:
                return False
            if ours["status"] == "INSUFFICIENT_EVIDENCE":
                return True
            for field in ("feed_price_e8", "reference_mid_e8"):
                value = theirs.get(field)
                reference = ours[field]
                if type(value) is not int or abs(value - reference) * 10000 > reference * 200:
                    return False
            return True

        result = gl.vm.run_nondet_unsafe(inspect, validate)
        record.update(result)
        record["assessed_at"] = now
        if result["status"] == "TRIGGER_CONFIRMED":
            until = now + record["duration_seconds"]
            if until > int(self.suspended_until):
                self.suspended_until = u256(until)
            record["pause_until"] = until
        self.assessments[str(int(assessment_id))] = _dump(record)
        return result["status"]

    @gl.public.write
    def request_borrow(self, units: u256) -> u256:
        amount = int(units)
        if amount < 1 or amount > 1000:
            _fail("units_out_of_bounds")
        if _now() < int(self.suspended_until):
            _fail("borrow_gate_closed")
        account = str(gl.message.sender_address).lower()
        previous = int(self.borrowed_units.get(account, u256(0)))
        self.borrowed_units[account] = u256(previous + amount)
        self.borrow_count = u256(int(self.borrow_count) + 1)
        return self.borrowed_units[account]

    @gl.public.view
    def get_borrowed_units(self, account: Address) -> str:
        return str(int(self.borrowed_units.get(str(account).lower(), u256(0))))
