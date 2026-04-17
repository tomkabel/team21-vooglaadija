import { motion } from "framer-motion";

export default function Slide9_TwoMechanisms() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-orange-900/20 via-black to-red-900/10" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          TWO-MECHANISM RECOVERY ARCHITECTURE
        </div>
        <h2 className="text-4xl font-bold text-white">
          Handling Different Failure Types
        </h2>
      </div>

      <div className="relative z-10 flex gap-8 px-8 py-4 min-h-[calc(100vh-180px)]">
        {/* Mechanism 1 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex-1 bg-gray-900/80 border border-yellow-500/30 rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-yellow-400">
              reset_stuck_jobs()
            </h3>
            <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-full px-3 py-1">
              <span className="text-yellow-400 font-mono text-sm">10 MIN</span>
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-gray-400 text-sm">
              <span className="text-yellow-400 font-semibold">Purpose:</span>{" "}
              Quick recovery for NORMAL stuck scenarios
            </div>

            <div className="bg-black/30 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-2">Use cases:</div>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• Worker hangs but doesn't crash</li>
                <li>• Worker deadlocks on internal resource</li>
                <li>• Temporary network issue</li>
              </ul>
            </div>

            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <div className="text-red-400 font-bold mb-1">
                → Marks job as FAILED
              </div>
              <div className="text-gray-400 text-sm">
                Something is wrong → fail fast, alert needed
              </div>
            </div>
          </div>
        </motion.div>

        {/* Center divider */}
        <div className="flex flex-col items-center justify-center">
          <div className="w-0.5 h-32 bg-gradient-to-b from-yellow-500 to-red-500" />
          <div className="text-2xl mt-4">⚡</div>
        </div>

        {/* Mechanism 2 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="flex-1 bg-gray-900/80 border border-red-500/30 rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-red-400">
              requeue_stuck_jobs()
            </h3>
            <div className="bg-red-500/20 border border-red-500/50 rounded-full px-3 py-1">
              <span className="text-red-400 font-mono text-sm">15 MIN</span>
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-gray-400 text-sm">
              <span className="text-red-400 font-semibold">Purpose:</span>{" "}
              Catastrophic failure recovery (SIGKILL/OOM)
            </div>

            <div className="bg-black/30 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-2">Use cases:</div>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• Container OOM → SIGKILL (graceful never runs)</li>
                <li>• Kubernetes node failure</li>
                <li>• Host-level crash</li>
              </ul>
            </div>

            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <div className="text-green-400 font-bold mb-1">
                → Marks job as PENDING
              </div>
              <div className="text-gray-400 text-sm">
                Work not lost, just interrupted → auto-recover
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Failure coverage */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="flex justify-center gap-8 text-center">
          {[
            {
              scenario: "Worker Hang",
              handler: "reset_stuck_jobs → FAILED",
              color: "text-yellow-400",
            },
            {
              scenario: "SIGTERM (graceful)",
              handler: "Shutdown → requeue",
              color: "text-green-400",
            },
            {
              scenario: "SIGKILL/OOM",
              handler: "Zombie Sweeper → PENDING",
              color: "text-red-400",
            },
          ].map((item, i) => (
            <div key={item.scenario}>
              <div className="text-gray-400 text-sm">{item.scenario}</div>
              <div className={`text-sm font-mono ${item.color}`}>
                {item.handler}
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
