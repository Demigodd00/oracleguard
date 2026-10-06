import { useCallback, useEffect, useState } from "react";
import { Activity, ArrowDownRight, ArrowRight, Check, ChevronRight, CircleAlert, Clock3, ExternalLink, FileLock2, Fingerprint, LockKeyhole, Radio, RefreshCw, Shield, ShieldAlert, Wallet, X } from "lucide-react";
import {
  configured, connect, contractAddress, explorerTx, loadSnapshot, pendingTransaction, resumePending, scenarioKind, scenarioSwitchAvailable, submit,
  type Address, type Assessment, type Gate, type Policy, type Provider, type Snapshot,
} from "./chain";

const previewPolicy: Policy = {
  version: "1.1.0", owner: "—", pair: "ETH-USD",
  feed_url: "https://feed.example.org/eth-usd.json",
  reference_a_url: "https://reference-a.example.net/eth-usd.json",
  reference_b_url: "https://reference-b.example.com/eth-usd.json",
  max_age_seconds: "600", max_reference_spread_bps: "200",
  trigger_deviation_bps: "1000", max_pause_seconds: "1800",
};
const previewGate: Gate = {
  closed: false, suspended_until: "0", borrow_count: "0",
  assessment_count: "0", checked_at: "0", funds_held: false,
};

