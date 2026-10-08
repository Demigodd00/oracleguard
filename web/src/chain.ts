import { chains, createClient } from "genlayer-js";
import { TransactionHashVariant, TransactionStatus } from "genlayer-js/types";

export type Address = `0x${string}`;
export interface Provider {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>;
}
declare global { interface Window { ethereum?: Provider } }

export interface Policy {
  version: string; owner: string; pair: string; feed_url: string;
  reference_a_url: string; reference_b_url: string; max_age_seconds: string;
  max_reference_spread_bps: string; trigger_deviation_bps: string;
  min_pause_seconds: string; max_pause_seconds: string;
}
export interface Gate {
  closed: boolean; suspended_until: string; remaining_seconds: string; borrow_count: string;
  assessment_count: string; checked_at: string; funds_held: boolean;
}
export interface Assessment {
  id: number; status: string; reason: string; requester: string; pair: string;
  feed_url: string; reference_a_url: string; reference_b_url: string;
  duration_seconds: number; note: string; opened_at: number; assessed_at: number;
  pause_until: number; feed_price_e8: number; reference_mid_e8: number; deviation_bps: number;
  samples?: Record<string, { url: string; http_status: number; raw_body: string; sha256: string; ok: boolean; reason: string; price_e8: number; observed_at: number }>;
}
export interface Snapshot { policy: Policy; gate: Gate; assessments: Assessment[] }

const healthyAddress = import.meta.env.VITE_ORACLEGUARD_ADDRESS?.trim() ?? "";
const staleAddress = import.meta.env.VITE_ORACLEGUARD_STALE_ADDRESS?.trim() ?? "";
const invalidAddress = import.meta.env.VITE_ORACLEGUARD_INVALID_ADDRESS?.trim() ?? "";
const selectedScenario = new URLSearchParams(window.location.search).get("scenario");
export const scenarioKind = selectedScenario === "stale" || selectedScenario === "invalid" ? selectedScenario : "healthy";
export const contractAddress = scenarioKind === "stale" ? staleAddress : scenarioKind === "invalid" ? invalidAddress : healthyAddress;
export const scenarioSwitchAvailable = [healthyAddress, staleAddress, invalidAddress].every(value => /^0x[0-9a-fA-F]{40}$/.test(value));
export const configured = /^0x[0-9a-fA-F]{40}$/.test(contractAddress) && !/^0x0{40}$/i.test(contractAddress);
const reader = createClient({ chain: chains.studionet });
const pendingKey = `oracleguard:pending:${contractAddress.toLowerCase()}`;

export function pendingTransaction(): string { return localStorage.getItem(pendingKey) ?? ""; }

function assertFinalizedSuccess(receipt: Record<string, unknown>): void {
  const status = receipt.statusName ?? receipt.status_name;
  const result = receipt.resultName ?? receipt.result_name;
  const consensus = (receipt.consensusData ?? receipt.consensus_data ?? {}) as Record<string, unknown>;
  const leaders = consensus.leaderReceipt ?? consensus.leader_receipt;
  const leader = (Array.isArray(leaders) ? leaders[0] : leaders ?? {}) as Record<string, unknown>;
  const execution = receipt.txExecutionResultName ?? receipt.tx_execution_result_name ?? leader.executionResult ?? leader.execution_result;
  if (status !== "FINALIZED" || !["AGREE", "MAJORITY_AGREE"].includes(String(result)) || !["FINISHED_WITH_RETURN", "SUCCESS"].includes(String(execution))) {
    throw new Error(`Transaction finalized without successful consensus (status: ${String(status)}, decision: ${String(result)}, execution: ${String(execution)}).`);
  }
}

export async function resumePending(): Promise<string> {
  const hash = pendingTransaction();
  if (!hash) return "";
  const receipt = await reader.waitForTransactionReceipt({ hash: hash as never, status: TransactionStatus.FINALIZED, retries: 120 });
  localStorage.removeItem(pendingKey);
  assertFinalizedSuccess(receipt as Record<string, unknown>);
  return hash;
}

function address(): Address {
  if (!configured) throw new Error("Set VITE_ORACLEGUARD_ADDRESS to the deployed contract address.");
  return contractAddress as Address;
}

function validAccount(value: unknown): Address {
  const account = Array.isArray(value) ? value[0] : undefined;
  if (typeof account !== "string" || !/^0x[0-9a-fA-F]{40}$/.test(account)) throw new Error("Wallet returned no valid account.");
  return account as Address;
}

export async function connect(): Promise<{ account: Address; provider: Provider }> {
  const provider = window.ethereum;
  if (!provider) throw new Error("Install or open a browser wallet to submit transactions.");
  const account = validAccount(await provider.request({ method: "eth_requestAccounts" }));
  const chain = chains.studionet;
  const chainId = `0x${chain.id.toString(16)}`;
  if (BigInt(String(await provider.request({ method: "eth_chainId" }))) !== BigInt(chain.id)) {
    try {
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId }] });
    } catch (error) {
      const code = (error as { code?: number })?.code;
      if (code !== 4902) throw error;
      await provider.request({ method: "wallet_addEthereumChain", params: [{
        chainId, chainName: chain.name, rpcUrls: [...chain.rpcUrls.default.http],
        nativeCurrency: chain.nativeCurrency,
        ...(chain.blockExplorers?.default.url ? { blockExplorerUrls: [chain.blockExplorers.default.url] } : {}),
      }] });
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId }] });
    }
  }
  if (BigInt(String(await provider.request({ method: "eth_chainId" }))) !== BigInt(chain.id)) {
    throw new Error("Switch to StudioNet before continuing.");
  }
  return { account, provider };
}

async function read<T>(functionName: string, args: unknown[] = []): Promise<T> {
  return await reader.readContract({
    address: address(), functionName, args: args as never[],
    transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
  }) as T;
}

export async function loadSnapshot(): Promise<Snapshot> {
  const [policy, gate] = await Promise.all([read<Policy>("get_policy"), read<Gate>("get_gate")]);
  const total = Number(gate.assessment_count);
  const start = Math.max(0, total - 20);
  const page = await read<{ items: Assessment[] }>("list_assessments", [start, 20]);
  return { policy, gate, assessments: [...page.items].reverse() };
}

export async function submit(
  account: Address, provider: Provider, functionName: string, args: unknown[],
  onProgress: (message: string, hash?: string) => void,
): Promise<string> {
  const client = createClient({ chain: chains.studionet, account, provider: provider as never });
  onProgress("Waiting for wallet signature");
  const hash = String(await client.writeContract({ address: address(), functionName, args: args as never[], value: 0n }));
  localStorage.setItem(pendingKey, hash);
  onProgress("Submitted. Waiting for validator finality", hash);
  await resumePending();
  onProgress("Finalized by GenLayer validators", hash);
  return hash;
}

export function explorerTx(hash: string): string {
  return `https://explorer-studio.genlayer.com/tx/${hash}`;
}
