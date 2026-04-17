import { motion } from "framer-motion";

const scenarios = [
  {
    name: "Redis Down",
    what: "API still accepts (writes to PostgreSQL + outbox)",
    result: "Jobs delayed, NOT lost — automatic recovery",
    color: "yellow",
  },
  {
    name: "PostgreSQL Down",
    what: "API returns 503, K8s routes to other pods",
    result: "Graceful degradation — no data loss",
    color: "orange",
  },
  {
    name: "Outbox Relay Crashes",
    what: "Entries stay pending, next relay picks up",
    result: "No duplicates — idempotent by design",
    color: "purple",
  },
  {
    name: "Network Partition",
    what: "SIGTERM can't reach, K8s sends SIGKILL",
    result: "Zombie Sweeper recovers within 15 minutes",
    color: "red",
  },
  {
    name: "OOMKill (SIGKILL)",
    what: "Graceful handler NEVER runs, job stuck",
    result: "Two mechanisms: 10m fail / 15m requeue",
    color: "red",
  },
];

export default function Slide16_FailureScenarios() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-red-900/20 via-black to-gray-900" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-red-400 font-mono text-sm mb-2">
          SCENE 9: FAILURE SCENARIOS
        </div>
        <h2 className="text-4xl font-bold text-white">
          Every System Fails — How We Handle It
        </h2>
      </div>

      <div className="relative z-10 px-8 py-4 min-h-[calc(100vh-180px)]">
        <div className="grid grid-cols-2 gap-4 max-w-5xl mx-auto">
          {scenarios.map((scenario, i) => (
            <motion.div
              key={scenario.name}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`bg-gray-900/80 border border-${scenario.color}-500/30 rounded-xl p-5`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold text-white">
                  {scenario.name}
                </h3>
                <div
                  className={`w-3 h-3 rounded-full bg-${scenario.color}-500`}
                />
              </div>
              <div className="text-sm text-gray-400 mb-2">What happens:</div>
              <div className="text-sm text-gray-300 mb-3">{scenario.what}</div>
              <div className="text-sm text-gray-400 mb-1">Result:</div>
              <div className={`text-sm font-mono text-${scenario.color}-400`}>
                {scenario.result}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800 px-8 py-4"
      >
        <div className="text-center text-gray-400">
          <span className="text-cyan-400 font-mono">Honest claim: </span>
          <span>
            "All work is eventually accounted for — completed, requeued, or
            swept."
          </span>
        </div>
      </motion.div>
    </div>
  );
}
