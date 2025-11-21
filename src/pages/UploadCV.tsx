import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { FileUpload } from '@/components/ui/file-upload';
import { ArrowRight, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function UploadCV() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    // Mock upload delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    toast.success('CV uploaded successfully!');
    setIsUploading(false);
    navigate('/cv-preview');
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Upload Your CV</h1>
            <p className="text-muted-foreground">
              Upload your existing CV to start creating tailored versions
            </p>
          </div>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Upload Document</CardTitle>
              <CardDescription>
                Supported formats: PDF, DOC, DOCX (Max 10MB)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <FileUpload onFileSelect={handleFileSelect} />

              {file && (
                <div className="p-4 bg-primary-light rounded-lg border border-primary/20">
                  <div className="flex items-center gap-2 text-primary mb-2">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">File ready to upload</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    We'll parse your CV and extract key information automatically
                  </p>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => navigate('/dashboard')}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                  className="flex-1 bg-gradient-to-r from-primary to-accent hover:opacity-90"
                >
                  {isUploading ? 'Uploading...' : 'Upload & Parse'}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h3 className="font-medium text-foreground mb-2">What happens next?</h3>
            <ol className="space-y-2 text-sm text-muted-foreground">
              <li className="flex gap-2">
                <span className="text-primary font-medium">1.</span>
                Your CV will be parsed and analyzed
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-medium">2.</span>
                We'll extract your experience, skills, and education
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-medium">3.</span>
                You can review the parsed information
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-medium">4.</span>
                Start adding job descriptions to tailor your CV
              </li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  );
}
