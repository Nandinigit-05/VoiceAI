import { Bot, TrendingUp, AlertCircle, Lightbulb, FileText } from "lucide-react";
import type { AiFeedback } from "@/services/api";

interface AIFeedbackCardProps {
  feedback: AiFeedback;
}

const AIFeedbackCard = ({ feedback }: AIFeedbackCardProps) => {
  const { overall_assessment, areas_to_improve, actionable_tips, improved_sample_answer } = feedback;

  return (
    <div className="glass-card p-6 animate-fade-up" style={{ animationDelay: "0.4s" }}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
          <Bot className="w-5 h-5 text-foreground" />
        </div>
        <div>
          <h2 className="font-display text-xl font-semibold">AI Coach Feedback</h2>
          <p className="text-muted-foreground text-sm">Focused interview coaching</p>
        </div>
      </div>

      <div className="space-y-5">
        {/* Overall Assessment */}
        {overall_assessment && overall_assessment.trim().length > 0 && (
          <div className="p-5 rounded-xl border bg-primary/5 border-primary/20 animate-fade-up" style={{ animationDelay: "0.5s" }}>
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-shrink-0">
                <TrendingUp className="w-5 h-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold text-foreground">
                Overall Assessment
              </h3>
            </div>
            <p className="text-foreground/90 leading-relaxed whitespace-pre-wrap">
              {overall_assessment}
            </p>
          </div>
        )}

        {/* Areas to Improve */}
        {Array.isArray(areas_to_improve) && areas_to_improve.length > 0 && (
          <div className="p-5 rounded-xl border bg-warning/5 border-warning/20 animate-fade-up" style={{ animationDelay: "0.6s" }}>
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-shrink-0">
                <AlertCircle className="w-5 h-5 text-warning" />
              </div>
              <h3 className="font-display text-lg font-semibold text-foreground">
                Areas to Improve
              </h3>
            </div>
            <ul className="list-disc list-inside space-y-1 text-foreground/90 text-sm">
              {areas_to_improve.map((item, index) => (
                <li key={index} className="leading-relaxed">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actionable Tips */}
        {Array.isArray(actionable_tips) && actionable_tips.length > 0 && (
          <div className="p-5 rounded-xl border bg-primary/5 border-primary/20 animate-fade-up" style={{ animationDelay: "0.7s" }}>
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-shrink-0">
                <Lightbulb className="w-5 h-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold text-foreground">
                Actionable Tips
              </h3>
            </div>
            <ul className="list-disc list-inside space-y-1 text-foreground/90 text-sm">
              {actionable_tips.map((tip, index) => (
                <li key={index} className="leading-relaxed">
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Improved Sample Answer */}
        {improved_sample_answer && improved_sample_answer.trim().length > 0 && (
          <div className="p-5 rounded-xl border bg-secondary/50 border-border animate-fade-up" style={{ animationDelay: "0.8s" }}>
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-shrink-0">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold text-foreground">
                Improved Sample Answer
              </h3>
            </div>
            <div className="rounded-lg bg-background/60 px-4 py-3 text-sm text-foreground/90 whitespace-pre-wrap text-left">
              {improved_sample_answer}
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-border">
        <p className="text-muted-foreground text-xs text-center">
          Analysis powered by AI • Use this as guidance to refine your next answer
        </p>
      </div>
    </div>
  );
};

export default AIFeedbackCard;
