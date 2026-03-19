/**
 * Minimal echo agent — the simplest possible AgentAnycast server.
 *
 * Run:
 *   npm install agentanycast
 *   npx tsx server.ts
 */

import { Node } from "agentanycast";

const node = new Node({
  card: {
    name: "Echo Agent",
    description: "Echoes back any message it receives.",
    skills: [{ id: "echo", description: "Echo the input" }],
  },
});

await node.start();

console.log(`Echo Agent started!`);
console.log(`  PeerID:  ${node.peerId}`);
console.log(`  Skills:  [echo]`);
console.log(`\nWaiting for tasks... (Ctrl+C to stop)\n`);

node.onTask(async (task) => {
  const text = task.messages.at(-1)?.parts[0]?.text ?? "";
  console.log(`  Received: ${JSON.stringify(text)}`);
  await task.complete([{ parts: [{ text: `Echo: ${text}` }] }]);
  console.log(`  Replied:  "Echo: ${text}"`);
});

await node.serveForever();
