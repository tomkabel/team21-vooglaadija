import { motion } from "framer-motion";

export default function Slide3_Problem() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-black to-purple-900/20" />

      {/* Header */}
      <div className="relative z-10 px-8 py-6 border-b border-gray-800/50">
        <div className="text-cyan-400 font-mono text-sm">
          SCENE 2: THE PROBLEM
        </div>
        <h2 className="text-4xl font-bold text-white mt-2">
          Why YouTube Downloads Are Harder Than They Look
        </h2>
      </div>

      {/* Split content */}
      <div className="relative z-10 flex min-h-[calc(100vh-120px)]">
        {/* Left: YouTube's Reality */}
        <div className="w-1/2 p-8 border-r border-gray-800/50">
          <h3 className="text-xl font-bold text-red-400 mb-6 flex items-center gap-2">
            <span className="text-2xl">◉</span> YouTube's Reality
          </h3>
          <div className="space-y-4">
            {[
              {
                icon: "⚡",
                title: "Rate Limits",
                desc: "HTTP 429 - IP-based token bucket",
              },
              {
                icon: "🌍",
                title: "Geo-blocks",
                desc: "Content unavailable in region",
              },
              {
                icon: "🔄",
                title: "Format Changes",
                desc: "Codec deprecated overnight",
              },
              {
                icon: "☠️",
                title: "Server Outages",
                desc: "HTTP 503 Service Unavailable",
              },
              {
                icon: "📡",
                title: "Network Instability",
                desc: "Connection reset by peer",
              },
            ].map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-gray-900/50 border border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{item.icon}</span>
                  <div>
                    <div className="font-semibold text-white">{item.title}</div>
                    <div className="text-sm text-gray-400">{item.desc}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right: User Expectation */}
        <div className="w-1/2 p-8">
          <h3 className="text-xl font-bold text-green-400 mb-6 flex items-center gap-2">
            <span className="text-2xl">◎</span> User Expectation
          </h3>
          <div className="space-y-6">
            {[
              { step: "1", action: "Paste link" },
              { step: "2", action: "Wait" },
              { step: "3", action: "Get video" },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + i * 0.1 }}
                className="flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-green-500/20 to-cyan-500/20 border border-green-500/50 flex items-center justify-center text-xl font-bold text-green-400">
                  {item.step}
                </div>
                <div className="text-xl text-gray-300">{item.action}</div>
              </motion.div>
            ))}
          </div>

          {/* The gap */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1 }}
            className="mt-12 p-6 bg-gradient-to-r from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-xl text-center"
          >
            <div className="text-4xl mb-4">⚡ → ❌</div>
            <div className="text-gray-400">
              The gap between reality and expectation
            </div>
          </motion.div>
        </div>
      </div>

      {/* Statistics footer */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="flex justify-center gap-12 text-center">
          {[
            {
              value: "60%",
              label: "YoY API Downtime Increase",
              source: "Uptrends 2025",
            },
            {
              value: "55 min",
              label: "Weekly API Unavailability",
              source: "Industry Report",
            },
            {
              value: "51%",
              label: "Bot Traffic (Imperva)",
              source: "2025 Bot Report",
            },
          ].map((stat, i) => (
            <div key={stat.label}>
              <div className="text-2xl font-bold text-cyan-400">
                {stat.value}
              </div>
              <div className="text-sm text-gray-400">{stat.label}</div>
              <div className="text-xs text-gray-600">{stat.source}</div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
