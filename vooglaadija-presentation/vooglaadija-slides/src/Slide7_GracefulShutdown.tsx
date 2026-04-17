import { motion } from "framer-motion";

export default function Slide7_GracefulShutdown() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-orange-900/20 via-black to-black" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          GRACEFUL SHUTDOWN
        </div>
        <h2 className="text-4xl font-bold text-white">
          25-Second Grace Period with 5s Runway
        </h2>
        <p className="text-red-400 mt-2 font-mono">
          ⚠ Kubernetes SIGKILL fires at 30s — we timeout at 25s
        </p>
      </div>

      {/* Timeline */}
      <div className="relative z-10 px-8 py-4 min-h-[calc(100vh-200px)]">
        <div className="relative max-w-4xl mx-auto">
          {/* Timeline line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500 via-yellow-500 to-red-500" />

          {/* Phase 1 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            className="relative flex items-start gap-6 mb-8"
          >
            <div className="w-16 h-16 rounded-full bg-cyan-500/20 border-2 border-cyan-500 flex items-center justify-center text-cyan-400 font-bold text-xl z-10">
              1
            </div>
            <div className="flex-1 bg-gray-900/80 border border-cyan-500/30 rounded-xl p-4">
              <div className="flex items-center gap-4 mb-2">
                <span className="text-cyan-400 font-mono text-sm">t=0</span>
                <span className="text-white font-bold">
                  Break Redis Polling Loop
                </span>
              </div>
              <pre className="text-sm font-mono text-gray-400">{`self.is_polling = False  # ← CRITICAL`}</pre>
              <p className="text-xs text-gray-500 mt-2">
                K8s readiness probe does NOTHING for workers — they pull from
                Redis
              </p>
            </div>
          </motion.div>

          {/* Phase 2 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="relative flex items-start gap-6 mb-8"
          >
            <div className="w-16 h-16 rounded-full bg-yellow-500/20 border-2 border-yellow-500 flex items-center justify-center text-yellow-400 font-bold text-xl z-10">
              2
            </div>
            <div className="flex-1 bg-gray-900/80 border border-yellow-500/30 rounded-xl p-4">
              <div className="flex items-center gap-4 mb-2">
                <span className="text-yellow-400 font-mono text-sm">
                  t=0-25
                </span>
                <span className="text-white font-bold">
                  Wait for Job Completion (max 25s)
                </span>
              </div>
              <pre className="text-sm font-mono text-gray-400">{`await asyncio.wait_for(self._wait_for_job_completion(), timeout=25.0)`}</pre>
              <p className="text-xs text-yellow-500 mt-2">
                ⚠ K8s SIGKILL fires at 30s — we have 5s runway for requeue
              </p>
            </div>
          </motion.div>

          {/* Phase 3 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="relative flex items-start gap-6 mb-8"
          >
            <div className="w-16 h-16 rounded-full bg-purple-500/20 border-2 border-purple-500 flex items-center justify-center text-purple-400 font-bold text-xl z-10">
              3
            </div>
            <div className="flex-1 bg-gray-900/80 border border-purple-500/30 rounded-xl p-4">
              <div className="flex items-center gap-4 mb-2">
                <span className="text-purple-400 font-mono text-sm">
                  t=25-30
                </span>
                <span className="text-white font-bold">
                  Requeue OR Complete
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                  <div className="text-green-400 font-bold">
                    ✓ Job completed
                  </div>
                  <div className="text-gray-400 text-sm">Mark as completed</div>
                </div>
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                  <div className="text-red-400 font-bold">✗ Timeout</div>
                  <div className="text-gray-400 text-sm">
                    Requeue + increment retry_count
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Phase 4 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="relative flex items-start gap-6"
          >
            <div className="w-16 h-16 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center text-red-400 font-bold text-xl z-10">
              4
            </div>
            <div className="flex-1 bg-gray-900/80 border border-red-500/30 rounded-xl p-4">
              <div className="flex items-center gap-4 mb-2">
                <span className="text-red-400 font-mono text-sm">t=30</span>
                <span className="text-white font-bold">
                  Exit Before SIGKILL
                </span>
              </div>
              <p className="text-gray-400">
                Worker exits cleanly — partial files purged
              </p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="flex justify-center gap-8">
          {[
            { label: "Completed normally", value: "47/50" },
            { label: "Requeued atomically", value: "3/50" },
            { label: "Jobs lost", value: "0", color: "text-green-400" },
          ].map((item, i) => (
            <div key={item.label} className="text-center">
              <div
                className={`text-2xl font-bold ${item.color || "text-white"}`}
              >
                {item.value}
              </div>
              <div className="text-xs text-gray-500">{item.label}</div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
