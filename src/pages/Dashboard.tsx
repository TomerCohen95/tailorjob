import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { FileText, Plus, Briefcase, Upload, AlertCircle } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { cvAPI, jobsAPI, type CV, type Job } from '@/lib/api';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function Dashboard() {
  const navigate = useNavigate();
  const [cvs, setCVs] = useState<CV[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is logged in
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        navigate('/login');
      } else {
        loadData();
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (!session) {
        navigate('/login');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      
      // Load CVs and jobs in parallel
      const [cvsData, jobsData] = await Promise.all([
        cvAPI.list(),
        jobsAPI.list()
      ]);
      
      setCVs(cvsData);
      setJobs(jobsData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load data';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  const latestCV = cvs[0]; // Most recent CV

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
          <p className="text-muted-foreground">Manage your CVs and job applications</p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="border-2 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-2 rounded-lg bg-primary-light">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <CardTitle>Your CV</CardTitle>
              </div>
              <CardDescription>
                {latestCV
                  ? `Last uploaded: ${new Date(latestCV.created_at).toLocaleDateString()}`
                  : 'No CV uploaded yet'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {latestCV ? (
                <>
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="font-medium text-foreground">{latestCV.filename}</p>
                    <p className="text-sm text-muted-foreground">
                      {(latestCV.file_size / 1024).toFixed(0)} KB • {latestCV.status}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link to="/cv-preview" className="flex-1">
                      <Button variant="outline" className="w-full">View Parsed CV</Button>
                    </Link>
                    <Link to="/upload-cv" className="flex-1">
                      <Button className="w-full bg-gradient-to-r from-primary to-accent">
                        <Upload className="mr-2 h-4 w-4" />
                        Upload New
                      </Button>
                    </Link>
                  </div>
                </>
              ) : (
                <Link to="/upload-cv">
                  <Button className="w-full bg-gradient-to-r from-primary to-accent">
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Your First CV
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-md hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-accent-light">
                    <Briefcase className="h-5 w-5 text-accent" />
                  </div>
                  <CardTitle>Your Jobs</CardTitle>
                </div>
                <Link to="/jobs/add">
                  <Button size="sm" className="bg-accent hover:bg-accent/90">
                    <Plus className="h-4 w-4 mr-1" />
                    Add Job
                  </Button>
                </Link>
              </div>
              <CardDescription>{jobs.length} jobs tracked</CardDescription>
            </CardHeader>
            <CardContent>
              {jobs.length > 0 ? (
                <div className="space-y-2">
                  {jobs.slice(0, 3).map((job) => (
                    <Link key={job.id} to={`/jobs/${job.id}/tailor`}>
                      <div className="p-4 border border-border rounded-lg hover:bg-muted transition-colors cursor-pointer">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-foreground">{job.title}</p>
                            <p className="text-sm text-muted-foreground">{job.company}</p>
                          </div>
                          <Button size="sm" variant="ghost">Tailor CV</Button>
                        </div>
                      </div>
                    </Link>
                  ))}
                  {jobs.length > 3 && (
                    <p className="text-sm text-muted-foreground text-center pt-2">
                      +{jobs.length - 3} more jobs
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-6">
                  <p className="text-muted-foreground mb-4">No jobs added yet</p>
                  <Link to="/jobs/add">
                    <Button variant="outline">Add Your First Job</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="bg-gradient-to-br from-primary-light to-accent-light border-0">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks to get you started</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-3 gap-4">
              <Link to="/upload-cv">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2 bg-card hover:bg-card/80">
                  <Upload className="h-6 w-6" />
                  <span>Upload CV</span>
                </Button>
              </Link>
              <Link to="/jobs/add">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2 bg-card hover:bg-card/80">
                  <Plus className="h-6 w-6" />
                  <span>Add Job</span>
                </Button>
              </Link>
              <Link to="/cv-preview">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2 bg-card hover:bg-card/80">
                  <FileText className="h-6 w-6" />
                  <span>View CV</span>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
