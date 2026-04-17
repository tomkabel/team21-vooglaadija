import { motion } from "framer-motion";

export default function Slide12_LiveDemo() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-red-900/20 via-black to-black" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-red-400 font-mono text-sm mb-2">
          ⚡ CHAOS ENGINEERING
        </div>
        <h2 className="text-4xl font-bold text-white">
          Live Demo: Kill Redis Mid-Download
        </h2>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-180px)] px-8">
        <div className="max-w-3xl w-full">
          {/* Steps */}
          <div className="space-y-4">
            {[
              {
                step: 1,
                action: "Start download (SSE stream shows progress)",
                status: "active",
              },
              {
                step: 2,
                action: "docker kill vooglaadija_redis_1",
                status: "pending",
                terminal: true,
              },
              {
                step: 3,
                action: "SSE degrades to polling mode (30s intervals)",
                status: "pending",
              },
              {
                step: 4,
                action: "Outbox accumulates via /metrics",
                status: "pending",
              },
              {
                step: 5,
                action: "docker start vooglaadija_redis_1",
                status: "pending",
                terminal: true,
              },
              {
                step: 6,
                action: "Queue flushes, download resumes, completion",
                status: "pending",
                success: true,
              },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
                className={`flex items-center gap-4 p-4 rounded-xl border ${
                  item.status === "active"
                    ? "bg-green-500/10 border-green-500/50"
                    : item.success
                      ? "bg-green-500/10 border-green-500/50"
                      : "bg-gray-900/50 border-gray-800"
                }`}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                    item.success
                      ? "bg-green-500 text-white"
                      : item.status === "active"
                        ? "bg-cyan-500 text-white animate-pulse"
                        : "bg-gray-800 text-gray-400"
                  }`}
                >
                  {item.success ? "✓" : item.step}
                </div>
                <div
                  className={`flex-1 font-mono text-sm ${item.terminal ? "text-yellow-400" : "text-gray-300"}`}
                >
                  {item.action}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Terminal mock */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
            className="mt-8 bg-gray-950 border border-gray-800 rounded-xl overflow-hidden"
          >
            <div className="bg-gray-900 px-4 py-2 border-b border-gray-800 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="ml-4 text-gray-400 text-sm font-mono">
                terminal
              </span>
            </div>
            <div className="p-4 font-mono text-sm">
              <div className="text-gray-400">
                $ docker kill vooglaadija_redis_1
              </div>
              <div className="text-green-400 mt-2">vooglaadija_redis_1</div>
              <div className="text-gray-500 mt-4">
                # SSE stream shows: "Redis disconnected, falling back to
                polling..."
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800 px-8 py-4">
        <div className="text-center text-gray-400">
          <span className="text-red-400 font-bold">
            "Everything working is boring. Let's break it."
          </span>
        </div>
      </div>
    </div>
  );
}
