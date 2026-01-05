import { ArrowLeft, Shield, Sparkles } from "lucide-react";
import TranscriptCard from "./TranscriptCard";
import SpeedGauge from "./SpeedGauge";
import FillerWordsChart from "./FillerWordsChart";
import CircularProgress from "./CircularProgress";
import AIFeedbackCard from "./AIFeedbackCard";
import type { AiFeedback } from "@/services/api";

interface AnalysisData {
  transcript: string;
  word_count: number;
  wpm: number;
  confidence_score: number;
  clarity_score: number;
  filler_counts: Record<string, number>;
  ai_feedback: AiFeedback;
}

interface AnalysisDashboardProps {
  data: AnalysisData;
  onReset: () => void;
}

const AnalysisDashboard = ({ data, onReset }: AnalysisDashboardProps) => {

  return (
    <section className="min-h-screen px-4 py-8 md:py-12">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 animate-fade-up">
          <div>
            <button
              onClick={onReset}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Record Again</span>
            </button>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Your <span className="text-gradient">Analysis</span> Results
            </h1>
          </div>
          
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary/20 border border-primary/30">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm text-primary font-medium">AI Analysis Complete</span>
          </div>
        </div>

        {/* Transcript */}
        <div className="mb-8">
          <TranscriptCard transcript={data.transcript} />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Left Column */}
          <div className="space-y-6">
            <SpeedGauge wpm={data.wpm} wordCount={data.word_count} />
            <FillerWordsChart fillerCounts={data.filler_counts} />
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Circular Progress Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="animate-fade-up" style={{ animationDelay: "0.3s" }}>
                <CircularProgress
                  value={data.confidence_score}
                  label="Confidence Score"
                  icon={<Shield className="w-5 h-5 text-success" />}
                  color="success"
                />
              </div>
              <div className="animate-fade-up" style={{ animationDelay: "0.35s" }}>
                <CircularProgress
                  value={data.clarity_score}
                  label="Clarity Score"
                  icon={<Sparkles className="w-5 h-5 text-primary" />}
                  color="primary"
                />
              </div>
            </div>

            {/* AI Feedback */}
            <AIFeedbackCard feedback={data.ai_feedback} />
          </div>
        </div>

        {/* Footer CTA */}
        <div className="text-center animate-fade-up" style={{ animationDelay: "0.6s" }}>
          <button
            onClick={onReset}
            className="px-8 py-4 rounded-xl font-display font-semibold bg-gradient-to-r from-primary to-primary/80 glow-button text-foreground transition-all"
          >
            Practice Another Response
          </button>
          <p className="mt-4 text-muted-foreground text-sm">
            Regular practice leads to interview success
          </p>
        </div>
      </div>
    </section>
  );
};

export default AnalysisDashboard;
