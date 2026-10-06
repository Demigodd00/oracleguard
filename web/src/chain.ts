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
  max_reference_spread_bps: string; trigger_deviation_bps: string; max_pause_seconds: string;
}
export interface Gate {
  closed: boolean; suspended_until: string; borrow_count: string;
  assessment_count: string; checked_at: string; funds_held: boolean;
}
export interface Assessment {
  id: number; status: string; reason: string; requester: string; pair: string;
  feed_url: string; reference_a_url: string; reference_b_url: string;
  duration_seconds: number; note: string; opened_at: number; assessed_at: number;
  pause_until: number; feed_price_e8: number; reference_mid_e8: number; deviation_bps: number;
}
export interface Snapshot { policy: Policy; gate: Gate; assessments: Assessment[] }

export const contractAddress = import.meta.env.VITE_ORACLEGUARD_ADDRESS?.trim() ?? "";
export const configured = /^0x[0-9a-fA-F]{40}$/.test(contractAddress) && !/^0x0{40}$/i.test(contractAddress);
const reader = createClient({ chain: chains.studionet });

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
  onProgress("Submitted. Waiting for validator finality", hash);
  const receipt = await reader.waitForTransactionReceipt({
    hash: hash as never, status: TransactionStatus.FINALIZED, retries: 120,
  });
  const raw = receipt as Record<string, unknown>;
  const consensus = (raw.consensus_data ?? raw.consensusData ?? {}) as Record<string, unknown>;
  const leaders = consensus.leader_receipt ?? consensus.leaderReceipt;
  const leader = (Array.isArray(leaders) ? leaders[0] : leaders ?? {}) as Record<string, unknown>;
  const execution = leader.execution_result ?? leader.executionResult;
  const genvm = (leader.genvm_result ?? leader.genvmResult ?? {}) as Record<string, unknown>;
  const result = (leader.result ?? {}) as Record<string, unknown>;
  const explicitFailure = Boolean(raw.error || genvm.error_code || genvm.error_description)
    || result.status === "rollback" || result.status === "error";
  const successful = !explicitFailure && (execution === "SUCCESS"
    || (execution === undefined && raw.txExecutionResultName === "FINISHED_WITH_RETURN"));
  if (!successful) {
    throw new Error(String(genvm.error_description ?? raw.error ?? "Transaction finalized without successful execution."));
  }
  onProgress("Finalized by GenLayer validators", hash);
  return hash;
}

export function explorerTx(hash: string): string {
  return `https://explorer-studio.genlayer.com/tx/${hash}`;
}
