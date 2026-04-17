import { motion } from "framer-motion";

export default function Slide5_OutboxPattern() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-black to-black" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          OUTBOX PATTERN — CRASH-PROOF
        </div>
        <h2 className="text-4xl font-bold text-white">
          Atomic Transaction: Job + Outbox
        </h2>
      </div>

      <div className="relative z-10 flex gap-8 px-8 min-h-[calc(100vh-180px)]">
        {/* Left: Transaction */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900/80 border border-purple-500/30 rounded-xl p-6"
          >
            <h3 className="text-xl font-bold text-purple-400 mb-4">
              PostgreSQL Transaction
            </h3>
            <pre className="text-sm font-mono text-gray-300 bg-black/50 rounded-lg p-4 overflow-x-auto">
              {`BEGIN TRANSACTION;
  
  INSERT INTO download_jobs
    (id, user_id, url, status, created_at)
    VALUES (uuid, user_id, url, 'pending', now());
  
  INSERT INTO outbox
    (id, job_id, event_type, status, created_at)
    VALUES (uuid, job_id, 'job_created', 'pending', now());
  
COMMIT;  -- ATOMIC: both succeed or both fail`}
            </pre>
            <div className="mt-4 flex items-center gap-2 text-green-400">
              <span className="text-xl">✓</span>
              <span className="font-mono">Single atomic operation</span>
            </div>
          </motion.div>
        </div>

        {/* Center: Flow */}
        <div className="flex flex-col items-center justify-center">
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500/30 to-pink-500/30 border-2 border-purple-500 flex items-center justify-center">
              <span className="text-3xl">⚡</span>
            </div>
          </motion.div>
          <div className="mt-4 text-gray-500 font-mono text-sm">30s poll</div>
        </div>

        {/* Right: Recovery */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-900/80 border border-cyan-500/30 rounded-xl p-6"
          >
            <h3 className="text-xl font-bold text-cyan-400 mb-4">
              Recovery Scenario
            </h3>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex items-center gap-3">
                <span className="text-cyan-400">t=0ms</span>
                <span className="text-gray-400">API receives request</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-cyan-400">t=5ms</span>
                <span className="text-gray-400">
                  PostgreSQL COMMIT (job + outbox)
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-yellow-400">t=6ms</span>
                <span className="text-red-400">⚠ API CRASH</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-cyan-400">t=30000ms</span>
                <span className="text-gray-400">
                  Outbox relay polls, finds pending
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-400">t=30005ms</span>
                <span className="text-green-400">Job is processing!</span>
              </div>
            </div>
            <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <span className="text-green-400 font-mono">
                Result: Job is processed (30s delay is acceptable)
              </span>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Key points */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="flex justify-center gap-8">
          {[
            {
              label: "Single Transaction",
              value: "✓",
              color: "text-green-400",
            },
            { label: "30s Poll Interval", value: "✓", color: "text-green-400" },
            {
              label: "FOR UPDATE SKIP LOCKED",
              value: "✓",
              color: "text-green-400",
            },
            {
              label: "DELETE (not UPDATE)",
              value: "✓",
              color: "text-green-400",
            },
          ].map((item, i) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className={`text-xl ${item.color}`}>{item.value}</span>
              <span className="text-gray-400 text-sm">{item.label}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
