import { motion } from "framer-motion";

const metrics = [
  { name: "ytprocessor_jobs_created_total", type: "Counter", labels: "status" },
  {
    name: "ytprocessor_jobs_completed_total",
    type: "Counter",
    labels: "status",
  },
  {
    name: "ytprocessor_job_duration_seconds",
    type: "Histogram",
    labels: "—",
    buckets: "[10,30,60,120,300,600]",
  },
  {
    name: "ytprocessor_http_requests_total",
    type: "Counter",
    labels: "method,endpoint,status",
  },
  { name: "ytprocessor_queue_depth", type: "Gauge", labels: "—" },
  { name: "ytprocessor_outbox_pending", type: "Gauge", labels: "—" },
];

export default function Slide13_Observability() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-900/20 via-black to-gray-900" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          SCENE 6: OBSERVABILITY STACK
        </div>
        <h2 className="text-4xl font-bold text-white">
          Production-Grade Operations
        </h2>
      </div>

      <div className="relative z-10 flex gap-8 px-8 py-4 min-h-[calc(100vh-180px)]">
        {/* Metrics table */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900/80 border border-blue-500/30 rounded-xl p-6 h-full"
          >
            <h3 className="text-xl font-bold text-blue-400 mb-4">
              Prometheus Metrics
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2 text-gray-400">Metric</th>
                    <th className="text-left py-2 text-gray-400">Type</th>
                    <th className="text-left py-2 text-gray-400">Labels</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m, i) => (
                    <motion.tr
                      key={m.name}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="border-b border-gray-800/50"
                    >
                      <td className="py-3 font-mono text-cyan-400">{m.name}</td>
                      <td className="py-3 text-purple-400">{m.type}</td>
                      <td className="py-3 text-gray-400">{m.labels}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>

        {/* Custom buckets callout */}
        <div className="w-96">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-red-500/10 border border-red-500/30 rounded-xl p-6"
          >
            <h3 className="text-xl font-bold text-red-400 mb-4">
              ⚠ Custom Histogram Buckets
            </h3>
            <div className="bg-black/50 rounded-lg p-4 mb-4">
              <div className="font-mono text-2xl text-cyan-400 text-center">
                [10, 30, 60, 120, 300, 600]
              </div>
            </div>
            <p className="text-gray-400 text-sm">
              Video downloads take 45-142s (p50-p99). Default Prometheus buckets
              max out at 10s — p99 would be +Inf (useless).
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-4 bg-gray-900/80 border border-gray-700 rounded-xl p-4"
          >
            <h4 className="text-sm font-bold text-gray-300 mb-2">
              Structured Logging
            </h4>
            <pre className="text-xs font-mono text-gray-400">
              {`{ "timestamp": "2026-04-17T03:47:12.456Z",
  "level": "INFO",
  "request_id": "abc-123-def-456",
  "job_id": "550e8400-e29b-41d4-a716",
  "attempt": 2,
  "jitter_type": "full_jitter" }`}
            </pre>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
