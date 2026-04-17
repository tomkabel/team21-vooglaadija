import { useState, useEffect, useCallback } from "react";
import Slide1_Cover from "./Slide1_Cover";
import Slide2_Hook from "./Slide2_Hook";
import Slide3_Problem from "./Slide3_Problem";
import Slide4_Architecture from "./Slide4_Architecture";
import Slide5_OutboxPattern from "./Slide5_OutboxPattern";
import Slide6_AtomicClaims from "./Slide6_AtomicClaims";
import Slide7_GracefulShutdown from "./Slide7_GracefulShutdown";
import Slide8_FullJitter from "./Slide8_FullJitter";
import Slide9_TwoMechanisms from "./Slide9_TwoMechanisms";
import Slide10_CircuitBreaker from "./Slide10_CircuitBreaker";
import Slide11_CodeDeepDive from "./Slide11_CodeDeepDive";
import Slide12_LiveDemo from "./Slide12_LiveDemo";
import Slide13_Observability from "./Slide13_Observability";
import Slide14_Security from "./Slide14_Security";
import Slide15_CICD from "./Slide15_CICD";
import Slide16_FailureScenarios from "./Slide16_FailureScenarios";
import Slide17_Conclusion from "./Slide17_Conclusion";

const slides = [
  Slide1_Cover,
  Slide2_Hook,
  Slide3_Problem,
  Slide4_Architecture,
  Slide5_OutboxPattern,
  Slide6_AtomicClaims,
  Slide7_GracefulShutdown,
  Slide8_FullJitter,
  Slide9_TwoMechanisms,
  Slide10_CircuitBreaker,
  Slide11_CodeDeepDive,
  Slide12_LiveDemo,
  Slide13_Observability,
  Slide14_Security,
  Slide15_CICD,
  Slide16_FailureScenarios,
  Slide17_Conclusion,
];

const slideNames = [
  "Cover",
  "The Hook",
  "The Problem",
  "Architecture",
  "Outbox Pattern",
  "Atomic Claims",
  "Graceful Shutdown",
  "Full Jitter",
  "Two Mechanisms",
  "Circuit Breaker",
  "Code Deep Dive",
  "Live Demo",
  "Observability",
  "Security",
  "CI/CD",
  "Failure Scenarios",
  "Conclusion",
];

function App() {
  const [currentSlide, setCurrentSlide] = useState(0);

  const nextSlide = useCallback(() => {
    setCurrentSlide((prev) => Math.min(prev + 1, slides.length - 1));
  }, []);

  const prevSlide = useCallback(() => {
    setCurrentSlide((prev) => Math.max(prev - 1, 0));
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " ") {
        e.preventDefault();
        nextSlide();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        prevSlide();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [nextSlide, prevSlide]);

  const CurrentSlide = slides[currentSlide];

  return (
    <div className="min-h-screen bg-black relative">
      <CurrentSlide />

      {/* Navigation indicator */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-black/80 backdrop-blur-sm border border-gray-800 rounded-full px-6 py-3 z-50">
        <button
          type="button"
          onClick={prevSlide}
          disabled={currentSlide === 0}
          className="text-gray-400 hover:text-white disabled:opacity-30 transition-colors text-2xl"
        >
          ←
        </button>
        <div className="flex items-center gap-2">
          <span className="text-cyan-400 font-mono text-sm">
            {String(currentSlide + 1).padStart(2, "0")}
          </span>
          <span className="text-gray-500">/</span>
          <span className="text-gray-400 font-mono text-sm">
            {String(slides.length).padStart(2, "0")}
          </span>
        </div>
        <div className="text-gray-400 text-sm font-mono w-32 text-center">
          {slideNames[currentSlide]}
        </div>
        <button
          type="button"
          onClick={nextSlide}
          disabled={currentSlide === slides.length - 1}
          className="text-gray-400 hover:text-white disabled:opacity-30 transition-colors text-2xl"
        >
          →
        </button>
      </div>

      {/* Progress bar */}
      <div className="fixed top-0 left-0 right-0 h-1 bg-gray-900 z-50">
        <div
          className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
          style={{ width: `${((currentSlide + 1) / slides.length) * 100}%` }}
        />
      </div>

      {/* Keyboard hint */}
      <div className="fixed top-4 right-4 text-xs text-gray-600 font-mono bg-black/50 backdrop-blur-sm px-3 py-2 rounded-lg z-50">
        Use ← → arrow keys to navigate
      </div>
    </div>
  );
}

export default App;
