import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Sparkles } from 'lucide-react';
import { ChatMessage } from '@/lib/mockData';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
}

export function ChatPanel({ messages, onSendMessage }: ChatPanelProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full border-l border-border bg-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-accent-light">
            <Sparkles className="h-4 w-4 text-accent" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">AI Assistant</h3>
            <p className="text-xs text-muted-foreground">Ask for CV improvements</p>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs mt-1 opacity-70">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask AI to improve your CV..."
            className="min-h-[80px] resize-none"
          />
          <Button onClick={handleSend} size="icon" className="h-20 w-12">
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setInput('Make the summary more impactful')}
            className="text-xs"
          >
            Enhance summary
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setInput('Add more relevant keywords')}
            className="text-xs"
          >
            Add keywords
          </Button>
        </div>
      </div>
    </div>
  );
}
