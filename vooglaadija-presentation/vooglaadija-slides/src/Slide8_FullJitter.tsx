import { motion } from "framer-motion";

export default function Slide8_FullJitter() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-900/20 via-black to-black" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          AWS STANDARD FULL JITTER
        </div>
        <h2 className="text-4xl font-bold text-white">
          Exponential Backoff That Scales
        </h2>
      </div>

      <div className="relative z-10 flex gap-8 px-8 py-4 min-h-[calc(100vh-180px)]">
        {/* Left: Formula */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900/80 border border-blue-500/30 rounded-xl p-6 h-full"
          >
            <h3 className="text-xl font-bold text-blue-400 mb-4">
              The Formula
            </h3>
            <div className="bg-black/50 rounded-lg p-6 text-center mb-6">
              <div className="text-2xl font-mono text-cyan-400 mb-2">
                delay = random.uniform(0, min(cap, base × 2^attempt))
              </div>
            </div>
            <pre className="text-sm font-mono text-gray-400">
              {`# Python Implementation
def calculate_full_jitter(attempt, base=60, cap=600):
    temp = min(cap, base * (2 ** attempt))
    return random.uniform(0, temp)  # AWS Standard`}
            </pre>
          </motion.div>
        </div>

        {/* Right: Comparison table */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-900/80 border border-cyan-500/30 rounded-xl p-6 h-full"
          >
            <h3 className="text-xl font-bold text-cyan-400 mb-4">
              Jitter Ranges (base=60s, cap=600s)
            </h3>
            <div className="space-y-3">
              {[
                { attempt: 1, range: "0-120s", variance: "100%" },
                { attempt: 2, range: "0-240s", variance: "100%" },
                { attempt: 3, range: "0-480s", variance: "100%" },
                { attempt: 4, range: "0-600s", variance: "100%" },
                { attempt: 5, range: "FAIL", variance: "—" },
              ].map((row) => (
                <div
                  key={row.attempt}
                  className="flex items-center justify-between p-3 bg-black/30 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-cyan-400 font-mono w-20">
                      Attempt {row.attempt}
                    </span>
                    <span className="text-gray-400">{row.range}</span>
                  </div>
                  <span
                    className={`text-sm ${row.variance === "100%" ? "text-green-400" : "text-gray-500"}`}
                  >
                    {row.variance}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* v4 vs v5 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="flex justify-center gap-12">
          <div className="text-center">
            <div className="text-red-400 font-bold mb-1">v4 FIXED JITTER</div>
            <div className="text-gray-400 text-sm">
              480s + 0-60s = ~12% variance
            </div>
          </div>
          <div className="text-cyan-400 text-2xl">→</div>
          <div className="text-center">
            <div className="text-green-400 font-bold mb-1">v5 FULL JITTER</div>
            <div className="text-gray-400 text-sm">
              0-600s = 100% variance, perfect spread
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
