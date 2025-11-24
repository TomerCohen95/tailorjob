import { ScrollArea } from '@/components/ui/scroll-area';
import { Briefcase, CheckCircle2 } from 'lucide-react';
import { Job } from '@/lib/api';
import { Badge } from '@/components/ui/badge';

interface JobDescriptionPanelProps {
  job: Job;
}

interface StructuredDescription {
  'About the Role'?: string;
  'Key Responsibilities'?: string[];
  'Required Qualifications'?: string[];
  'Preferred Qualifications'?: string[];
  'Technical Skills'?: string[];
}

export function JobDescriptionPanel({ job }: JobDescriptionPanelProps) {
  // Try to parse description as JSON
  let parsedDescription: StructuredDescription | null = null;
  try {
    parsedDescription = JSON.parse(job.description);
  } catch {
    // If not JSON, keep as null and show plain text
  }

  const renderStructuredDescription = (data: StructuredDescription) => (
    <div className="space-y-6">
      {data['About the Role'] && (
        <div>
          <h3 className="text-base font-semibold text-foreground mb-2">About the Role</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">{data['About the Role']}</p>
        </div>
      )}
      
      {data['Key Responsibilities'] && Array.isArray(data['Key Responsibilities']) && (
        <div>
          <h3 className="text-base font-semibold text-foreground mb-3">Key Responsibilities</h3>
          <ul className="space-y-2">
            {data['Key Responsibilities'].map((item: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {data['Required Qualifications'] && Array.isArray(data['Required Qualifications']) && (
        <div>
          <h3 className="text-base font-semibold text-foreground mb-3 flex items-center gap-2">
            Required Qualifications
            <Badge variant="destructive" className="text-xs">Must Have</Badge>
          </h3>
          <ul className="space-y-2">
            {data['Required Qualifications'].map((item: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {data['Preferred Qualifications'] && Array.isArray(data['Preferred Qualifications']) && (
        <div>
          <h3 className="text-base font-semibold text-foreground mb-3 flex items-center gap-2">
            Preferred Qualifications
            <Badge variant="secondary" className="text-xs">Nice to Have</Badge>
          </h3>
          <ul className="space-y-2">
            {data['Preferred Qualifications'].map((item: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {data['Technical Skills'] && Array.isArray(data['Technical Skills']) && (
        <div>
          <h3 className="text-base font-semibold text-foreground mb-3">Technical Skills</h3>
          <div className="flex flex-wrap gap-2">
            {data['Technical Skills'].map((item: string, i: number) => (
              <Badge key={i} variant="outline" className="bg-primary/10 text-xs">
                {item}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );

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
        {parsedDescription ? (
          renderStructuredDescription(parsedDescription)
        ) : (
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap font-sans text-sm text-foreground leading-relaxed">
              {job.description}
            </pre>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
