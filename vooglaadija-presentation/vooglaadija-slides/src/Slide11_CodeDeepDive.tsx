import { motion } from "framer-motion";
import { useState } from "react";

const codeSnippets = [
  {
    title: "Outbox Transaction",
    file: "app/services/outbox_service.py:25-45",
    code: `async def create_job_with_outbox(db, user_id, url):
    job = DownloadJob(
        id=UUID(), user_id=user_id,
        url=url, status=JobStatus.PENDING
    )
    outbox_entry = Outbox(
        id=UUID(), job_id=job.id,
        event_type="job_created"
    )
    db.add(job)
    db.add(outbox_entry)
    await db.commit()  # ATOMIC
    return job`,
  },
  {
    title: "Atomic Job Claim",
    file: "worker/processor.py:30-55",
    code: `async def claim_job(self, job_id):
    result = await self.db.execute(
        update(DownloadJob)
        .where(
            DownloadJob.id == job_id,
            DownloadJob.status == JobStatus.PENDING
        )
        .values(status=JobStatus.PROCESSING)
    )
    claimed = result.rowcount == 1
    if not claimed:
        return False  # Duplicate
    return True`,
  },
  {
    title: "Graceful Shutdown",
    file: "worker/main.py:20-40",
    code: `async def _signal_handler(self, sig):
    self.is_polling = False  # CRITICAL
    
    if self.current_job_id:
        await asyncio.wait_for(
            self._wait_for_job_completion(),
            timeout=25.0  # < K8s SIGKILL
        )`,
  },
  {
    title: "AWS Full Jitter",
    file: "app/services/retry_service.py",
    code: `def calculate_full_jitter(attempt, base=60, cap=600):
    temp = min(cap, base * (2 ** attempt))
    return random.uniform(0, temp)  # AWS Standard`,
  },
];

export default function Slide11_CodeDeepDive() {
  const [active, setActive] = useState(0);

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 via-black to-gray-900" />

      <div className="relative z-10 px-8 py-6">
        <div className="text-cyan-400 font-mono text-sm mb-2">
          SCENE 4: CODE DEEP DIVE
        </div>
        <h2 className="text-4xl font-bold text-white">
          Production-Code Evidence
        </h2>
      </div>

      <div className="relative z-10 flex min-h-[calc(100vh-180px)]">
        {/* Tabs */}
        <div className="w-64 border-r border-gray-800 p-4">
          {codeSnippets.map((snippet, i) => (
            <motion.button
              key={snippet.title}
              onClick={() => setActive(i)}
              whileHover={{ x: 4 }}
              className={`w-full text-left p-4 rounded-lg mb-2 transition-all ${
                active === i
                  ? "bg-cyan-500/20 border border-cyan-500/50"
                  : "bg-gray-900/50 border border-gray-800 hover:border-gray-600"
              }`}
            >
              <div
                className={`font-semibold ${active === i ? "text-cyan-400" : "text-gray-300"}`}
              >
                {snippet.title}
              </div>
              <div className="text-xs text-gray-500 mt-1">{snippet.file}</div>
            </motion.button>
          ))}
        </div>

        {/* Code display */}
        <div className="flex-1 p-6">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-950 border border-gray-800 rounded-xl h-full overflow-hidden"
          >
            <div className="bg-gray-900 px-4 py-3 border-b border-gray-800 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="ml-4 text-gray-400 text-sm font-mono">
                {codeSnippets[active].file}
              </span>
            </div>
            <pre className="p-6 text-sm font-mono text-gray-300 overflow-x-auto h-[calc(100%-48px)]">
              {codeSnippets[active].code}
            </pre>
          </motion.div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 border-t border-gray-800 px-8 py-3">
        <div className="flex justify-center gap-6 text-sm text-gray-400">
          <span className="text-cyan-400">✓</span>
          <span>Line-level file references</span>
          <span className="text-cyan-400">✓</span>
          <span>Actual production code</span>
          <span className="text-cyan-400">✓</span>
          <span>Verified per production-analysis.md</span>
        </div>
      </div>
    </div>
  );
}