function short(value: string): string {
  return value.length > 22 ? `${value.slice(0, 10)}…${value.slice(-8)}` : value;
}
function hostname(url: string): string {
  try { return new URL(url).hostname; } catch { return url; }
}
function date(unix: number | string): string {
  const n = Number(unix);
  return n > 0 ? new Date(n * 1000).toLocaleString() : "—";
}
function price(value: number): string {
  return value > 0 ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(value / 1e8) : "—";
}
function reason(value: string): string {
  const labels: Record<string, string> = {
    PRICE_DEVIATION: "Feed differs from references", FEED_STALE: "Feed update is stale",
    WITHIN_POLICY: "Prices are within policy", REFERENCES_CONFLICT: "References conflict",
    REFERENCE_STALE: "Reference data is stale", SOURCE_INVALID: "Source unavailable or invalid",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}

export default function App() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [account, setAccount] = useState<Address | null>(null);
  const [provider, setProvider] = useState<Provider | null>(null);
  const [loading, setLoading] = useState(configured);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [hash, setHash] = useState("");
  const [pendingHash, setPendingHash] = useState(() => configured ? pendingTransaction() : "");
  const [duration, setDuration] = useState("900");
  const [note, setNote] = useState("");
  const [borrowUnits, setBorrowUnits] = useState("10");

  const refresh = useCallback(async () => {
    if (!configured) return;
    setLoading(true);
    try { setSnapshot(await loadSnapshot()); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  const wallet = useCallback(async () => {
    const session = await connect();
    setAccount(session.account);
    setProvider(session.provider);
    return session;
  }, []);

  const action = async (method: string, args: unknown[]) => {
    if (busy || !configured || !snapshot || pendingHash) return;
    setBusy(true); setError(""); setHash("");
    try {
      const session = account && provider ? { account, provider } : await wallet();
      await submit(session.account, session.provider, method, args, (message, tx) => {
        setNotice(message); if (tx) { setHash(tx); setPendingHash(tx); }
      });
      setPendingHash("");
      await refresh();
      if (method === "open_assessment") setNote("");
    } catch (e) {
      setPendingHash(pendingTransaction());
      setError(e instanceof Error ? e.message : String(e));
      setNotice("");
    } finally { setBusy(false); }
  };

  const retryFinality = async () => {
    setBusy(true); setError(""); setNotice("Checking validator finality");
    try { await resumePending(); setPendingHash(""); setNotice("Finalized by GenLayer validators"); await refresh(); }
    catch (e) { setPendingHash(pendingTransaction()); setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  const policy = snapshot?.policy ?? previewPolicy;
  const gate = snapshot?.gate ?? previewGate;
  const incidents = snapshot?.assessments ?? [];
  const status = configured && !snapshot ? "Loading" : gate.closed ? "Protected" : "Operational";
  const pauseMinutes = Number(policy.max_pause_seconds) / 60;

  return <div className="app">
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><Shield size={19} strokeWidth={2.5} /></div><span>ORACLE<span className="brand-light">GUARD</span></span></div>
      <div className="topbar-right">
        {scenarioSwitchAvailable && <nav className="scenario-nav" aria-label="Review scenarios"><a className={scenarioKind === "healthy" ? "selected" : ""} href="./">LIVE</a><a className={scenarioKind === "stale" ? "selected" : ""} href="?scenario=stale">STALE</a><a className={scenarioKind === "invalid" ? "selected" : ""} href="?scenario=invalid">MISSING</a></nav>}
        <span className="network"><span className="network-dot" /> {configured ? "GENLAYER STUDIONET" : "PREVIEW MODE"}</span>
        <button className="wallet-button" onClick={() => void wallet().catch(e => setError(String(e)))} disabled={!configured || busy}>
          <Wallet size={15} /> {account ? short(account) : "Connect wallet"}
        </button>
      </div>
    </header>

    <main>
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> FEED INTEGRITY PROTOCOL <span className="version">v1.1</span></div>
          <h1>When a price feed breaks, <em>borrowing waits.</em></h1>
          <p>OracleGuard lets GenLayer validators compare a protected feed with two independent references. A confirmed incident closes one borrowing gate for a bounded period. Unclear evidence grants no authority.</p>
          <div className="hero-actions"><a href="#console" className="primary-link">Open console <ArrowRight size={16} /></a><a href="#how" className="text-link">How it works <ArrowDownRight size={16} /></a></div>
        </div>
        <div className={`hero-status ${gate.closed ? "is-closed" : ""}`}>
          <div className="status-top"><span>PROTECTED ACTION</span><span className="live-pill"><span /> {configured && snapshot ? "LIVE GATE" : "PREVIEW"}</span></div>
          <div className="status-icon">{gate.closed ? <LockKeyhole size={35} /> : <Activity size={35} />}</div>
          <div className="status-kicker">BORROW ADMISSION</div>
          <div className="status-word">{status}</div>
          <p>{configured && !snapshot ? "Waiting for finalized gate state from StudioNet." : gate.closed ? `Borrow requests are blocked until ${date(gate.suspended_until)}.` : "Borrow requests are currently accepted by the demonstration contract."}</p>
          <div className="status-bottom"><span><span className="tiny-dot" /> {gate.closed ? "TEMPORARY HOLD" : "GATE OPEN"}</span><span>{policy.pair}</span></div>
        </div>
      </section>

      {!configured && <div className="setup-banner"><CircleAlert size={18} /><div><strong>Preview mode</strong><span>Deploy the contract and set <code>VITE_ORACLEGUARD_ADDRESS</code> to activate the live console. The policy shown here is illustrative.</span></div></div>}
      {configured && scenarioKind === "stale" && <div className="setup-banner"><CircleAlert size={18} /><div><strong>Synthetic stale-feed fixture</strong><span>This charter uses a commit-pinned test response to demonstrate a stale-feed trigger. It does not represent a real oracle incident.</span></div></div>}
      {configured && scenarioKind === "invalid" && <div className="setup-banner"><CircleAlert size={18} /><div><strong>Missing reference fixture</strong><span>One commit-pinned reference URL deliberately returns HTTP 404. This checks that unavailable evidence cannot close the gate.</span></div></div>}

      <section className="metrics" aria-label="Protocol metrics">
        <div className="metric"><span>PROTECTED MARKET</span><strong>{policy.pair}</strong><small>One asset pair, one gate</small></div>
        <div className="metric"><span>DEVIATION TRIGGER</span><strong>{(Number(policy.trigger_deviation_bps) / 100).toFixed(0)}%</strong><small>Versus reference midpoint</small></div>
        <div className="metric"><span>MAXIMUM HOLD</span><strong>{pauseMinutes} min</strong><small>Expires automatically</small></div>
        <div className="metric"><span>ASSESSMENTS</span><strong>{gate.assessment_count}</strong><small>{gate.borrow_count} borrow admissions</small></div>
      </section>

      <section className="console-grid" id="console">
        <div className="panel policy-panel">
          <div className="panel-heading"><div><span className="section-label">01 / IMMUTABLE CHARTER</span><h2>Evidence policy</h2></div><FileLock2 size={20} /></div>
          <p className="panel-intro">These sources and thresholds were fixed when the contract was deployed. No account can change them or manually close the gate.</p>
          <div className="source-list">
            <Source role="PROTECTED FEED" label="Primary price input" url={policy.feed_url} number="01" />
            <Source role="REFERENCE A" label="Independent market source" url={policy.reference_a_url} number="02" />
            <Source role="REFERENCE B" label="Independent market source" url={policy.reference_b_url} number="03" />
          </div>
          <div className="rule-grid">
            <div><span>MAX SAMPLE AGE</span><strong>{policy.max_age_seconds}s</strong></div>
            <div><span>REF. SPREAD LIMIT</span><strong>{(Number(policy.max_reference_spread_bps) / 100).toFixed(1)}%</strong></div>
          </div>
          {configured && <a className="contract-link" href={`https://explorer-studio.genlayer.com/address/${contractAddress}`} target="_blank" rel="noreferrer">View contract {short(contractAddress)} <ExternalLink size={14} /></a>}
        </div>

        <div className="panel action-panel">
          <div className="panel-heading"><div><span className="section-label">02 / INCIDENT WORKFLOW</span><h2>Open assessment</h2></div><Radio size={20} /></div>
          <p className="panel-intro">First commit the request. Once it finalizes, validators fetch the charter’s exact URLs and evaluate the evidence.</p>
          <label className="field-label" htmlFor="note">INCIDENT NOTE</label>
          <textarea id="note" maxLength={280} value={note} onChange={e => setNote(e.target.value)} placeholder="Describe the suspected feed issue…" disabled={!configured || !snapshot || busy || !!pendingHash} />
          <div className="input-row"><div><label className="field-label" htmlFor="duration">REQUESTED HOLD</label><div className="number-input"><input id="duration" type="number" min="60" max={policy.max_pause_seconds} step="60" value={duration} onChange={e => setDuration(e.target.value)} disabled={!configured || !snapshot || busy || !!pendingHash} /><span>seconds</span></div></div><div className="duration-hint">Maximum<br/><strong>{pauseMinutes} minutes</strong></div></div>
          <button className="action-button" disabled={!configured || !snapshot || busy || !!pendingHash || !note.trim() || Number(duration) < 60 || Number(duration) > Number(policy.max_pause_seconds)} onClick={() => void action("open_assessment", [Number(duration), note])}>Open assessment <ArrowRight size={17} /></button>
          <div className="action-divider"><span>PROTECTED ACTION DEMO</span></div>
          <div className="borrow-row"><div className="number-input"><input aria-label="Borrow units" type="number" min="1" max="1000" value={borrowUnits} onChange={e => setBorrowUnits(e.target.value)} disabled={!configured || !snapshot || busy || !!pendingHash} /><span>units</span></div><button className="secondary-button" disabled={!configured || !snapshot || busy || !!pendingHash || gate.closed || Number(borrowUnits) < 1 || Number(borrowUnits) > 1000} onClick={() => void action("request_borrow", [Number(borrowUnits)])}>Test borrow <ChevronRight size={16} /></button></div>
          <p className="microcopy">Demo admission counter only. No loan is issued and no user funds are held.</p>
        </div>
      </section>

      {(notice || error) && <div className={`feedback ${error ? "feedback-error" : ""}`}><div>{error ? <X size={18} /> : <RefreshCw size={18} className={busy ? "spin" : ""} />}<span>{error || notice}</span></div>{hash && <a href={explorerTx(hash)} target="_blank" rel="noreferrer">View transaction <ExternalLink size={14} /></a>}</div>}
      {pendingHash && <div className="feedback"><div><Clock3 size={18} /><span>A submitted transaction is awaiting a finality check. New actions are held to prevent duplicates.</span></div><button className="refresh-button" disabled={busy} onClick={() => void retryFinality()}>Check finality</button><a href={explorerTx(pendingHash)} target="_blank" rel="noreferrer">View transaction <ExternalLink size={14} /></a></div>}

      <section className="incidents">
        <div className="section-header"><div><span className="section-label">03 / CONSENSUS RECORD</span><h2>Assessment history</h2><p>Only finalized decisions are shown in the live console.</p></div><button className="refresh-button" onClick={() => void refresh()} disabled={!configured || loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button></div>
        <div className="incident-table">
          <div className="table-head"><span>INCIDENT</span><span>DECISION</span><span>EVIDENCE</span><span>OPENED</span><span>ACTION</span></div>
          {incidents.length === 0 ? <div className="empty-state"><Fingerprint size={27} /><strong>No assessments yet</strong><span>{configured ? "Open an assessment to create the first immutable record." : "Assessment records appear here after deployment."}</span></div> : incidents.map(item => <Incident key={item.id} item={item} disabled={busy || !!pendingHash} onEvaluate={() => void action("evaluate_assessment", [item.id])} />)}
        </div>
      </section>

      <section className="how" id="how"><div className="how-title"><span className="section-label">SYSTEM DESIGN</span><h2>Authority follows evidence.</h2><p>Every step narrows what the system is allowed to do.</p></div><div className="how-steps"><div><span className="step-icon"><FileLock2 size={22} /></span><span className="step-number">01</span><h3>Fix the charter</h3><p>Pair, source URLs, thresholds and maximum hold are immutable at deployment.</p></div><div><span className="step-icon"><Fingerprint size={22} /></span><span className="step-number">02</span><h3>Record the request</h3><p>An incident’s duration and reason are written before anyone evaluates live data.</p></div><div><span className="step-icon"><ShieldAlert size={22} /></span><span className="step-number">03</span><h3>Reach consensus</h3><p>Validators fetch independently. Missing or conflicting evidence cannot close the gate.</p></div><div><span className="step-icon"><Clock3 size={22} /></span><span className="step-number">04</span><h3>Expire the hold</h3><p>A confirmed hold affects only borrow admission and ends without an administrator.</p></div></div></section>
    </main>

    <footer><div className="brand footer-brand"><div className="brand-mark"><Shield size={17} /></div><span>ORACLE<span className="brand-light">GUARD</span></span></div><span>Validator-governed circuit control on GenLayer.</span><a href="https://docs.genlayer.com/" target="_blank" rel="noreferrer">GenLayer docs <ExternalLink size={13} /></a></footer>
  </div>;
}

function Source({ role, label, url, number }: { role: string; label: string; url: string; number: string }) {
  return <div className="source"><div className="source-index">{number}</div><div><span>{role}</span><strong>{label}</strong><small>{hostname(url)}</small></div><a href={url} target="_blank" rel="noreferrer" aria-label={`Open ${role}`}><ExternalLink size={15} /></a></div>;
}

function Incident({ item, disabled, onEvaluate }: { item: Assessment; disabled: boolean; onEvaluate: () => void }) {
  const confirmed = item.status === "TRIGGER_CONFIRMED";
  return <div className="incident-entry"><div className="incident-row"><div className="incident-id"><strong>#{String(item.id).padStart(3, "0")}</strong><small>{item.note}</small></div><div><span className={`decision decision-${item.status.toLowerCase()}`}>{confirmed ? <LockKeyhole size={13} /> : item.status === "NO_TRIGGER" ? <Check size={13} /> : <CircleAlert size={13} />}{item.status.replaceAll("_", " ")}</span></div><div className="evidence-cell"><strong>{item.status === "OPEN" ? "Awaiting validators" : reason(item.reason)}</strong><small>{item.reference_mid_e8 ? `${price(item.feed_price_e8)} / ${price(item.reference_mid_e8)} ref.` : "—"}</small></div><div className="date-cell">{date(item.opened_at)}</div><div>{item.status === "OPEN" ? <button className="evaluate-button" disabled={disabled} onClick={onEvaluate}>Evaluate <ArrowRight size={14} /></button> : <span className="recorded">{confirmed ? `Until ${date(item.pause_until)}` : "Recorded"}</span>}</div></div>{item.samples && Object.keys(item.samples).length > 0 && <details className="evidence-details"><summary>Inspect recorded source responses</summary><div className="evidence-grid">{Object.entries(item.samples).map(([role, sample]) => <div key={role}><strong>{role.replaceAll("_", " ")}</strong><a href={sample.url} target="_blank" rel="noreferrer">{hostname(sample.url)} <ExternalLink size={12} /></a><span>HTTP {sample.http_status} · {sample.ok ? price(sample.price_e8) : sample.reason} · {date(sample.observed_at)}</span><code>SHA-256: {sample.sha256 || "—"}</code><pre>{sample.raw_body || "No response body recorded"}</pre></div>)}</div></details>}</div>;
}
