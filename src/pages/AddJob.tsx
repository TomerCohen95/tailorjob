import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { ArrowRight, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export default function AddJob() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title || !formData.company || !formData.description) {
      toast.error('Please fill in all fields');
      return;
    }

    // Mock save delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    toast.success('Job saved successfully!');
    navigate('/jobs/1/tailor'); // Navigate to tailor page with mock job ID
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
                Paste the job description you're applying for
              </CardDescription>
            </CardHeader>
            <CardContent>
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
                    className="flex-1 bg-gradient-to-r from-primary to-accent hover:opacity-90"
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    Tailor My CV
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
