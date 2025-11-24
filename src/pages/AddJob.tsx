import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { ArrowRight, Sparkles, Link as LinkIcon, Loader2, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { jobsAPI } from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function AddJob() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: ''
  });
  const [jobUrl, setJobUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);
  const [scrapedData, setScrapedData] = useState<any>(null);
  const [urlError, setUrlError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title || !formData.company || !formData.description) {
      toast.error('Please fill in all fields');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const job = await jobsAPI.create({
        title: formData.title,
        company: formData.company,
        description: formData.description
      });
      
      toast.success('Job saved successfully!', {
        description: `${job.title} at ${job.company}`
      });
      
      // Navigate to tailor page with the actual job ID
      navigate(`/jobs/${job.id}/tailor`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save job';
      toast.error('Save failed', {
        description: message
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFetchFromUrl = async () => {
    if (!jobUrl.trim()) {
      toast.error('Please enter a job URL');
      return;
    }

    // Validate URL format
    try {
      new URL(jobUrl);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    setIsFetchingUrl(true);
    setUrlError(null); // Clear previous errors

    try {
      toast.info('Fetching job details...', {
        description: 'Using AI to extract information from the page'
      });
      
      const jobDetails = await jobsAPI.scrapeFromUrl(jobUrl);
      
      // Parse description if it's JSON
      let parsedDescription = jobDetails.description;
      if (typeof jobDetails.description === 'string') {
        try {
          parsedDescription = JSON.parse(jobDetails.description);
        } catch {
          // If not JSON, keep as string
        }
      }
      
      // Store scraped data for display
      setScrapedData({
        title: jobDetails.title || '',
        company: jobDetails.company || '',
        parsedDescription,
        id: jobDetails.id // Store the saved job ID
      });
      
      // Convert structured data to plain text for storage
      const descriptionText = typeof parsedDescription === 'object'
        ? formatStructuredDescription(parsedDescription)
        : parsedDescription;
      
      setFormData({
        title: jobDetails.title || '',
        company: jobDetails.company || '',
        description: descriptionText
      });
      
      toast.success('Job saved successfully!', {
        description: `${jobDetails.title} at ${jobDetails.company} - Click "Continue to Tailor" below`
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch job details';
      
      // Set error state for visible alert
      setUrlError(message);
      
      // Also show toast for immediate feedback
      toast.error('❌ Invalid Job URL', {
        description: message,
        duration: 6000,
      });
    } finally {
      setIsFetchingUrl(false);
    }
  };

  const formatStructuredDescription = (data: any): string => {
    let text = '';
    
    if (data['About the Role']) {
      text += `ABOUT THE ROLE:\n${data['About the Role']}\n\n`;
    }
    
    if (data['Key Responsibilities']) {
      text += 'KEY RESPONSIBILITIES:\n';
      data['Key Responsibilities'].forEach((item: string) => {
        text += `• ${item}\n`;
      });
      text += '\n';
    }
    
    if (data['Required Qualifications']) {
      text += 'REQUIRED QUALIFICATIONS:\n';
      data['Required Qualifications'].forEach((item: string) => {
        text += `• ${item}\n`;
      });
      text += '\n';
    }
    
    if (data['Preferred Qualifications']) {
      text += 'PREFERRED QUALIFICATIONS:\n';
      data['Preferred Qualifications'].forEach((item: string) => {
        text += `• ${item}\n`;
      });
      text += '\n';
    }
    
    if (data['Technical Skills']) {
      text += 'TECHNICAL SKILLS:\n';
      data['Technical Skills'].forEach((item: string) => {
        text += `• ${item}\n`;
      });
    }
    
    return text;
  };

  const renderStructuredData = (data: any) => {
    if (!data || typeof data !== 'object') return null;
    
    return (
      <div className="space-y-6">
        {data['About the Role'] && (
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2">About the Role</h3>
            <p className="text-muted-foreground">{data['About the Role']}</p>
          </div>
        )}
        
        {data['Key Responsibilities'] && Array.isArray(data['Key Responsibilities']) && (
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-3">Key Responsibilities</h3>
            <ul className="space-y-2">
              {data['Key Responsibilities'].map((item: string, i: number) => (
                <li key={i} className="flex gap-2 text-muted-foreground">
                  <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data['Required Qualifications'] && Array.isArray(data['Required Qualifications']) && (
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
              Required Qualifications
              <Badge variant="destructive">Must Have</Badge>
            </h3>
            <ul className="space-y-2">
              {data['Required Qualifications'].map((item: string, i: number) => (
                <li key={i} className="flex gap-2 text-muted-foreground">
                  <CheckCircle2 className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data['Preferred Qualifications'] && Array.isArray(data['Preferred Qualifications']) && (
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
              Preferred Qualifications
              <Badge variant="secondary">Nice to Have</Badge>
            </h3>
            <ul className="space-y-2">
              {data['Preferred Qualifications'].map((item: string, i: number) => (
                <li key={i} className="flex gap-2 text-muted-foreground">
                  <CheckCircle2 className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data['Technical Skills'] && Array.isArray(data['Technical Skills']) && (
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-3">Technical Skills</h3>
            <div className="flex flex-wrap gap-2">
              {data['Technical Skills'].map((item: string, i: number) => (
                <Badge key={i} variant="outline" className="bg-primary-light">
                  {item}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Add Job Description</h1>
            <p className="text-muted-foreground">
              Enter the job details to tailor your CV
            </p>
          </div>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Job Details</CardTitle>
              <CardDescription>
                Add a job by pasting details manually or from a URL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="manual" className="mb-6">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="manual">Manual Entry</TabsTrigger>
                  <TabsTrigger value="url">From URL</TabsTrigger>
                </TabsList>
                
                <TabsContent value="url" className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="jobUrl">Job Posting URL</Label>
                    <div className="flex gap-2">
                      <Input
                        id="jobUrl"
                        type="url"
                        placeholder="https://example.com/jobs/senior-developer"
                        value={jobUrl}
                        onChange={(e) => setJobUrl(e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        onClick={handleFetchFromUrl}
                        disabled={isFetchingUrl}
                        className="bg-gradient-to-r from-primary to-accent"
                      >
                        {isFetchingUrl ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Fetching...
                          </>
                        ) : (
                          <>
                            <LinkIcon className="mr-2 h-4 w-4" />
                            Fetch
                          </>
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Paste a link to automatically extract job details
                    </p>
                  </div>

                  {urlError && (
                    <Alert variant="destructive" className="border-2 border-red-500">
                      <XCircle className="h-5 w-5" />
                      <AlertTitle className="text-lg font-semibold">Invalid Job URL</AlertTitle>
                      <AlertDescription className="mt-2 text-base">
                        <p className="mb-3">{urlError}</p>
                        <div className="bg-red-50 dark:bg-red-950/20 p-3 rounded-md">
                          <p className="text-sm font-medium mb-2">💡 For LinkedIn jobs:</p>
                          <ol className="text-sm space-y-1 list-decimal list-inside">
                            <li>Open the job posting in LinkedIn</li>
                            <li>Click the job to view its full details</li>
                            <li>Copy the URL (should look like: <code className="text-xs bg-red-100 dark:bg-red-900/30 px-1 py-0.5 rounded">linkedin.com/jobs/view/[job-id]</code>)</li>
                            <li>Paste it here</li>
                          </ol>
                        </div>
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="p-4 bg-muted rounded-lg border">
                    <p className="text-sm text-muted-foreground">
                      Supported platforms: LinkedIn, Indeed, Glassdoor, and more
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="manual" className="mt-4">
                  <p className="text-sm text-muted-foreground mb-4">
                    Manually enter the job details below
                  </p>
                </TabsContent>
              </Tabs>

              {scrapedData ? (
                <div className="space-y-6">
                  <div className="p-6 bg-muted rounded-lg space-y-4">
                    <div>
                      <Label className="text-sm text-muted-foreground">Job Title</Label>
                      <p className="text-xl font-bold text-foreground">{scrapedData.title}</p>
                    </div>
                    <div>
                      <Label className="text-sm text-muted-foreground">Company</Label>
                      <p className="text-lg font-semibold text-foreground">{scrapedData.company}</p>
                    </div>
                  </div>
                  
                  <div className="p-6 border rounded-lg">
                    {renderStructuredData(scrapedData.parsedDescription)}
                  </div>
                  
                  <div className="flex gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setScrapedData(null);
                        setJobUrl('');
                        setFormData({ title: '', company: '', description: '' });
                      }}
                      className="flex-1"
                    >
                      Try Another URL
                    </Button>
                    <Button
                      onClick={() => navigate(`/jobs/${scrapedData.id}/tailor`)}
                      className="flex-1 bg-gradient-to-r from-primary to-accent hover:opacity-90"
                    >
                      <Sparkles className="mr-2 h-4 w-4" />
                      Continue to Tailor
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="title">Job Title *</Label>
                  <Input
                    id="title"
                    placeholder="e.g. Senior React Developer"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company">Company *</Label>
                  <Input
                    id="company"
                    placeholder="e.g. Acme Corp"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Job Description *</Label>
                  <Textarea
                    id="description"
                    placeholder="Paste the full job description here..."
                    className="min-h-[300px] font-mono text-sm"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">
                    Include responsibilities, requirements, and any other relevant information
                  </p>
                </div>

                <div className="p-4 bg-accent-light rounded-lg border border-accent/20">
                  <div className="flex items-center gap-2 text-accent mb-2">
                    <Sparkles className="h-5 w-5" />
                    <span className="font-medium">AI will analyze this</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Our AI will match your experience to this job description and create a tailored CV
                  </p>
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/dashboard')}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 bg-gradient-to-r from-primary to-accent hover:opacity-90"
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    {isSubmitting ? 'Saving...' : 'Tailor My CV'}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
                </form>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
