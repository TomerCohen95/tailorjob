import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Briefcase, GraduationCap, Award } from 'lucide-react';
import { mockParsedCV } from '@/lib/mockData';

export default function CVPreview() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Parsed CV Preview</h1>
              <p className="text-muted-foreground">Review your extracted information</p>
            </div>
            <Link to="/jobs/add">
              <Button className="bg-gradient-to-r from-primary to-accent hover:opacity-90">
                Continue to Add Job
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

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
                <p className="text-foreground leading-relaxed">{mockParsedCV.summary}</p>
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
                <div className="flex flex-wrap gap-2">
                  {mockParsedCV.skills.map((skill, index) => (
                    <Badge key={index} variant="secondary" className="px-3 py-1">
                      {skill}
                    </Badge>
                  ))}
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
                {mockParsedCV.experience.map((exp, index) => (
                  <div key={index} className="border-l-2 border-primary pl-4">
                    <h3 className="font-semibold text-foreground text-lg">{exp.title}</h3>
                    <p className="text-muted-foreground mb-2">{exp.company} • {exp.period}</p>
                    <ul className="space-y-1 list-disc list-inside text-foreground">
                      {exp.description.map((item, i) => (
                        <li key={i} className="text-sm">{item}</li>
                      ))}
                    </ul>
                  </div>
                ))}
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
                {mockParsedCV.education.map((edu, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-accent-light">
                      <GraduationCap className="h-4 w-4 text-accent" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">{edu.degree}</h3>
                      <p className="text-sm text-muted-foreground">{edu.institution} • {edu.year}</p>
                    </div>
                  </div>
                ))}
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
