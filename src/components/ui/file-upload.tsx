import { useCallback, useState } from 'react';
import { Upload, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  className?: string;
}

export function FileUpload({ onFileSelect, accept = '.pdf,.doc,.docx', className }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      setSelectedFile(files[0]);
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      setSelectedFile(files[0]);
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);

  const clearFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className={cn('w-full', className)}>
      {!selectedFile ? (
        <label
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={cn(
            'flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer transition-colors',
            isDragging
              ? 'border-primary bg-primary-light'
              : 'border-border bg-card hover:bg-muted'
          )}
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <Upload className={cn('w-12 h-12 mb-4', isDragging ? 'text-primary' : 'text-muted-foreground')} />
            <p className="mb-2 text-sm text-foreground">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-muted-foreground">PDF, DOC, or DOCX (MAX. 10MB)</p>
          </div>
          <input
            type="file"
            className="hidden"
            accept={accept}
            onChange={handleFileInput}
          />
        </label>
      ) : (
        <div className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-light">
              <File className="w-6 h-6 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <button
            onClick={clearFile}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>
      )}
    </div>
  );
}
