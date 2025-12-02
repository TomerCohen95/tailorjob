import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import type { Job, MatchScore } from '@/lib/api';

interface MatchDebugPanelProps {
  job: Job | null;
  cvData: any;
  matchScore: MatchScore | null;
}

export function MatchDebugPanel({ job, cvData, matchScore }: MatchDebugPanelProps) {
  const [copied, setCopied] = useState(false);

  const debugData = {
    timestamp: new Date().toISOString(),
    job: job ? {
      id: job.id,
      title: job.title,
      company: job.company,
      description: job.description,
      url: job.url,
      requirements_matrix: job.requirements_matrix,
      created_at: job.created_at
    } : null,
    cv: cvData,
    match_analysis: matchScore ? {
      overall_score: matchScore.overall_score,
      matcher_version: matchScore.matcher_version || matchScore.analysis?.matcher_version || 'unknown',
      
      // v2.x fields (if present)
      deterministic_score: matchScore.deterministic_score,
      fit_score: matchScore.fit_score,
      
      // v3.0 fields (if present)
      ai_holistic_score: matchScore.ai_holistic_score,
      component_average: matchScore.component_average,
      scoring_method: matchScore.scoring_method,
      
      // Component scores (both versions)
      skills_score: matchScore.skills_score,
      experience_score: matchScore.experience_score,
      qualifications_score: matchScore.qualifications_score,
      
      // v3.0 domain analysis (if present)
      domain_fit: matchScore.domain_fit,
      domain_mismatch: matchScore.domain_mismatch,
      domain_mismatch_severity: matchScore.domain_mismatch_severity,
      domain_explanation: matchScore.domain_explanation,
      transferability_assessment: matchScore.transferability_assessment,
      reasoning: matchScore.reasoning,
      
      // Match details (prefer flattened, fallback to nested)
      strengths: matchScore.strengths || matchScore.analysis?.strengths,
      gaps: matchScore.gaps || matchScore.analysis?.gaps,
      recommendations: matchScore.recommendations || matchScore.analysis?.recommendations,
      matched_skills: matchScore.matched_skills || matchScore.analysis?.matched_skills,
      missing_skills: matchScore.missing_skills || matchScore.analysis?.missing_skills,
      matched_qualifications: matchScore.matched_qualifications || matchScore.analysis?.matched_qualifications,
      missing_qualifications: matchScore.missing_qualifications || matchScore.analysis?.missing_qualifications,
      
      // Include full analysis object if present (for complete debugging)
      analysis: matchScore.analysis,
      
      analyzed_at: matchScore.created_at
    } : null
  };

  const formattedJson = JSON.stringify(debugData, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedJson);
      setCopied(true);
      toast.success('Debug data copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy debug data');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Copy Button */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>Match Debug Data</CardTitle>
              <CardDescription>
                Raw data for LLM analysis. Copy this entire block and paste it into your AI judge.
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="shrink-0"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy All
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Data Summary */}
            <div className="grid grid-cols-4 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <div className="text-sm font-medium text-muted-foreground">Job</div>
                <div className="text-lg font-semibold">{job?.title || 'Not loaded'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">CV Data</div>
                <div className="text-lg font-semibold">{cvData ? 'Loaded' : 'Not loaded'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">Match Score</div>
                <div className="text-lg font-semibold">
                  {matchScore ? `${matchScore.overall_score}%` : 'Not analyzed'}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">Matcher</div>
                <div className="text-lg font-semibold">
                  {matchScore ? (matchScore.matcher_version || matchScore.analysis?.matcher_version || 'v2.x') : 'N/A'}
                </div>
              </div>
            </div>

            {/* JSON Data Display */}
            <div className="relative">
              <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg overflow-x-auto text-xs font-mono max-h-[600px] overflow-y-auto">
                {formattedJson}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Component Breakdown */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Job Data */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Job Data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Title:</span> {job?.title}
            </div>
            <div>
              <span className="font-medium">Company:</span> {job?.company}
            </div>
            <div>
              <span className="font-medium">Requirements Matrix:</span>{' '}
              {job?.requirements_matrix ? (
                <span className="text-green-600">✓ Present</span>
              ) : (
                <span className="text-amber-600">✗ Missing</span>
              )}
            </div>
            {job?.requirements_matrix && (
              <>
                <div>
                  <span className="font-medium">Must-have:</span>{' '}
                  {job.requirements_matrix.must_have?.length || 0} requirements
                </div>
                <div>
                  <span className="font-medium">Nice-to-have:</span>{' '}
                  {job.requirements_matrix.nice_to_have?.length || 0} requirements
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* CV Data */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">CV Data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {cvData ? (
              <>
                <div>
                  <span className="font-medium">Name:</span> {cvData.name || 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Skills:</span>{' '}
                  {cvData.skills ? Object.keys(cvData.skills).length : 0} categories
                </div>
                <div>
                  <span className="font-medium">Experience:</span>{' '}
                  {cvData.experience?.length || 0} roles
                </div>
                <div>
                  <span className="font-medium">Education:</span>{' '}
                  {cvData.education?.length || 0} entries
                </div>
              </>
            ) : (
              <div className="text-muted-foreground">CV data not loaded</div>
            )}
          </CardContent>
        </Card>

        {/* Match Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Match Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {matchScore ? (
              <>
                <div>
                  <span className="font-medium">Overall:</span> {matchScore.overall_score}%
                </div>
                {matchScore.scoring_method && (
                  <div className="text-xs text-blue-600 font-medium">
                    {matchScore.scoring_method}
                  </div>
                )}
                {matchScore.deterministic_score !== undefined && (
                  <div>
                    <span className="font-medium">Deterministic:</span> {matchScore.deterministic_score}%
                  </div>
                )}
                {matchScore.fit_score !== undefined && (
                  <div>
                    <span className="font-medium">Fit Score:</span> {matchScore.fit_score}%
                  </div>
                )}
                {matchScore.ai_holistic_score !== undefined && (
                  <div>
                    <span className="font-medium">AI Holistic:</span> {matchScore.ai_holistic_score}%
                  </div>
                )}
                {matchScore.component_average !== undefined && (
                  <div>
                    <span className="font-medium">Component Avg:</span> {matchScore.component_average}%
                  </div>
                )}
                {matchScore.domain_fit && (
                  <div>
                    <span className="font-medium">Domain:</span>{' '}
                    <span className={
                      matchScore.domain_fit === 'SAME' ? 'text-green-600' :
                      matchScore.domain_fit === 'ADJACENT' ? 'text-yellow-600' :
                      'text-red-600'
                    }>
                      {matchScore.domain_fit}
                    </span>
                  </div>
                )}
                <div>
                  <span className="font-medium">Strengths:</span> {matchScore.strengths?.length || matchScore.analysis?.strengths?.length || 0}
                </div>
                <div>
                  <span className="font-medium">Gaps:</span> {matchScore.gaps?.length || matchScore.analysis?.gaps?.length || 0}
                </div>
                <div>
                  <span className="font-medium">Recommendations:</span> {matchScore.recommendations?.length || matchScore.analysis?.recommendations?.length || 0}
                </div>
              </>
            ) : (
              <div className="text-muted-foreground">Match not analyzed yet</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Instructions */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-base text-blue-900">How to Use This Data</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>1.</strong> Click "Copy All" above to copy the complete debug data
          </p>
          <p>
            <strong>2.</strong> Paste it into your AI judge (Claude, GPT-4, etc.)
          </p>
          <p>
            <strong>3.</strong> Ask the AI to evaluate the match quality and provide feedback
          </p>
          <p className="mt-4 p-3 bg-white rounded border border-blue-200">
            <strong>Example prompt:</strong><br />
            "Analyze this CV matcher output. Does the {matchScore?.overall_score}% score fairly represent 
            the candidate's fit? Are there any bugs in the matching logic? What improvements would you suggest?"
          </p>
        </CardContent>
      </Card>
    </div>
  );
}