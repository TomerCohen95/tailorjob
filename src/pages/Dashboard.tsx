import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { FileText, Plus, Briefcase, Upload } from 'lucide-react';
import { mockJobs } from '@/lib/mockData';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
          <p className="text-muted-foreground">Manage your CVs and job applications</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="border-2 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-2 rounded-lg bg-primary-light">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <CardTitle>Your CV</CardTitle>
              </div>
              <CardDescription>Last uploaded: January 15, 2024</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-4 bg-muted rounded-lg">
                <p className="font-medium text-foreground">john_doe_cv.pdf</p>
                <p className="text-sm text-muted-foreground">245 KB</p>
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
              <CardDescription>{mockJobs.length} jobs tracked</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {mockJobs.map((job) => (
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
              </div>
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
