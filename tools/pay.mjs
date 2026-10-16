// Payable write for Objection. `genlayer write` always sends a value of 0, so
// bonds go through genlayer-js directly, borrowed from the installed CLI.
//
//   GENLAYER_KEYSTORE_PASSWORD=... node tools/pay.mjs <account> <address> \
//       <method> <valueWei> '<json args array>'
//
// <account> is a keystore name from `genlayer account list`. The keystore is
// decrypted in memory only. Use a throwaway testnet account.
import { createRequire } from "module";
import { execSync } from "child_process";
import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const cliDir = process.env.GENLAYER_CLI_DIR ||
  join(execSync("npm root -g").toString().trim(), "genlayer");
const require = createRequire(join(cliDir, "package.json"));
const { ethers } = require("ethers");
const gl = require("genlayer-js");
const { testnetBradbury } = require("genlayer-js/chains");

const [account, address, method, valueWei, argsJson = "[]"] = process.argv.slice(2);
const password = process.env.GENLAYER_KEYSTORE_PASSWORD;
if (!password) throw new Error("set GENLAYER_KEYSTORE_PASSWORD");
const keystore = readFileSync(
  join(homedir(), ".genlayer", "keystores", account + ".json"), "utf-8");
const wallet = await ethers.Wallet.fromEncryptedJson(keystore, password);
const client = gl.createClient({
  chain: testnetBradbury, account: gl.createAccount(wallet.privateKey) });

// Bradbury's consensus contract intermittently reverts the submission itself,
// before anything executes. Nothing ran, so resubmitting is safe.
let hash;
for (let attempt = 1; ; attempt++) {
  try {
    hash = await client.writeContract({
      address, functionName: method, args: JSON.parse(argsJson),
      value: BigInt(valueWei) });
    break;
  } catch (err) {
    if (attempt >= 5 || !String(err.message).includes("was reverted")) throw err;
    console.log("submission reverted, retry", attempt);
    await new Promise(r => setTimeout(r, 15000));
  }
}
console.log("tx", hash);
const receipt = await client.waitForTransactionReceipt({
  hash, status: "ACCEPTED", interval: 5000, retries: 120 });
console.log(receipt.status_name, receipt.txExecutionResultName);
