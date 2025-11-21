import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';

interface CVEditorProps {
  content: string;
  onChange: (content: string) => void;
}

export function CVEditor({ content, onChange }: CVEditorProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border bg-card">
        <h3 className="font-semibold text-foreground">Tailored CV</h3>
        <p className="text-sm text-muted-foreground">Edit your tailored resume</p>
      </div>
      
      <ScrollArea className="flex-1 p-6">
        <Textarea
          value={content}
          onChange={(e) => onChange(e.target.value)}
          className="min-h-[800px] font-mono text-sm leading-relaxed resize-none border-0 focus-visible:ring-0"
          placeholder="Your tailored CV will appear here..."
        />
      </ScrollArea>
    </div>
  );
}
