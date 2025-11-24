import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navigation } from '@/components/layout/Navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Briefcase, Calendar, Trash2, FileText, Loader2 } from 'lucide-react';
import { jobsAPI, cvAPI, matchingAPI } from '@/lib/api';
import { toast } from 'sonner';
import { MatchScoreBadge } from '@/components/cv/MatchScoreBadge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface Job {
  id: string;
  title: string;
  company: string;
  description: string;
  created_at: string;
}

export default function Jobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteJobId, setDeleteJobId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [jobScores, setJobScores] = useState<Map<string, number>>(new Map());
  const [primaryCvId, setPrimaryCvId] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
    loadPrimaryCv();
  }, []);

  useEffect(() => {
    if (jobs.length > 0 && primaryCvId) {
      loadJobScores();
    }
  }, [jobs, primaryCvId]);

  const loadJobs = async () => {
    try {
      const data = await jobsAPI.list();
      setJobs(data);
    } catch (error) {
      toast.error('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const loadPrimaryCv = async () => {
    try {
      const cvs = await cvAPI.list();
      const primary = cvs.find(cv => cv.is_primary);
      if (primary) {
        setPrimaryCvId(primary.id);
      }
    } catch (error) {
      console.error('Failed to load primary CV:', error);
    }
  };

  const loadJobScores = async () => {
    const scores = new Map();
    for (const job of jobs) {
      try {
        const score = await matchingAPI.getScore(primaryCvId!, job.id);
        if (score) {
          scores.set(job.id, score.overall_score);
        }
      } catch (error) {
        console.error(`Failed to load score for job ${job.id}:`, error);
      }
    }
    setJobScores(scores);
  };

  const handleDelete = async () => {
    if (!deleteJobId) return;
    
    setDeleting(true);
    try {
      await jobsAPI.delete(deleteJobId);
      setJobs(jobs.filter(j => j.id !== deleteJobId));
      toast.success('Job deleted successfully');
    } catch (error) {
      toast.error('Failed to delete job');
    } finally {
      setDeleting(false);
      setDeleteJobId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(date);
  };

  const getDescriptionPreview = (description: string) => {
    // Try to parse as JSON first
    try {
      const parsed = JSON.parse(description);
      if (parsed['About the Role']) {
        return parsed['About the Role'].substring(0, 150) + '...';
      }
    } catch {
      // If not JSON, use plain text
      return description.substring(0, 150) + '...';
    }
    return description.substring(0, 150) + '...';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">My Jobs</h1>
              <p className="text-muted-foreground">
                Manage your saved job postings
              </p>
            </div>
            <Button
              onClick={() => navigate('/jobs/add')}
              className="bg-gradient-to-r from-primary to-accent"
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Job
            </Button>
          </div>

          {/* Jobs Grid */}
          {jobs.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent className="space-y-4">
                <Briefcase className="h-16 w-16 mx-auto text-muted-foreground" />
                <div>
                  <h3 className="text-xl font-semibold mb-2">No jobs yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Start by adding your first job posting
                  </p>
                  <Button
                    onClick={() => navigate('/jobs/add')}
                    className="bg-gradient-to-r from-primary to-accent"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Your First Job
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job) => (
                <Card key={job.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between mb-2">
                      <Badge variant="secondary" className="mb-2">
                        <Briefcase className="h-3 w-3 mr-1" />
                        {job.company}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => setDeleteJobId(job.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <CardTitle className="text-lg line-clamp-2 flex-1">{job.title}</CardTitle>
                      {jobScores.has(job.id) && (
                        <MatchScoreBadge
                          score={jobScores.get(job.id)}
                          size="sm"
                          showLabel={false}
                        />
                      )}
                    </div>
                    <CardDescription className="flex items-center gap-2 text-xs">
                      <Calendar className="h-3 w-3" />
                      Added {formatDate(job.created_at)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {getDescriptionPreview(job.description)}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => navigate(`/jobs/${job.id}/tailor`)}
                      >
                        <FileText className="mr-2 h-4 w-4" />
                        View Details
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteJobId} onOpenChange={() => setDeleteJobId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Job?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this job posting. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}