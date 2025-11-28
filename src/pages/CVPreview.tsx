import { Link, useSearchParams, useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Briefcase, GraduationCap, Award, Loader2, CheckCircle2, Clock } from 'lucide-react';
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface CVSections {
  summary: string;
  skills: string[] | Record<string, string[]>;
  experience: any[];
  education: any[];
  certifications: any[];
}

export default function CVPreview() {
  const [searchParams] = useSearchParams();
  const { id } = useParams();
  const cvId = id || searchParams.get('cvId');
  const [sections, setSections] = useState<CVSections | null>(null);
  const [loading, setLoading] = useState(true);
  const [cvStatus, setCvStatus] = useState<string>('');
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const fetchCVData = async () => {
      if (!cvId) {
        // If no cvId, fetch the primary CV (or most recent if no primary)
        try {
          const cvs = await apiClient.getCVs();
          if (cvs.length > 0) {
            // Find primary CV or fall back to most recent
            const primaryCV = cvs.find(cv => cv.is_primary) || cvs[0];
            const data = await apiClient.getCV(primaryCV.id);
            setCvStatus(data.cv?.status || 'unknown');
            
            if (data.sections) {
              // Parse JSON strings from database
              setSections({
                summary: data.sections.summary || 'No summary available',
                skills: JSON.parse(data.sections.skills || '[]'),
                experience: JSON.parse(data.sections.experience || '[]'),
                education: JSON.parse(data.sections.education || '[]'),
                certifications: JSON.parse(data.sections.certifications || '[]')
              });
            }
          }
        } catch (error) {
          console.error('Error fetching CV:', error);
          toast.error('Failed to load CV data');
        } finally {
          setLoading(false);
        }
        return;
      }

      try {
        const data = await apiClient.getCV(cvId);
        setCvStatus(data.cv?.status || 'unknown');
        
        if (data.sections) {
          // Parse JSON strings from database
          setSections({
            summary: data.sections.summary || 'No summary available',
            skills: JSON.parse(data.sections.skills || '[]'),
            experience: JSON.parse(data.sections.experience || '[]'),
            education: JSON.parse(data.sections.education || '[]'),
            certifications: JSON.parse(data.sections.certifications || '[]')
          });
        }
      } catch (error) {
        console.error('Error fetching CV:', error);
        toast.error('Failed to load CV data');
      } finally {
        setLoading(false);
      }
    };

    fetchCVData();
  }, [cvId]);

  // Poll for updates when CV is being parsed
  useEffect(() => {
    if (cvStatus === 'uploaded' || cvStatus === 'parsing') {
      const interval = setInterval(async () => {
        try {
          const targetCvId = cvId || (await apiClient.getCVs())[0]?.id;
          if (targetCvId) {
            const data = await apiClient.getCV(targetCvId);
            const newStatus = data.cv?.status || 'unknown';
            setCvStatus(newStatus);
            
            // If parsing completed, update sections and stop polling
            if (newStatus === 'parsed' && data.sections) {
              setSections({
                summary: data.sections.summary || 'No summary available',
                skills: JSON.parse(data.sections.skills || '[]'),
                experience: JSON.parse(data.sections.experience || '[]'),
                education: JSON.parse(data.sections.education || '[]'),
                certifications: JSON.parse(data.sections.certifications || '[]')
              });
              toast.success('CV parsing completed!');
              clearInterval(interval);
            }
          }
        } catch (error) {
          console.error('Error polling CV status:', error);
        }
      }, 3000); // Poll every 3 seconds

      setPollingInterval(interval);

      return () => {
        clearInterval(interval);
      };
    }
  }, [cvStatus, cvId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="flex items-center justify-center h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!sections) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">No CV data available. Please upload a CV first.</p>
              <div className="mt-4 flex justify-center">
                <Link to="/upload">
                  <Button>Upload CV</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const renderStatusBadge = () => {
    switch (cvStatus) {
      case 'uploaded':
      case 'parsing':
        return (
          <Badge variant="outline" className="border-yellow-500 text-yellow-700 bg-yellow-50">
            <Clock className="h-3 w-3 mr-1 animate-pulse" />
            Parsing in progress...
          </Badge>
        );
      case 'parsed':
        return (
          <Badge variant="outline" className="border-green-500 text-green-700 bg-green-50">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Parsing complete
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="destructive">
            Parsing failed
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-foreground">Parsed CV Preview</h1>
                {renderStatusBadge()}
              </div>
              <p className="text-muted-foreground">Review your extracted information</p>
            </div>
            <Link to="/jobs/add">
              <Button
                className="bg-gradient-to-r from-primary to-accent hover:opacity-90"
                disabled={cvStatus !== 'parsed'}
              >
                Continue to Add Job
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

          {(cvStatus === 'uploaded' || cvStatus === 'parsing') && (
            <Alert className="mb-6 border-yellow-500 bg-yellow-50">
              <Loader2 className="h-4 w-4 animate-spin text-yellow-700" />
              <AlertDescription className="text-yellow-700">
                Your CV is being parsed with AI. This usually takes 10-30 seconds. The page will update automatically when complete.
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-6">
            {/* Summary */}
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-primary" />
                  Professional Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground leading-relaxed">{sections.summary}</p>
              </CardContent>
            </Card>

            {/* Skills */}
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-accent" />
                  Skills
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-4">
                  {Array.isArray(sections.skills) ? (
                    <div className="flex flex-wrap gap-2">
                      {sections.skills.length > 0 ? (
                        sections.skills.map((skill, index) => (
                          <Badge key={index} variant="secondary" className="px-3 py-1">
                            {skill}
                          </Badge>
                        ))
                      ) : (
                        <p className="text-muted-foreground">No skills listed</p>
                      )}
                    </div>
                  ) : (
                    Object.entries(sections.skills).map(([category, skills]) => (
                      <div key={category}>
                        <h4 className="text-sm font-semibold text-muted-foreground mb-2 capitalize">
                          {category.replace('_', ' ')}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {skills && skills.length > 0 ? (
                            skills.map((skill, index) => (
                              <Badge key={index} variant="secondary" className="px-3 py-1">
                                {skill}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-sm text-muted-foreground italic">None</span>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Experience */}
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-primary" />
                  Work Experience
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {sections.experience.length > 0 ? (
                  sections.experience.map((exp, index) => (
                    <div key={index} className="border-l-2 border-primary pl-4">
                      <h3 className="font-semibold text-foreground text-lg">{exp.title || 'Position'}</h3>
                      <p className="text-muted-foreground mb-2">
                        {exp.company || 'Company'} • {exp.period || exp.duration || 'Duration'}
                      </p>
                      {exp.description && (
                        <ul className="space-y-2 list-disc list-inside text-foreground">
                          {Array.isArray(exp.description) ? (
                            exp.description.map((item, i) => (
                              <li key={i} className="text-sm leading-relaxed">{item}</li>
                            ))
                          ) : (
                            // Handle string with bullet points - split by common bullet symbols
                            exp.description.split(/[●•\n]/g)
                              .map(item => item.trim())
                              .filter(item => item.length > 0)
                              .map((item, i) => (
                                <li key={i} className="text-sm leading-relaxed">{item}</li>
                              ))
                          )}
                        </ul>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">No work experience listed</p>
                )}
              </CardContent>
            </Card>

            {/* Education */}
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GraduationCap className="h-5 w-5 text-accent" />
                  Education
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {sections.education.length > 0 ? (
                  sections.education.map((edu, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-accent-light">
                        <GraduationCap className="h-4 w-4 text-accent" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{edu.degree || 'Degree'}</h3>
                        <p className="text-sm text-muted-foreground">
                          {edu.institution || edu.school || 'Institution'} • {edu.year || edu.graduation_year || 'Year'}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">No education listed</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="mt-8 flex justify-end">
            <Link to="/jobs/add">
              <Button size="lg" className="bg-gradient-to-r from-primary to-accent hover:opacity-90">
                Continue to Add Job
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
