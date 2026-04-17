import { motion } from "framer-motion";

export default function Slide6_AtomicClaims() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-green-900/20 via-black to-black" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          ATOMIC JOB CLAIMS
        </div>
        <h2 className="text-4xl font-bold text-white">
          At-Least-Once with Idempotent Transitions
        </h2>
        <p className="text-red-400 mt-2 font-mono">
          ⚠ "Exactly-once delivery" is a DISTRIBUTED SYSTEMS MYTH
        </p>
      </div>

      <div className="relative z-10 flex gap-8 px-8 py-4 min-h-[calc(100vh-220px)]">
        {/* Left: The Update */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-gray-900/80 border border-green-500/30 rounded-xl p-6 h-full"
          >
            <h3 className="text-xl font-bold text-green-400 mb-4">
              UPDATE ... WHERE status = 'pending'
            </h3>
            <pre className="text-sm font-mono text-gray-300 bg-black/50 rounded-lg p-4 overflow-x-auto h-[calc(100%-80px)]">
              {`UPDATE download_jobs
  SET status = 'processing',
      updated_at = now()
  WHERE id = $job_id
    AND status = 'pending'

RETURNING rowcount;

IF rowcount = 1 → Won the race
IF rowcount = 0 → Duplicate, safely ignored`}
            </pre>
          </motion.div>
        </div>

        {/* Center: Flow diagram */}
        <div className="flex flex-col items-center justify-center">
          <div className="space-y-8">
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-center"
            >
              <div className="text-red-400 font-bold">
                Redis delivers duplicate
              </div>
              <div className="text-gray-400 text-sm">
                Same job_id to two workers
              </div>
            </motion.div>

            <div className="text-cyan-400 text-4xl">↓</div>

            <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4 text-center">
              <div className="text-green-400 font-bold">
                Worker 1: rowcount = 1
              </div>
              <div className="text-gray-400 text-sm">Process job</div>
            </div>

            <div className="text-gray-500 text-4xl">↓</div>

            <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4 text-center">
              <div className="text-gray-400 font-bold">
                Worker 2: rowcount = 0
              </div>
              <div className="text-gray-500 text-sm">
                Discard (expected behavior)
              </div>
            </div>
          </div>
        </div>

        {/* Right: Results */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-900/80 border border-cyan-500/30 rounded-xl p-6 h-full"
          >
            <h3 className="text-xl font-bold text-cyan-400 mb-4">
              Test: 10 workers, 100 jobs
            </h3>
            <div className="space-y-4">
              {[
                {
                  label: "Jobs processed at least once",
                  value: "100%",
                  color: "text-green-400",
                },
                {
                  label: "Race conditions detected",
                  value: "0",
                  color: "text-green-400",
                },
                {
                  label: "Duplicate processing events",
                  value: "0",
                  color: "text-green-400",
                },
                { label: "Lost jobs", value: "0", color: "text-green-400" },
              ].map((stat, i) => (
                <div
                  key={stat.label}
                  className="flex items-center justify-between p-3 bg-black/30 rounded-lg"
                >
                  <span className="text-gray-400">{stat.label}</span>
                  <span className={`text-2xl font-bold ${stat.color}`}>
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Key insight */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="text-center">
          <span className="text-cyan-400 font-mono">KEY INSIGHT: </span>
          <span className="text-gray-400">
            No distributed locks needed — database MVCC guarantees atomicity
          </span>
        </div>
      </motion.div>
    </div>
  );
}
