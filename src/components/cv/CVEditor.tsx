import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Download, Target } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface CVEditorProps {
  content: string;
  onChange: (content: string) => void;
}

export function CVEditor({ content, onChange }: CVEditorProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border bg-card">
        <h3 className="font-semibold text-foreground">Tailored CV Export</h3>
        <p className="text-sm text-muted-foreground">Generate a tailored CV PDF for this job</p>
      </div>
      
      <ScrollArea className="flex-1">
        <div className="flex items-center justify-center min-h-full p-8">
          <Card className="max-w-md p-8 text-center space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-primary to-accent blur-2xl opacity-20"></div>
                <div className="relative bg-gradient-to-br from-primary to-accent p-4 rounded-2xl">
                  <FileText className="h-12 w-12 text-white" />
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-2xl font-bold text-foreground">
                Export Tailored CV
              </h3>
              <p className="text-muted-foreground">
                Generate a customized CV PDF for this specific job
              </p>
            </div>
            
            <div className="space-y-3 text-sm text-muted-foreground pt-4">
              <div className="flex items-start gap-3 text-left">
                <Target className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">Match Analysis First</p>
                  <p className="text-xs">Go to the "Match Analysis" tab to analyze how well your CV matches this job</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 text-left">
                <Download className="h-5 w-5 text-accent shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">Export PDF</p>
                  <p className="text-xs">Once analyzed, click "Export PDF" at the top to generate your tailored CV</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 text-left">
                <FileText className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">AI-Optimized</p>
                  <p className="text-xs">The PDF will highlight your most relevant skills and experience for this position</p>
                </div>
              </div>
            </div>
            
            <div className="pt-4">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => {
                  // This will trigger the parent component to switch tabs
                  const tabTrigger = document.querySelector('[value="score"]') as HTMLElement;
                  if (tabTrigger) tabTrigger.click();
                }}
              >
                <Target className="h-4 w-4 mr-2" />
                Go to Match Analysis
              </Button>
            </div>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
