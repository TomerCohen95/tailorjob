import { Badge } from '@/components/ui/badge';
import { Target, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MatchScoreBadgeProps {
  score?: number;
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showLabel?: boolean;
}

export function MatchScoreBadge({ 
  score, 
  loading = false, 
  size = 'md',
  showIcon = true,
  showLabel = true
}: MatchScoreBadgeProps) {
  if (loading) {
    return (
      <Badge variant="outline" className="gap-1">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span className="text-xs">Analyzing...</span>
      </Badge>
    );
  }

  if (score === undefined) {
    return null;
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 60) return 'from-blue-500 to-cyan-600';
    if (score >= 40) return 'from-yellow-500 to-orange-500';
    return 'from-red-500 to-rose-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Low';
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-3 py-1 gap-1.5',
    lg: 'text-base px-4 py-1.5 gap-2'
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
    lg: 'h-4 w-4'
  };

  return (
    <div className={cn(
      "inline-flex items-center rounded-full font-semibold",
      "bg-gradient-to-r text-white shadow-md transition-all hover:shadow-lg",
      getScoreColor(score),
      sizeClasses[size]
    )}>
      {showIcon && <Target className={iconSizes[size]} />}
      <span>{score}%</span>
      {showLabel && size !== 'sm' && (
        <span className="text-xs opacity-90 font-normal">
          {getScoreLabel(score)}
        </span>
      )}
    </div>
  );
}