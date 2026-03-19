/**
 * Send a task to an echo agent.
 *
 * Run:
 *   npx tsx client.ts <PEER_ID> "Hello, world!"
 */

import { Node } from "agentanycast";

const [peerId, text] = process.argv.slice(2);
if (!peerId || !text) {
  console.error("Usage: npx tsx client.ts <PEER_ID> <MESSAGE>");
  process.exit(1);
}

const node = new Node({
  card: { name: "Client", skills: [] },
});
await node.start();

console.log(`Sending to ${peerId}: ${JSON.stringify(text)}`);

const handle = await node.sendTask(
  { role: "user", parts: [{ text }] },
  { peerId },
);
const result = await handle.wait(30_000);

const reply = result.artifacts[0]?.parts[0]?.text ?? "";
console.log(`Response: ${reply}`);

await node.stop();
