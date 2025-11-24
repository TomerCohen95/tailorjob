import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Target, CheckCircle2, AlertCircle, Lightbulb, 
  TrendingUp, Award, Loader2, Sparkles
} from 'lucide-react';
import { MatchScore } from '@/lib/api';
import { MatchScoreBadge } from './MatchScoreBadge';
import { cn } from '@/lib/utils';

interface MatchScorePanelProps {
  score?: MatchScore | null;
  loading?: boolean;
  onAnalyze?: () => void;
}

export function MatchScorePanel({ score, loading, onAnalyze }: MatchScorePanelProps) {
  if (!score && !loading) {
    return (
      <Card className="border-dashed border-2">
        <CardContent className="flex flex-col items-center justify-center py-12 gap-4">
          <div className="rounded-full bg-primary/10 p-4">
            <Target className="h-8 w-8 text-primary" />
          </div>
          <div className="text-center space-y-2">
            <h3 className="font-semibold text-lg">Analyze Your Match</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Use AI to see how well your CV matches this job and get personalized recommendations
            </p>
          </div>
          <Button 
            onClick={onAnalyze} 
            className="bg-gradient-to-r from-primary to-accent hover:opacity-90 gap-2"
          >
            <Sparkles className="h-4 w-4" />
            Analyze Match Score
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Analyzing your CV match...</p>
            <p className="text-xs text-muted-foreground">This may take a few seconds</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!score) return null;

  return (
    <div className="space-y-4">
      {/* Overall Score Card */}
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-background to-primary/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Match Score</CardTitle>
            <MatchScoreBadge score={score.overall_score} size="lg" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Category Scores */}
          <div className="space-y-3">
            {score.skills_score !== undefined && score.skills_score !== null && (
              <ScoreBar
                label="Skills Match"
                score={score.skills_score}
                icon={<Award className="h-4 w-4" />}
              />
            )}
            {score.experience_score !== undefined && score.experience_score !== null && (
              <ScoreBar
                label="Experience Match"
                score={score.experience_score}
                icon={<TrendingUp className="h-4 w-4" />}
              />
            )}
            {score.qualifications_score !== undefined && score.qualifications_score !== null && (
              <ScoreBar
                label="Qualifications Match"
                score={score.qualifications_score}
                icon={<CheckCircle2 className="h-4 w-4" />}
              />
            )}
          </div>
          
          {score.cached && (
            <p className="text-xs text-muted-foreground text-center pt-2 border-t">
              Analyzed {new Date(score.created_at).toLocaleDateString()} at {new Date(score.created_at).toLocaleTimeString()}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Strengths */}
      {score.analysis.strengths?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-green-600 dark:text-green-500">
              <CheckCircle2 className="h-5 w-5" />
              Your Strengths
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {score.analysis.strengths.map((strength, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Gaps */}
      {score.analysis.gaps?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-amber-600 dark:text-amber-500">
              <AlertCircle className="h-5 w-5" />
              Areas to Address
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {score.analysis.gaps.map((gap, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <AlertCircle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {score.analysis.recommendations?.length > 0 && (
        <Card className="border-2 border-primary/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-primary">
              <Lightbulb className="h-5 w-5" />
              AI Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {score.analysis.recommendations.map((rec, i) => (
                <li key={i} className="flex gap-2 text-sm bg-primary/5 p-3 rounded-lg">
                  <Lightbulb className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Skills Breakdown */}
      {(score.analysis.matched_skills?.length > 0 || score.analysis.missing_skills?.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Skills Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {score.analysis.matched_skills?.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2 text-green-600 dark:text-green-500">Matched Skills</p>
                <div className="flex flex-wrap gap-2">
                  {score.analysis.matched_skills.map((skill, i) => (
                    <Badge key={i} variant="outline" className="bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {score.analysis.missing_skills?.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2 text-amber-600 dark:text-amber-500">Missing Skills</p>
                <div className="flex flex-wrap gap-2">
                  {score.analysis.missing_skills.map((skill, i) => (
                    <Badge key={i} variant="outline" className="bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="flex justify-center pt-2">
        <Button 
          variant="outline" 
          onClick={onAnalyze}
          className="gap-2"
        >
          <Sparkles className="h-4 w-4" />
          Re-analyze Match
        </Button>
      </div>
    </div>
  );
}

// Helper component for score bars
function ScoreBar({ label, score, icon }: { label: string; score: number; icon: React.ReactNode }) {
  const getColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          {icon}
          {label}
        </span>
        <span className="font-semibold">{score}%</span>
      </div>
      <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
        <div 
          className={cn("h-full transition-all duration-500 rounded-full", getColor(score))}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}