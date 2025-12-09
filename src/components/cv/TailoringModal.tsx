import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ActionCard, ActionSuggestion } from './ActionCard';
import { Loader2, Download, Sparkles } from 'lucide-react';
import { tailorAPI } from '@/lib/api';
import { toast } from 'sonner';

interface TailoringModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  matchAnalysis: any;
  cvText: string;
  cvId: string;
  jobId: string;
  onSuggestionsChange?: (suggestions: ActionSuggestion[]) => void;
}

export function TailoringModal({
  open,
  onOpenChange,
  matchAnalysis,
  cvText,
  cvId,
  jobId,
  onSuggestionsChange,
}: TailoringModalProps) {
  const [suggestions, setSuggestions] = useState<ActionSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  // Parse recommendations when modal opens
  useEffect(() => {
    if (open && matchAnalysis) {
      parseRecommendations();
    }
  }, [open, matchAnalysis]);

  const parseRecommendations = async () => {
    setLoading(true);
    try {
      const result = await tailorAPI.parseRecommendations(matchAnalysis);
      setSuggestions(
        result.suggestions.map((s: any) => ({
          ...s,
          status: 'pending',
        }))
      );
    } catch (error: any) {
      console.error('Failed to parse recommendations:', error);
      toast.error('Failed to load suggestions: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = (actionId: string) => {
    setSuggestions((prev) => {
      const updated = prev.map((s) => (s.id === actionId ? { ...s, status: 'accepted' as const } : s));
      // Notify parent of accepted suggestions
      if (onSuggestionsChange) {
        const accepted = updated.filter((s) => s.status === 'accepted');
        onSuggestionsChange(accepted);
      }
      return updated;
    });
  };

  const handleReject = (actionId: string) => {
    setSuggestions((prev) => {
      const updated = prev.map((s) => (s.id === actionId ? { ...s, status: 'rejected' as const } : s));
      // Notify parent of accepted suggestions
      if (onSuggestionsChange) {
        const accepted = updated.filter((s) => s.status === 'accepted');
        onSuggestionsChange(accepted);
      }
      return updated;
    });
  };

  const handleAcceptAll = () => {
    setSuggestions((prev) => {
      const updated = prev.map((s) => (s.status === 'pending' ? { ...s, status: 'accepted' as const } : s));
      // Notify parent of accepted suggestions
      if (onSuggestionsChange) {
        const accepted = updated.filter((s) => s.status === 'accepted');
        onSuggestionsChange(accepted);
      }
      return updated;
    });
  };

  const handleExportPDF = async () => {
    setExportingPDF(true);
    try {
      // Get accepted suggestions
      const acceptedSuggestions = suggestions.filter((s) => s.status === 'accepted');
      
      if (acceptedSuggestions.length === 0) {
        toast.error('Please accept at least one suggestion before exporting');
        return;
      }

      // Generate PDF with tailored content
      const pdfBlob = await tailorAPI.generatePDF(cvText, matchAnalysis, 'modern');
      
      // Download the PDF
      const url = window.URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tailored-cv-${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Tailored CV exported successfully!');
      onOpenChange(false);
    } catch (error: any) {
      console.error('Failed to export PDF:', error);
      toast.error('Failed to export PDF: ' + (error.message || 'Unknown error'));
    } finally {
      setExportingPDF(false);
    }
  };

  const filteredSuggestions = suggestions.filter((s) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'pending') return s.status === 'pending';
    if (activeTab === 'accepted') return s.status === 'accepted';
    return false;
  });

  const stats = {
    total: suggestions.length,
    pending: suggestions.filter((s) => s.status === 'pending').length,
    accepted: suggestions.filter((s) => s.status === 'accepted').length,
    high: suggestions.filter((s) => s.impact === 'high').length,
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0 gap-0">
        <DialogHeader className="px-6 pt-6 pb-4">
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2 text-2xl">
                <Sparkles className="h-6 w-6 text-purple-600" />
                Tailor Your CV
              </DialogTitle>
              <DialogDescription className="mt-2">
                Review AI-powered suggestions to improve your match with this job
              </DialogDescription>
            </div>
            {!loading && stats.total > 0 && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAcceptAll}
                  disabled={stats.pending === 0}
                >
                  Accept All {stats.high > 0 && `High Impact (${stats.high})`}
                </Button>
                <Button
                  onClick={handleExportPDF}
                  disabled={stats.accepted === 0 || exportingPDF}
                  size="sm"
                >
                  {exportingPDF ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Export PDF ({stats.accepted})
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        </DialogHeader>

        <div className="px-6 pb-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
              <span className="ml-3 text-gray-600">Analyzing recommendations...</span>
            </div>
          ) : suggestions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No suggestions available</p>
              <p className="text-sm text-gray-500 mt-2">
                This might mean your CV already matches the job requirements well!
              </p>
            </div>
          ) : (
            <>
              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <Sparkles className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      {stats.total} suggestions found • {stats.high} high impact
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      Review each suggestion and accept the ones you want to apply to your CV
                    </p>
                  </div>
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="w-full grid grid-cols-3 mb-4">
                  <TabsTrigger value="all">
                    All ({stats.total})
                  </TabsTrigger>
                  <TabsTrigger value="pending">
                    Pending ({stats.pending})
                  </TabsTrigger>
                  <TabsTrigger value="accepted">
                    Accepted ({stats.accepted})
                  </TabsTrigger>
                </TabsList>

                <TabsContent value={activeTab} className="mt-0">
                  <ScrollArea className="h-[50vh]">
                    <div className="space-y-3 pr-4">
                      {filteredSuggestions.map((suggestion) => (
                        <ActionCard
                          key={suggestion.id}
                          action={suggestion}
                          onAccept={handleAccept}
                          onReject={handleReject}
                        />
                      ))}
                      {filteredSuggestions.length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          No {activeTab} suggestions
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}