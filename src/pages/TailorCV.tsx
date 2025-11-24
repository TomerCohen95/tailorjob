import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Navigation } from '@/components/layout/Navigation';
import { JobDescriptionPanel } from '@/components/cv/JobDescriptionPanel';
import { CVEditor } from '@/components/cv/CVEditor';
import { ChatPanel } from '@/components/cv/ChatPanel';
import { RevisionHistory } from '@/components/cv/RevisionHistory';
import { Save, Download, History, Loader2 } from 'lucide-react';
import { mockTailoredCV, mockChatMessages, mockRevisions, ChatMessage, Revision } from '@/lib/mockData';
import { toast } from 'sonner';
import { jobsAPI, type Job } from '@/lib/api';

export default function TailorCV() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [cvContent, setCvContent] = useState(mockTailoredCV);
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatMessages);
  const [revisions, setRevisions] = useState<Revision[]>(mockRevisions);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (!id) {
      toast.error('No job ID provided');
      navigate('/dashboard');
      return;
    }

    loadJob();
  }, [id, navigate]);

  async function loadJob() {
    try {
      setLoading(true);
      const jobData = await jobsAPI.get(id!);
      setJob(jobData);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load job';
      console.error('Failed to load job:', error);
      toast.error(message);
      // Don't auto-redirect, let user see the error
      setJob(null);
    } finally {
      setLoading(false);
    }
  }

  const handleSendMessage = (message: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages([...messages, userMessage]);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I've analyzed your request. Here are some suggestions:\n\n1. Emphasize leadership experience in the summary\n2. Add more specific metrics and achievements\n3. Highlight relevant technologies from the job description\n\nWould you like me to apply these changes?",
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
    }, 1000);
  };

  const handleSaveRevision = () => {
    const newRevision: Revision = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      type: 'user',
      content: 'Manual save'
    };
    setRevisions([newRevision, ...revisions]);
    toast.success('Revision saved!');
  };

  const handleExportPDF = () => {
    toast.success('PDF export started! (This is a mock action)');
  };

  const handleSelectRevision = (revision: Revision) => {
    toast.info(`Loading revision: ${revision.content}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <p>Loading job details...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <p className="text-muted-foreground">Failed to load job details</p>
            <Button onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      {/* Action Bar */}
      <div className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-foreground">{job.title}</h2>
              <p className="text-sm text-muted-foreground">{job.company}</p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowHistory(!showHistory)}
              >
                <History className="h-4 w-4 mr-2" />
                History
              </Button>
              <Button variant="outline" size="sm" onClick={handleSaveRevision}>
                <Save className="h-4 w-4 mr-2" />
                Save Revision
              </Button>
              <Button
                size="sm"
                className="bg-gradient-to-r from-primary to-accent hover:opacity-90"
                onClick={handleExportPDF}
              >
                <Download className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Editor Layout */}
      <div className="flex h-[calc(100vh-180px)]">
        {/* Job Description Panel - Left */}
        <div className="w-80 hidden lg:block">
          <JobDescriptionPanel job={job} />
        </div>

        {/* CV Editor - Center */}
        <div className="flex-1 border-r border-border">
          <CVEditor content={cvContent} onChange={setCvContent} />
        </div>

        {/* Chat Panel - Right */}
        <div className="w-96 hidden xl:block">
          <ChatPanel messages={messages} onSendMessage={handleSendMessage} />
        </div>

        {/* Revision History - Slide-in Panel */}
        {showHistory && (
          <div className="fixed right-0 top-[180px] bottom-0 z-50 shadow-2xl animate-slide-in">
            <RevisionHistory
              revisions={revisions}
              onSelectRevision={handleSelectRevision}
            />
          </div>
        )}
      </div>

      {/* Mobile Warning */}
      <div className="lg:hidden p-4 bg-accent-light border-t border-accent/20">
        <p className="text-sm text-center text-muted-foreground">
          For the best experience, use a larger screen to access all editor features
        </p>
      </div>
    </div>
  );
}
