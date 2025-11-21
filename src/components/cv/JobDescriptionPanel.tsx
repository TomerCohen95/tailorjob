import { ScrollArea } from '@/components/ui/scroll-area';
import { Briefcase } from 'lucide-react';
import { Job } from '@/lib/mockData';

interface JobDescriptionPanelProps {
  job: Job;
}

export function JobDescriptionPanel({ job }: JobDescriptionPanelProps) {
  return (
    <div className="flex flex-col h-full border-r border-border bg-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-2 rounded-lg bg-primary-light">
            <Briefcase className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{job.title}</h3>
            <p className="text-sm text-muted-foreground">{job.company}</p>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1 p-6">
        <div className="prose prose-sm max-w-none">
          <pre className="whitespace-pre-wrap font-sans text-sm text-foreground leading-relaxed">
            {job.description}
          </pre>
        </div>
      </ScrollArea>
    </div>
  );
}
