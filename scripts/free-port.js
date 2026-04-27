#!/usr/bin/env node
/**
 * Free a TCP port on Windows by killing owning PIDs.
 * Safe no-op when port is already free.
 */
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { execSync } = require("child_process");

const port = process.argv[2];
if (!port || !/^\d+$/.test(port)) {
  console.error("Usage: node scripts/free-port.js <port>");
  process.exit(1);
}

function getPidsOnPort(targetPort) {
  try {
    const out = execSync(`netstat -ano -p tcp | findstr :${targetPort}`, {
      stdio: ["ignore", "pipe", "ignore"],
      encoding: "utf8",
    });
    const pids = new Set();
    for (const line of out.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const parts = trimmed.split(/\s+/);
      const pid = parts[parts.length - 1];
      if (/^\d+$/.test(pid)) pids.add(pid);
    }
    return [...pids];
  } catch {
    return [];
  }
}

const pids = getPidsOnPort(port);
if (pids.length === 0) {
  console.log(`[free-port] Port ${port} is already free.`);
  process.exit(0);
}

for (const pid of pids) {
  try {
    execSync(`taskkill /PID ${pid} /F`, { stdio: "ignore" });
    console.log(`[free-port] Killed PID ${pid} on port ${port}.`);
  } catch {
    // Ignore failures; next start command will show if port still occupied.
  }
}

const remaining = getPidsOnPort(port);
if (remaining.length > 0) {
  console.warn(`[free-port] Warning: port ${port} still in use by PID(s): ${remaining.join(", ")}`);
} else {
  console.log(`[free-port] Port ${port} is now free.`);
}
