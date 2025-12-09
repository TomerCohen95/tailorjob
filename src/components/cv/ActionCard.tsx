import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, ChevronDown, ChevronUp, Lightbulb } from "lucide-react";
import { useState } from "react";

export interface ActionSuggestion {
  id: string;
  type: 'add_metric' | 'highlight_skill' | 'enhance_experience' | 'add_to_summary' | 'emphasize_achievement' | 'expand_description';
  section: string;
  suggestion: string;
  reasoning: string;
  impact: 'high' | 'medium' | 'low';
  original_text: string;
  target?: string;
  examples?: string[];
  status?: 'pending' | 'accepted' | 'rejected';
}

interface ActionCardProps {
  action: ActionSuggestion;
  onAccept: (actionId: string) => void;
  onReject: (actionId: string) => void;
}

const impactColors = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
};

const impactLabels = {
  high: '🎯 High Impact',
  medium: '⭐ Medium Impact',
  low: '💡 Low Impact',
};

const typeLabels = {
  add_metric: 'Add Metric',
  highlight_skill: 'Highlight Skill',
  enhance_experience: 'Enhance Experience',
  add_to_summary: 'Add to Summary',
  emphasize_achievement: 'Emphasize Achievement',
  expand_description: 'Expand Description',
};

export function ActionCard({ action, onAccept, onReject }: ActionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localStatus, setLocalStatus] = useState<'pending' | 'accepted' | 'rejected'>(
    action.status || 'pending'
  );

  const handleAccept = () => {
    setLocalStatus('accepted');
    onAccept(action.id);
  };

  const handleReject = () => {
    setLocalStatus('rejected');
    onReject(action.id);
  };

  if (localStatus === 'rejected') {
    return (
      <Card className="opacity-50 border-gray-200">
        <CardContent className="pt-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-gray-400" />
            <span className="text-sm text-gray-500">Suggestion skipped</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLocalStatus('pending')}
          >
            Undo
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (localStatus === 'accepted') {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span className="text-sm text-green-700 font-medium">Applied to CV</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLocalStatus('pending')}
          >
            Undo
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className={impactColors[action.impact]}>
                {impactLabels[action.impact]}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {typeLabels[action.type]}
              </Badge>
            </div>
            <CardTitle className="text-base">
              {action.section.charAt(0).toUpperCase() + action.section.slice(1)} Section
            </CardTitle>
            {action.target && (
              <CardDescription className="text-sm mt-1">
                Target: <span className="font-medium">{action.target}</span>
              </CardDescription>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        <div className="bg-blue-50 border border-blue-100 rounded-md p-3">
          <p className="text-sm text-blue-900 font-medium">{action.suggestion}</p>
        </div>

        {action.examples && action.examples.length > 0 && (
          <div className="bg-purple-50 border border-purple-100 rounded-md p-3 space-y-1">
            <p className="text-xs text-purple-700 font-medium mb-1">Examples:</p>
            {action.examples.map((example, idx) => (
              <p key={idx} className="text-sm text-purple-900 italic">
                "{example}"
              </p>
            ))}
          </div>
        )}

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          <Lightbulb className="h-4 w-4" />
          <span className="font-medium">Why this helps</span>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>

        {isExpanded && (
          <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
            <p className="text-sm text-gray-700">{action.reasoning}</p>
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <Button
            onClick={handleAccept}
            className="flex-1 bg-green-600 hover:bg-green-700"
            size="sm"
          >
            <CheckCircle2 className="h-4 w-4 mr-1" />
            Apply
          </Button>
          <Button
            onClick={handleReject}
            variant="outline"
            className="flex-1"
            size="sm"
          >
            <XCircle className="h-4 w-4 mr-1" />
            Skip
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}