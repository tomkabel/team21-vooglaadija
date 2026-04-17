import { motion } from "framer-motion";

const achievements = [
  { label: "Staff-Level Architecture", done: true },
  { label: "Measured Reliability", done: true },
  { label: "Chaos Engineered", done: true },
  { label: "Production-Tested Patterns", done: true },
  { label: "Honest Trade-offs", done: true },
];

export default function Slide17_Conclusion() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-cyan-900/20 via-black to-purple-900/20" />

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-8">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h2 className="text-6xl font-bold text-white mb-4">What We Built</h2>
          <p className="text-2xl text-gray-400">
            A system designed to expect failure — and handle it
          </p>
        </motion.div>

        {/* Achievement badges */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="flex flex-wrap justify-center gap-4 mb-12"
        >
          {achievements.map((a, i) => (
            <motion.div
              key={a.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/50 rounded-full px-6 py-3"
            >
              <span className="text-cyan-400 mr-2">✓</span>
              <span className="text-white font-semibold">{a.label}</span>
            </motion.div>
          ))}
        </motion.div>

        {/* Key insight */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-gray-900/80 border border-cyan-500/30 rounded-2xl p-8 max-w-2xl text-center"
        >
          <p className="text-xl text-gray-300 leading-relaxed">
            "Building a script that downloads a video is easy.
            <br />
            Building a distributed system that survives 55 minutes of weekly API
            downtime —<br />
            <span className="text-cyan-400 font-bold">
              that's software engineering.
            </span>
            "
          </p>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-16 grid grid-cols-4 gap-8"
        >
          {[
            { value: "v5.1", label: "Final Version" },
            { value: "8 min", label: "Presentation" },
            { value: "17", label: "Slides" },
            { value: "100%", label: "Measured" },
          ].map((stat, i) => (
            <div key={stat.label} className="text-center">
              <div className="text-4xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-gray-500">{stat.label}</div>
            </div>
          ))}
        </motion.div>

        {/* Bottom */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-16 text-center"
        >
          <div className="text-gray-600 text-sm font-mono">
            Junior to Senior Developer | TalTech 2026
          </div>
          <div className="text-cyan-400 font-mono mt-2">vooglaadija</div>
        </motion.div>
      </div>
    </div>
  );
}
