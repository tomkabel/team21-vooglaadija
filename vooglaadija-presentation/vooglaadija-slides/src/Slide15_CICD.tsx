import { motion } from "framer-motion";

const stages = [
  { name: "Lint", tool: "ruff", time: "2 min", icon: "✓" },
  { name: "Types", tool: "mypy", time: "5 min", icon: "✓" },
  {
    name: "Unit",
    tool: "pytest + Testcontainers",
    time: "15 min",
    icon: "✓",
    note: "PostgreSQL (NOT SQLite!)",
  },
  {
    name: "Integration",
    tool: "pytest + PG + Redis",
    time: "20 min",
    icon: "✓",
  },
  { name: "Security", tool: "bandit + safety", time: "10 min", icon: "✓" },
  { name: "Build", tool: "multi-stage Dockerfile", time: "15 min", icon: "✓" },
  { name: "Publish", tool: "GHCR", time: "5 min", icon: "✓" },
];

export default function Slide15_CICD() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-black to-gray-900" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          SCENE 8: CI/CD PIPELINE
        </div>
        <h2 className="text-4xl font-bold text-white">Professional DevOps</h2>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-200px)] px-8">
        <div className="max-w-4xl w-full">
          {/* Pipeline visualization */}
          <div className="flex items-center justify-between mb-8">
            {stages.map((stage, i) => (
              <motion.div
                key={stage.name}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex flex-col items-center"
              >
                <div
                  className={`w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold border-2 ${
                    stage.name === "Unit"
                      ? "bg-yellow-500/20 border-yellow-500 text-yellow-400"
                      : "bg-green-500/20 border-green-500 text-green-400"
                  }`}
                >
                  {stage.icon}
                </div>
                <div className="mt-2 text-center">
                  <div className="font-bold text-white">{stage.name}</div>
                  <div className="text-xs text-gray-500">{stage.time}</div>
                </div>
                {i < stages.length - 1 && (
                  <div
                    className="absolute h-0.5 bg-gradient-to-r from-green-500 to-cyan-500"
                    style={{
                      left: `${(i + 0.5) * (100 / stages.length)}%`,
                      width: `${100 / stages.length}%`,
                      top: "3rem",
                    }}
                  />
                )}
              </motion.div>
            ))}
          </div>

          {/* Key points */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="bg-gray-900/80 border border-purple-500/30 rounded-xl p-6"
          >
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <div className="text-red-400 font-bold mb-2">
                  ⚠ Why NOT SQLite?
                </div>
                <p className="text-sm text-gray-400">
                  SQLite does NOT support{" "}
                  <span className="text-cyan-400 font-mono">
                    FOR UPDATE SKIP LOCKED
                  </span>{" "}
                  — the most critical distributed systems logic would be
                  UNTESTED.
                </p>
              </div>
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <div className="text-green-400 font-bold mb-2">
                  ✓ Testcontainers Solution
                </div>
                <p className="text-sm text-gray-400">
                  Ephemeral PostgreSQL per test suite — 100% fidelity to
                  production behavior.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 border-t border-gray-800 px-8 py-3">
        <div className="flex justify-center gap-8 text-sm">
          <span className="text-gray-400">Total: ~58 min</span>
          <span className="text-green-400">Parallelized: ~25 min</span>
          <span className="text-cyan-400">100+ tests</span>
        </div>
      </div>
    </div>
  );
}
