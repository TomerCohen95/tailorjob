import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Clock, User, Sparkles } from 'lucide-react';
import { Revision } from '@/lib/mockData';

interface RevisionHistoryProps {
  revisions: Revision[];
  onSelectRevision: (revision: Revision) => void;
}

export function RevisionHistory({ revisions, onSelectRevision }: RevisionHistoryProps) {
  return (
    <div className="w-80 border-l border-border bg-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-foreground">Revision History</h3>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {revisions.length} saved versions
        </p>
      </div>

      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="p-4 space-y-2">
          {revisions.map((revision, index) => (
            <Button
              key={revision.id}
              variant="ghost"
              className="w-full justify-start h-auto p-3"
              onClick={() => onSelectRevision(revision)}
            >
              <div className="flex items-start gap-3 w-full">
                <div className={`p-2 rounded-lg ${
                  revision.type === 'ai' ? 'bg-accent-light' : 'bg-primary-light'
                }`}>
                  {revision.type === 'ai' ? (
                    <Sparkles className="h-4 w-4 text-accent" />
                  ) : (
                    <User className="h-4 w-4 text-primary" />
                  )}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-foreground">
                    {revision.content}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(revision.timestamp).toLocaleString()}
                  </p>
                  {index === 0 && (
                    <span className="inline-block mt-1 text-xs bg-primary-light text-primary px-2 py-0.5 rounded">
                      Current
                    </span>
                  )}
                </div>
              </div>
            </Button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
