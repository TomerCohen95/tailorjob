import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { FileText, Plus, Briefcase, Upload, AlertCircle, Trash2, History, ChevronDown, ChevronUp, Clock, CheckCircle, XCircle, Loader2, Bell, Eye, Star } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { cvAPI, jobsAPI, type CV, type Job, type CVNotification } from '@/lib/api';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

export default function Dashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [cvs, setCVs] = useState<CV[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobToDelete, setJobToDelete] = useState<Job | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showCVHistory, setShowCVHistory] = useState(searchParams.get('showHistory') === 'true');
  const [cvToDelete, setCvToDelete] = useState<CV | null>(null);
  const [isDeletingCV, setIsDeletingCV] = useState(false);
  const [notifications, setNotifications] = useState<CVNotification[]>([]);

  // Update URL when history view changes
  const toggleCVHistory = () => {
    const newValue = !showCVHistory;
    setShowCVHistory(newValue);
    if (newValue) {
      setSearchParams({ showHistory: 'true' });
    } else {
      setSearchParams({});
    }
  };

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
      
      // Load CVs, jobs, and notifications in parallel
      const [cvsData, jobsData, notificationsData] = await Promise.all([
        cvAPI.list(),
        jobsAPI.list(),
        cvAPI.getNotifications()
      ]);
      
      setCVs(cvsData);
      setJobs(jobsData);
      setNotifications(notificationsData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load data';
      
      // If authentication error, redirect to login
      if (message.includes('Not authenticated') || message.includes('401') || message.includes('403')) {
        await supabase.auth.signOut();
        navigate('/login');
        return;
      }
      
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteJob() {
    if (!jobToDelete) return;

    setIsDeleting(true);
    try {
      await jobsAPI.delete(jobToDelete.id);
      toast.success('Job deleted successfully');
      setJobs(jobs.filter(j => j.id !== jobToDelete.id));
      setJobToDelete(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete job';
      toast.error(message);
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleDeleteCV() {
    if (!cvToDelete) return;

    setIsDeletingCV(true);
    try {
      await cvAPI.delete(cvToDelete.id);
      toast.success('CV deleted successfully');
      setCVs(cvs.filter(cv => cv.id !== cvToDelete.id));
      setCvToDelete(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete CV';
      toast.error(message);
    } finally {
      setIsDeletingCV(false);
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'parsed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'parsing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'parsed':
        return 'Parsed';
      case 'parsing':
        return 'Parsing...';
      case 'error':
        return 'Error';
      default:
        return 'Uploaded';
    }
  };

  const primaryCV = cvs.find(cv => cv.is_primary) || cvs[0]; // Primary CV or most recent
  
  // Group CVs by file_hash to show only unique uploads
  // Keep the most recent version of each unique CV
  const uniqueCVs = cvs.reduce((acc, cv) => {
    const hash = cv.file_hash || cv.id; // Fallback to ID if no hash
    const existing = acc.get(hash);
    
    // Keep the CV with the most recent created_at date
    if (!existing || new Date(cv.created_at) > new Date(existing.created_at)) {
      acc.set(hash, cv);
    }
    
    return acc;
  }, new Map<string, CV>());
  
  const displayCVs = Array.from(uniqueCVs.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const handleSetPrimary = async (cvId: string) => {
    try {
      await cvAPI.setPrimary(cvId);
      toast.success('CV set as primary');
      loadData(); // Reload to update UI
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to set CV as primary';
      toast.error(message);
    }
  };

  const handleViewCV = async (notification: CVNotification) => {
    try {
      // Mark notification as read
      await cvAPI.deleteNotification(notification.id);
      setNotifications(notifications.filter(n => n.id !== notification.id));
      
      // Navigate to CV
      navigate(`/cv/${notification.cv_id}`);
    } catch (error) {
      console.error('Error handling notification:', error);
    }
  };

  const handleMakePrimary = async (notification: CVNotification) => {
    try {
      await cvAPI.setPrimary(notification.cv_id);
      await cvAPI.deleteNotification(notification.id);
      setNotifications(notifications.filter(n => n.id !== notification.id));
      toast.success('CV set as primary');
      loadData(); // Reload to update UI
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to set CV as primary';
      toast.error(message);
    }
  };

  const handleDismissNotification = async (notificationId: string) => {
    try {
      await cvAPI.deleteNotification(notificationId);
      setNotifications(notifications.filter(n => n.id !== notificationId));
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
  };

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

        {/* Notifications Section */}
        {notifications.length > 0 && (
          <div className="mb-6 space-y-3">
            {notifications.map((notification) => (
              <Alert key={notification.id} className="border-green-500/50 bg-green-50 dark:bg-green-950/20">
                <Bell className="h-4 w-4 text-green-600" />
                <AlertDescription className="flex items-center justify-between gap-4">
                  <span className="text-green-800 dark:text-green-200">{notification.message}</span>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewCV(notification)}
                      className="border-green-600 text-green-700 hover:bg-green-100"
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      View
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleMakePrimary(notification)}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <Star className="h-3 w-3 mr-1" />
                      Make Primary
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDismissNotification(notification.id)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      Dismiss
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="border-2 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-2 rounded-lg bg-primary-light">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Your CV</CardTitle>
                  {cvs.length > 1 && (
                    <CardDescription className="text-xs mt-1">
                      {cvs.length} uploads •{' '}
                      <button
                        onClick={toggleCVHistory}
                        className="text-primary hover:underline"
                      >
                        {showCVHistory ? 'Hide history' : 'View history'}
                      </button>
                    </CardDescription>
                  )}
                </div>
              </div>
              <CardDescription>
                {primaryCV
                  ? `Last uploaded: ${new Date(primaryCV.created_at).toLocaleDateString()}`
                  : 'No CV uploaded yet'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {primaryCV ? (
                <>
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="flex items-start gap-2">
                      {getStatusIcon(primaryCV.status)}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground truncate">{primaryCV.original_filename}</p>
                        <p className="text-sm text-muted-foreground">
                          {(primaryCV.file_size / 1024).toFixed(0)} KB • {getStatusText(primaryCV.status)}
                        </p>
                      </div>
                    </div>
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
                    <div key={job.id} className="p-4 border border-border rounded-lg hover:bg-muted transition-colors group">
                      <div className="flex items-start justify-between gap-2">
                        <Link to={`/jobs/${job.id}/tailor`} className="flex-1">
                          <div>
                            <p className="font-medium text-foreground">{job.title}</p>
                            <p className="text-sm text-muted-foreground">{job.company}</p>
                          </div>
                        </Link>
                        <div className="flex gap-1">
                          <Link to={`/jobs/${job.id}/tailor`}>
                            <Button size="sm" variant="ghost">Tailor CV</Button>
                          </Link>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                            onClick={(e) => {
                              e.preventDefault();
                              setJobToDelete(job);
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                  {jobs.length > 3 && (
                    <Link
                      to="/jobs"
                      className="block text-sm text-primary hover:text-primary/80 text-center pt-2 font-medium transition-colors cursor-pointer"
                    >
                      +{jobs.length - 3} more jobs →
                    </Link>
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

        {/* CV Upload History - Separate Section */}
        {displayCVs.length > 1 && showCVHistory && (
          <Card className="shadow-md mb-8">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <History className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle>CV Upload History</CardTitle>
                    <CardDescription>All your uploaded CVs ({displayCVs.length} unique uploads)</CardDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleCVHistory}
                >
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Hide
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {displayCVs.map((cv, index) => (
                  <div
                    key={cv.id}
                    className="p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {getStatusIcon(cv.status)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium text-foreground truncate">
                              {cv.original_filename}
                            </p>
                            {cv.is_primary && (
                              <span className="px-2 py-0.5 text-xs font-medium bg-primary text-primary-foreground rounded shrink-0">
                                Primary
                              </span>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-x-3 text-xs text-muted-foreground">
                            <span>
                              {new Date(cv.created_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                            <span>{(cv.file_size / 1024).toFixed(0)} KB</span>
                            <span>{getStatusText(cv.status)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        {cv.is_primary ? (
                          <span className="px-3 py-1.5 text-xs font-medium bg-primary/10 text-primary rounded border border-primary/20">
                            Active
                          </span>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleSetPrimary(cv.id)}
                          >
                            Set as Primary
                          </Button>
                        )}
                        {cv.status === 'parsed' && (
                          <Link to={`/cv-preview?cvId=${cv.id}&returnTo=${encodeURIComponent('/dashboard?showHistory=true')}`}>
                            <Button size="sm" variant="outline">
                              View
                            </Button>
                          </Link>
                        )}
                        {cv.status === 'error' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={async () => {
                              try {
                                await cvAPI.reparse(cv.id);
                                toast.success('Re-parsing initiated');
                                loadData();
                              } catch (error) {
                                toast.error('Failed to re-parse CV');
                              }
                            }}
                          >
                            Retry
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={() => setCvToDelete(cv)}
                          disabled={cv.is_primary}
                          title={cv.is_primary ? "Cannot delete primary CV" : "Delete CV"}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

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

      <AlertDialog open={!!jobToDelete} onOpenChange={(open) => !open && setJobToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Job?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{jobToDelete?.title}" at {jobToDelete?.company}?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteJob}
              disabled={isDeleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* CV Delete Confirmation Dialog */}
      <AlertDialog open={!!cvToDelete} onOpenChange={(open) => !open && setCvToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete CV?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{cvToDelete?.original_filename}"?
              This will permanently remove the CV and all its parsed data. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeletingCV}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteCV}
              disabled={isDeletingCV}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isDeletingCV ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
