import { useState, useEffect } from "react";
import { motion } from "framer-motion";

const logs = [
  {
    time: "03:47:12.000",
    level: "ERROR",
    msg: "Job #4473: HTTP 429 Too Many Requests (Token bucket exhausted)",
    color: "text-red-400",
  },
  {
    time: "03:47:12.050",
    level: "INFO",
    msg: "Job #4473: Backoff attempt 1. Delay: 18s (Full Jitter)",
    color: "text-cyan-400",
  },
  {
    time: "03:48:05.112",
    level: "ERROR",
    msg: "Job #4473: HTTP 429 Too Many Requests",
    color: "text-red-400",
  },
  {
    time: "03:48:05.150",
    level: "INFO",
    msg: "Job #4473: Backoff attempt 2. Delay: 73s (Full Jitter)",
    color: "text-cyan-400",
  },
  {
    time: "03:52:15.000",
    level: "SUCCESS",
    msg: "Job #4473: Stream downloaded and verified.",
    color: "text-green-400",
  },
];

export default function Slide2_Hook() {
  const [visibleLogs, setVisibleLogs] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleLogs((v) => (v < logs.length ? v + 1 : v));
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      {/* Dark terminal background */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-black" />

      {/* Scanlines effect */}
      <div
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          background:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)",
        }}
      />

      {/* Header */}
      <div className="relative z-10 px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
          <span className="text-gray-400 font-mono text-sm">
            SYSTEM LOG | 2026-04-17
          </span>
        </div>
        <div className="text-cyan-400 font-mono text-sm">SCENE 1: THE HOOK</div>
      </div>

      {/* Main content */}
      <div className="relative z-10 px-8 py-4">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-5xl font-bold text-white mb-2">
            3:47 AM — Production Failure
          </h2>
          <p className="text-gray-400 text-lg">
            What happens when the YouTube API fails at 3 AM
          </p>
        </motion.div>

        {/* Terminal window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden max-w-4xl mx-auto"
        >
          {/* Terminal header */}
          <div className="bg-gray-900 px-4 py-3 flex items-center gap-2 border-b border-gray-800">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="ml-4 text-gray-400 text-sm font-mono">
              vooglaadija-worker-1
            </span>
          </div>

          {/* Terminal content */}
          <div className="p-6 font-mono text-sm space-y-2">
            {logs.map((log, i) => (
              <motion.div
                key={log.time}
                initial={{ opacity: 0, x: -20 }}
                animate={{
                  opacity: i < visibleLogs ? 1 : 0,
                  x: i < visibleLogs ? 0 : -20,
                }}
                transition={{ duration: 0.3 }}
                className={`flex gap-4 ${i < visibleLogs ? "" : "invisible"}`}
              >
                <span className="text-gray-500">{log.time}</span>
                <span
                  className={`${log.level === "ERROR" ? "text-red-400" : log.level === "SUCCESS" ? "text-green-400" : "text-cyan-400"} font-semibold`}
                >
                  [{log.level}]
                </span>
                <span className="text-gray-300">{log.msg}</span>
              </motion.div>
            ))}
            {visibleLogs >= logs.length && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-4 pt-4 border-t border-gray-800"
              >
                <span className="text-green-400">▶</span>
                <span className="text-gray-400 ml-2">
                  Download completed: video_4473.mp4 (1.2 GB)
                </span>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Key insight */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5 }}
          className="mt-8 text-center"
        >
          <div className="inline-block bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 rounded-lg px-6 py-4">
            <p className="text-cyan-400 text-xl font-mono">
              "Job #4473 survived 3 failures and 5 minutes of chaos —{" "}
              <span className="text-white font-bold">
                HTTP 429. No pages. No manual intervention.
              </span>
              "
            </p>
          </div>
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          className="mt-12 grid grid-cols-4 gap-4 max-w-4xl mx-auto"
        >
          {[
            { label: "Failures Survived", value: "3", icon: "⟲" },
            { label: "Total Time", value: "5m 3s", icon: "◷" },
            { label: "Manual Actions", value: "0", icon: "✓" },
            { label: "Result", value: "SUCCESS", icon: "✓" },
          ].map((stat, i) => (
            <div
              key={stat.label}
              className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 text-center"
            >
              <div className="text-2xl mb-1">{stat.icon}</div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-gray-500 uppercase">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Footer */}
      <div className="absolute bottom-4 left-8 right-8 flex justify-between text-xs text-gray-600 font-mono">
        <span>
          CORE THESIS: Production systems fail — SIGKILL, OOM, network
          partitions
        </span>
        <span>0:00 - 0:30</span>
      </div>
    </div>
  );
}
