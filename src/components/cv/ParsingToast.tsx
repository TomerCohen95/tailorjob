import { useCVParsing } from '@/contexts/CVParsingContext';
import { Card } from '@/components/ui/card';
import { Loader2, Minimize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

export function ParsingToast() {
  const { parsingCVs } = useCVParsing();
  const [minimized, setMinimized] = useState(false);
  
  // Get the first parsing CV (in case of multiple)
  const parsingArray = Array.from(parsingCVs.values());
  const activeParsing = parsingArray.find(cv => cv.status === 'parsing' || cv.status === 'uploading');
  
  if (!activeParsing) return null;
  
  const elapsed = Math.floor((Date.now() - activeParsing.startTime.getTime()) / 1000);
  
  if (minimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMinimized(false)}
          className="shadow-lg bg-background hover:bg-accent"
        >
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
          Parsing CV...
        </Button>
      </div>
    );
  }
  
  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 max-w-[calc(100vw-2rem)]">
      <Card className="shadow-lg border-primary/20">
        <div className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <div>
                <h3 className="font-semibold text-sm">Parsing Your CV</h3>
                <p className="text-xs text-muted-foreground truncate max-w-[250px]">
                  {activeParsing.filename}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => setMinimized(true)}
            >
              <Minimize2 className="h-3 w-3" />
            </Button>
          </div>
          
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">
              This usually takes 15-30 seconds
            </p>
            <p className="text-xs text-muted-foreground">
              Elapsed: {elapsed}s
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}