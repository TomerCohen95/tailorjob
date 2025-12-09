import { Card } from "@/components/ui/card";
import { Minus, Plus } from "lucide-react";

interface DiffViewProps {
  before: string;
  after: string;
  title?: string;
}

export function DiffView({ before, after, title }: DiffViewProps) {
  return (
    <Card className="p-4 bg-gray-50">
      {title && (
        <div className="mb-3 pb-2 border-b border-gray-200">
          <h4 className="font-medium text-sm text-gray-700">{title}</h4>
        </div>
      )}
      
      <div className="space-y-2 font-mono text-xs">
        {/* Before (removed) */}
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded p-2">
          <Minus className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-xs text-red-600 font-semibold mb-1">Before:</div>
            <p className="text-red-800 leading-relaxed whitespace-pre-wrap font-sans">
              {before}
            </p>
          </div>
        </div>

        {/* After (added) */}
        <div className="flex items-start gap-2 bg-green-50 border border-green-200 rounded p-2">
          <Plus className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-xs text-green-600 font-semibold mb-1">After:</div>
            <p className="text-green-800 leading-relaxed whitespace-pre-wrap font-sans">
              {after}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}