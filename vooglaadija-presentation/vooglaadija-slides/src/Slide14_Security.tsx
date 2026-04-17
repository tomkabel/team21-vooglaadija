import { motion } from "framer-motion";

const securityFeatures = [
  { name: "Password Hashing", impl: "bcrypt (cost factor 12)", icon: "🔐" },
  { name: "JWT Access Token", impl: "HS256, 15 min expiry", icon: "🎫" },
  { name: "JWT Refresh Token", impl: "7 days, rotation enabled", icon: "🔄" },
  { name: "IDOR Protection", impl: "User ID in WHERE clause", icon: "🛡️" },
  { name: "CSRF Protection", impl: "Double-submit cookie", icon: "⚔️" },
  { name: "Rate Limiting", impl: "60 req/min per IP", icon: "🚦" },
];

export default function Slide14_Security() {
  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-green-900/20 via-black to-gray-900" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          SCENE 7: SECURITY IMPLEMENTATION
        </div>
        <h2 className="text-4xl font-bold text-white">Defense in Depth</h2>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-180px)] px-8">
        <div className="grid grid-cols-3 gap-4 max-w-4xl">
          {securityFeatures.map((feature, i) => (
            <motion.div
              key={feature.name}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="bg-gray-900/80 border border-green-500/30 rounded-xl p-6 text-center"
            >
              <div className="text-4xl mb-3">{feature.icon}</div>
              <div className="text-lg font-bold text-white mb-1">
                {feature.name}
              </div>
              <div className="text-sm text-green-400 font-mono">
                {feature.impl}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute bottom-0 left-0 right-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800 px-8 py-4"
      >
        <div className="text-center text-gray-400 text-sm">
          Each layer addresses a specific{" "}
          <span className="text-green-400 font-semibold">threat vector</span>
        </div>
      </motion.div>
    </div>
  );
}
