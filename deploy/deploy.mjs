// Usage: PRIVATE_KEY=0x... node deploy/deploy.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { generatePrivateKey } from "genlayer-js";
import { TransactionStatus } from "genlayer-js/types";
import { makeClient } from "./client.mjs";

const pk = process.env.PRIVATE_KEY || generatePrivateKey();
const { client, account, config } = makeClient(pk);
console.log("deployer:", account.address);

const code = readFileSync(new URL("../contracts/oracle_reconciler.py", import.meta.url), "utf8");

const deployHash = await client.deployContract({ code, args: [], leaderOnly: false });
const receipt = await client.waitForTransactionReceipt({
  hash: deployHash, status: TransactionStatus.ACCEPTED, retries: 120, interval: 3000,
});
const address = receipt?.data?.contract_address ?? receipt?.txDataDecoded?.contractAddress;
console.log("deployed at:", address);
console.log("explorer:", config.explorer);

const f = config.exampleFeed;
const regHash = await client.writeContract({
  address, functionName: "register_feed",
  args: [f.feed_id, JSON.stringify(f.sources), f.decimals, f.tolerance_bps, f.drift_bps, f.min_sources, f.min_agree],
  value: 0n,
});
await client.waitForTransactionReceipt({ hash: regHash, status: TransactionStatus.ACCEPTED, retries: 120, interval: 3000 });
console.log("registered feed:", f.feed_id);

writeFileSync(new URL("./deployed.json", import.meta.url), JSON.stringify({ address, feed_id: f.feed_id }, null, 2));
