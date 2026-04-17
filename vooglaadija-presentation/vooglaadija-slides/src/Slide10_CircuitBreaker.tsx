import { motion } from "framer-motion";

export default function Slide10_CircuitBreaker() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-black to-purple-900/10" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          CIRCUIT BREAKER STATE MACHINE
        </div>
        <h2 className="text-4xl font-bold text-white">
          Preventing Cascading Failures
        </h2>
      </div>

      {/* State diagram */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-200px)] px-8">
        <div className="flex items-center gap-8">
          {/* CLOSED */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-40 h-40 rounded-full bg-gradient-to-br from-green-500/20 to-green-600/20 border-4 border-green-500 flex flex-col items-center justify-center"
          >
            <div className="text-3xl font-bold text-green-400">CLOSED</div>
            <div className="text-xs text-gray-400">Normal</div>
          </motion.div>

          {/* Arrow */}
          <div className="flex flex-col items-center">
            <div className="text-gray-500 text-sm mb-2">
              failures ≥ threshold
            </div>
            <motion.div
              animate={{ x: [0, 5, 0] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="text-3xl text-cyan-400"
            >
              →
            </motion.div>
          </div>

          {/* OPEN */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="w-40 h-40 rounded-full bg-gradient-to-br from-red-500/20 to-red-600/20 border-4 border-red-500 flex flex-col items-center justify-center"
          >
            <div className="text-3xl font-bold text-red-400">OPEN</div>
            <div className="text-xs text-gray-400">Failing</div>
          </motion.div>

          {/* Arrow */}
          <div className="flex flex-col items-center">
            <div className="text-gray-500 text-sm mb-2">recovery_timeout</div>
            <motion.div
              animate={{ y: [0, 5, 0] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="text-3xl text-cyan-400"
            >
              ↓
            </motion.div>
          </div>

          {/* HALF-OPEN */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="w-40 h-40 rounded-full bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 border-4 border-yellow-500 flex flex-col items-center justify-center"
          >
            <div className="text-3xl font-bold text-yellow-400">HALF-OPEN</div>
            <div className="text-xs text-gray-400">Testing</div>
          </motion.div>
        </div>
      </div>

      {/* Bug fix callout */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-4">
          <div className="text-red-400 font-bold mb-2">
            ⚠ BUG FIX (per production-analysis.md)
          </div>
          <div className="grid grid-cols-2 gap-6 text-sm">
            <div>
              <div className="text-gray-400 mb-1">BEFORE:</div>
              <div className="text-red-300 font-mono">
                _half_open_calls += 1 (never decremented)
              </div>
            </div>
            <div>
              <div className="text-gray-400 mb-1">AFTER:</div>
              <div className="text-green-300 font-mono">
                _half_open_calls += 1 (then -=1 after completion)
              </div>
            </div>
          </div>
        </div>
        <div className="text-center text-gray-400 text-sm">
          Counter grows indefinitely → circuit stays OPEN → recovery blocked
        </div>
      </motion.div>
    </div>
  );
}
