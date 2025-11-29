import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Navigation } from '@/components/layout/Navigation';
import { FileUpload } from '@/components/ui/file-upload';
import { ArrowRight, CheckCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { cvAPI } from '@/lib/api';
import { useCVParsing } from '@/contexts/CVParsingContext';
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

export default function UploadCV() {
  const navigate = useNavigate();
  const { startParsing } = useCVParsing();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false);
  const [duplicateCvId, setDuplicateCvId] = useState<string | null>(null);
  const [duplicateCvInfo, setDuplicateCvInfo] = useState<any>(null);
  const [cvToCancel, setCvToCancel] = useState<string | null>(null);
  const [isCanceling, setIsCanceling] = useState(false);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    
    try {
      const result: any = await cvAPI.upload(file);
      
      // Check if it's a duplicate
      if (result.status === 'duplicate') {
        setDuplicateCvId(result.cv_id);
        setDuplicateCvInfo(result.existing_cv);
        setShowDuplicateDialog(true);
        setIsUploading(false);
        return;
      }
      
      // Store CV ID for cancellation
      if (result.cv_id) {
        setCvToCancel(result.cv_id);
        // Start tracking parsing in context
        startParsing(result.cv_id, file.name);
      }
      
      toast.success('CV uploaded successfully!', {
        description: 'Your CV is being parsed...'
      });
      
      // Redirect to dashboard after successful upload
      navigate('/dashboard');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to upload CV';
      toast.error('Upload failed', {
        description: message
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancelUpload = async () => {
    if (!cvToCancel) return;
    
    setIsCanceling(true);
    try {
      await cvAPI.delete(cvToCancel);
      toast.success('Upload cancelled');
      setCvToCancel(null);
      setFile(null);
    } catch (error) {
      console.error('Failed to cancel upload:', error);
    } finally {
      setIsCanceling(false);
      setIsUploading(false);
    }
  };

  const handleReparse = async () => {
    if (!duplicateCvId) return;

    setShowDuplicateDialog(false);
    setIsUploading(true);

    try {
      await cvAPI.reparse(duplicateCvId);
      
      toast.success('Re-parsing initiated!', {
        description: 'Your CV is being parsed with the updated AI...'
      });
      
      navigate('/dashboard');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to re-parse CV';
      toast.error('Re-parse failed', {
        description: message
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleUseDuplicate = () => {
    setShowDuplicateDialog(false);
    navigate('/dashboard');
  };

  return (
    <>
      <AlertDialog open={showDuplicateDialog} onOpenChange={setShowDuplicateDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <AlertDialogTitle>CV Already Exists</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="space-y-2">
              <p>
                You've already uploaded this CV on{' '}
                {duplicateCvInfo?.created_at &&
                  new Date(duplicateCvInfo.created_at).toLocaleDateString()}
              </p>
              <p className="font-medium text-foreground">
                File: {duplicateCvInfo?.original_filename}
              </p>
              <p className="text-sm mt-2">
                Would you like to re-parse it with the latest AI improvements, or use the existing version?
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleUseDuplicate}>
              Use Existing
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleReparse}>
              Re-parse CV
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

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
                {isUploading ? (
                  <Button
                    onClick={handleCancelUpload}
                    variant="destructive"
                    className="flex-1"
                    disabled={isCanceling}
                  >
                    {isCanceling ? 'Canceling...' : 'Cancel Upload'}
                  </Button>
                ) : (
                  <Button
                    onClick={handleUpload}
                    disabled={!file}
                    className="flex-1 bg-gradient-to-r from-primary to-accent hover:opacity-90"
                  >
                    Upload & Parse
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                )}
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
    </>
  );
}
