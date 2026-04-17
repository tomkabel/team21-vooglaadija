import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Slide1_Cover() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setPhase((p) => (p + 1) % 4);
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-20">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(34,211,238,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(34,211,238,0.1) 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
            transform: `perspective(500px) rotateX(60deg) translateY(${phase * 10}px)`,
          }}
        />
      </div>

      {/* Floating orbs */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 blur-3xl"
        animate={{ x: [0, 100, 0], y: [0, -50, 0], scale: [1, 1.2, 1] }}
        transition={{ duration: 8, repeat: Infinity }}
      />
      <motion.div
        className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-3xl"
        animate={{ x: [0, -80, 0], y: [0, 60, 0], scale: [1.2, 1, 1.2] }}
        transition={{ duration: 10, repeat: Infinity }}
      />

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-8">
        {/* Top badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/50 text-cyan-400 px-4 py-2 text-sm font-mono rounded-full">
            JUNIOR → SENIOR ENGINEER | TalTech 2026
          </div>
        </motion.div>

        {/* Main title */}
        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <h1 className="text-8xl md:text-9xl font-black tracking-tighter bg-gradient-to-b from-white via-cyan-200 to-cyan-400 bg-clip-text text-transparent">
            VOOGLAADIJA
          </h1>
        </motion.div>

        {/* Subtitle */}
        <motion.p
          className="mt-6 text-2xl md:text-3xl text-gray-400 font-light tracking-wide"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          Production-Grade YouTube Download Processor
        </motion.p>

        {/* Animated tagline */}
        <motion.div
          className="mt-16 flex items-center gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          <div className="h-px w-20 bg-gradient-to-r from-transparent to-cyan-500" />
          <AnimatePresence mode="wait">
            <motion.p
              key={phase}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-xl text-cyan-400 font-mono"
            >
              {
                [
                  "STAFF-LEVEL DISTRIBUTED SYSTEMS",
                  "CRASH-PROOF ARCHITECTURE",
                  "MEASURED RELIABILITY",
                  "CHAOS ENGINEERED",
                ][phase]
              }
            </motion.p>
          </AnimatePresence>
          <div className="h-px w-20 bg-gradient-to-l from-transparent to-cyan-500" />
        </motion.div>

        {/* Stats grid */}
        <motion.div
          className="mt-20 grid grid-cols-3 gap-8"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          {[
            { label: "At-Least-Once Delivery", value: "100%" },
            { label: "Zero Lost Jobs", value: "✓" },
            { label: "Processing p99", value: "142s" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + i * 0.1 }}
              className="text-center"
            >
              <div className="text-4xl font-bold text-white mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-gray-500 uppercase tracking-wider">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Bottom scan line */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500 to-transparent"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: [0, 1, 0] }}
          transition={{ duration: 3, repeat: Infinity }}
        />
      </div>

      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-24 h-24 border-l-2 border-t-2 border-cyan-500/30" />
      <div className="absolute top-0 right-0 w-24 h-24 border-r-2 border-t-2 border-cyan-500/30" />
      <div className="absolute bottom-0 left-0 w-24 h-24 border-l-2 border-b-2 border-cyan-500/30" />
      <div className="absolute bottom-0 right-0 w-24 h-24 border-r-2 border-b-2 border-cyan-500/30" />

      <div className="absolute bottom-4 right-4 text-xs text-gray-600 font-mono">
        v5.1 | STAFF-LEVEL REVIEW READY
      </div>
    </div>
  );
}
