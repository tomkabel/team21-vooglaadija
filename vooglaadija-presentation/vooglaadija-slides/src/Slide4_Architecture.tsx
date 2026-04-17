import { motion } from "framer-motion";

export default function Slide4_Architecture() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 via-black to-gray-900" />

      {/* Header */}
      <div className="relative z-10 px-8 py-6 border-b border-gray-800/50">
        <div className="text-cyan-400 font-mono text-sm">
          SCENE 3: SYSTEM ARCHITECTURE
        </div>
        <h2 className="text-5xl font-bold text-white mt-2">
          Production-Grade Reliability
        </h2>
        <p className="text-gray-400 mt-2">
          Three Pillars: Reliability · Observability · Maintainability
        </p>
      </div>

      {/* Architecture diagram */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-200px)] px-8">
        <svg
          viewBox="0 0 1200 500"
          className="w-full max-w-5xl"
          role="img"
          aria-label="System Architecture Diagram"
        >
          {/* Background grid */}
          <defs>
            <pattern
              id="grid"
              width="40"
              height="40"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke="rgba(34,211,238,0.1)"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="1200" height="500" fill="url(#grid)" />

          {/* User/API Layer */}
          <motion.g
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <rect
              x="480"
              y="20"
              width="240"
              height="60"
              rx="8"
              fill="rgba(34,211,238,0.1)"
              stroke="#22d3ee"
              strokeWidth="2"
            />
            <text
              x="600"
              y="55"
              textAnchor="middle"
              fill="#22d3ee"
              fontSize="14"
              fontWeight="bold"
            >
              API / User Request
            </text>
          </motion.g>

          {/* PostgreSQL */}
          <motion.g
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <rect
              x="80"
              y="150"
              width="200"
              height="100"
              rx="8"
              fill="rgba(168,85,247,0.1)"
              stroke="#a855f7"
              strokeWidth="2"
            />
            <text
              x="180"
              y="190"
              textAnchor="middle"
              fill="#a855f7"
              fontSize="14"
              fontWeight="bold"
            >
              PostgreSQL
            </text>
            <text
              x="180"
              y="215"
              textAnchor="middle"
              fill="#a855f7"
              fontSize="12"
            >
              jobs + outbox
            </text>
          </motion.g>

          {/* Outbox Pattern Box */}
          <motion.g
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <rect
              x="80"
              y="280"
              width="200"
              height="80"
              rx="8"
              fill="rgba(236,72,153,0.1)"
              stroke="#ec4899"
              strokeWidth="2"
            />
            <text
              x="180"
              y="315"
              textAnchor="middle"
              fill="#ec4899"
              fontSize="13"
              fontWeight="bold"
            >
              OUTBOX PATTERN
            </text>
            <text
              x="180"
              y="335"
              textAnchor="middle"
              fill="#ec4899"
              fontSize="11"
            >
              Single Transaction
            </text>
          </motion.g>

          {/* Outbox Relay */}
          <motion.g
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <rect
              x="80"
              y="400"
              width="200"
              height="70"
              rx="8"
              fill="rgba(34,211,238,0.1)"
              stroke="#22d3ee"
              strokeWidth="2"
            />
            <text
              x="180"
              y="430"
              textAnchor="middle"
              fill="#22d3ee"
              fontSize="13"
              fontWeight="bold"
            >
              sync_outbox_to_queue()
            </text>
            <text
              x="180"
              y="450"
              textAnchor="middle"
              fill="#22d3ee"
              fontSize="11"
            >
              FOR UPDATE SKIP LOCKED
            </text>
          </motion.g>

          {/* Redis */}
          <motion.g
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <rect
              x="920"
              y="150"
              width="200"
              height="100"
              rx="8"
              fill="rgba(239,68,68,0.1)"
              stroke="#ef4444"
              strokeWidth="2"
            />
            <text
              x="1020"
              y="190"
              textAnchor="middle"
              fill="#ef4444"
              fontSize="14"
              fontWeight="bold"
            >
              Redis Queue
            </text>
            <text
              x="1020"
              y="215"
              textAnchor="middle"
              fill="#ef4444"
              fontSize="12"
            >
              download_queue
            </text>
          </motion.g>

          {/* Worker */}
          <motion.g
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <rect
              x="920"
              y="300"
              width="200"
              height="100"
              rx="8"
              fill="rgba(34,211,238,0.1)"
              stroke="#22d3ee"
              strokeWidth="2"
            />
            <text
              x="1020"
              y="340"
              textAnchor="middle"
              fill="#22d3ee"
              fontSize="14"
              fontWeight="bold"
            >
              Worker(s)
            </text>
            <text
              x="1020"
              y="365"
              textAnchor="middle"
              fill="#22d3ee"
              fontSize="12"
            >
              claim_job() + process
            </text>
          </motion.g>

          {/* YouTube */}
          <motion.g
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
          >
            <rect
              x="920"
              y="440"
              width="200"
              height="50"
              rx="8"
              fill="rgba(255,0,0,0.1)"
              stroke="#ff0000"
              strokeWidth="2"
            />
            <text
              x="1020"
              y="472"
              textAnchor="middle"
              fill="#ff0000"
              fontSize="14"
              fontWeight="bold"
            >
              YouTube API
            </text>
          </motion.g>

          {/* Arrows */}
          <motion.g
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            {/* API to PostgreSQL */}
            <path
              d="M 500 80 L 180 150"
              stroke="#22d3ee"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrow)"
            />
            {/* PostgreSQL to Outbox */}
            <path
              d="M 180 250 L 180 280"
              stroke="#a855f7"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrow)"
            />
            {/* Outbox to Relay */}
            <path
              d="M 180 360 L 180 400"
              stroke="#ec4899"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrow)"
            />
            {/* Relay to Redis */}
            <path
              d="M 280 435 L 920 200"
              stroke="#22d3ee"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrow)"
            />
            {/* Redis to Worker */}
            <path
              d="M 1020 250 L 1020 300"
              stroke="#ef4444"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrow)"
            />
            {/* Worker to YouTube */}
            <path
              d="M 1020 400 L 1020 440"
              stroke="#22d3ee"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrow)"
            />
          </motion.g>

          {/* Arrow marker */}
          <defs>
            <marker
              id="arrow"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L0,6 L9,3 z" fill="#22d3ee" />
            </marker>
          </defs>
        </svg>
      </div>

      {/* Key features row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800/50 px-8 py-4"
      >
        <div className="flex justify-center gap-8">
          {[
            { label: "At-Least-Once", value: "✓", color: "text-green-400" },
            { label: "Crash-Proof", value: "✓", color: "text-green-400" },
            {
              label: "Horizontal Scaling",
              value: "✓",
              color: "text-green-400",
            },
            { label: "No Lost Jobs", value: "✓", color: "text-green-400" },
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
