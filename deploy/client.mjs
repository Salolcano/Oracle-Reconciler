import { createClient, createAccount } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { readFileSync } from "node:fs";

const config = JSON.parse(readFileSync(new URL("./config.json", import.meta.url)));

// Studio Next: same shape as studionet, different chain id + RPC.
export const studioNext = {
  ...studionet,
  id: config.chainId,
  name: "Studio Next",
  rpcUrls: { default: { http: [config.rpc] } },
};

export function makeClient(privateKey) {
  const account = createAccount(privateKey);
  const client = createClient({ chain: studioNext, endpoint: config.rpc, account });
  return { client, account, config };
}
