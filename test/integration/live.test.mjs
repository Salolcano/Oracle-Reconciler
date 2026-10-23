// Live test against Studio Next. Needs network + a funded key:
//   RUN_LIVE=1 PRIVATE_KEY=0x... node --test test/integration
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { TransactionStatus } from "genlayer-js/types";
import { makeClient } from "../../deploy/client.mjs";

const live = process.env.RUN_LIVE === "1";
const deployedPath = new URL("../../deploy/deployed.json", import.meta.url);

test("reconcile round reaches ACCEPTED and publishes a value", { skip: !live }, async () => {
  assert.ok(existsSync(deployedPath), "run deploy/deploy.mjs first");
  const { address, feed_id } = JSON.parse(readFileSync(deployedPath));
  const { client } = makeClient(process.env.PRIVATE_KEY);

  const hash = await client.writeContract({ address, functionName: "reconcile", args: [feed_id], value: 0n });
  await client.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED, retries: 200, interval: 3000 });

  const round = await client.readContract({ address, functionName: "get_round", args: [feed_id] });
  assert.ok(Number(round) >= 1);

  const latest = JSON.parse(await client.readContract({ address, functionName: "get_latest", args: [feed_id] }));
  assert.equal(latest.status, "OK");
  assert.ok(latest.agreeing.length >= 2);
  console.log("value (scaled):", latest.value, "outliers:", latest.outliers);
});
