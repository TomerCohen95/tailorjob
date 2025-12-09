import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import { ActionSuggestion } from './ActionCard';
import { DiffView } from './DiffView';

interface CVPreviewProps {
  cvData: any;
  acceptedSuggestions: ActionSuggestion[];
}

export function CVPreview({ cvData, acceptedSuggestions }: CVPreviewProps) {
  if (!cvData || !cvData.sections) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <p className="text-muted-foreground">Loading CV data...</p>
      </div>
    );
  }

  const sections = cvData.sections;
  
  // Group suggestions by section
  const suggestionsBySection: Record<string, ActionSuggestion[]> = {};
  acceptedSuggestions.forEach(suggestion => {
    if (!suggestionsBySection[suggestion.section]) {
      suggestionsBySection[suggestion.section] = [];
    }
    suggestionsBySection[suggestion.section].push(suggestion);
  });

  // Extract clean text from CV section content with full formatting
  const extractCleanText = (content: any): string => {
    if (typeof content === 'string') {
      // If it's a JSON string, try to parse it
      if (content.startsWith('{') || content.startsWith('[')) {
        try {
          const parsed = JSON.parse(content);
          return extractCleanText(parsed);
        } catch {
          return content;
        }
      }
      return content;
    }
    
    if (Array.isArray(content)) {
      return content.map(item => {
        if (typeof item === 'string') return item;
        if (item.title && item.company) {
          let text = `${item.title} at ${item.company}`;
          if (item.period) text += `\n${item.period}`;
          if (item.description) {
            text += '\n\n';
            if (Array.isArray(item.description)) {
              text += item.description.map(d => `• ${d}`).join('\n');
            } else {
              text += item.description;
            }
          }
          return text;
        }
        if (item.description) return Array.isArray(item.description) ? item.description.join('\n') : item.description;
        return JSON.stringify(item);
      }).join('\n\n---\n\n');
    }
    
    if (typeof content === 'object' && content !== null) {
      // Handle objects like skills sections
      return Object.entries(content)
        .map(([key, value]) => {
          if (Array.isArray(value)) {
            return `${key}:\n${value.map(v => `  • ${v}`).join('\n')}`;
          }
          return `${key}: ${value}`;
        })
        .join('\n\n');
    }
    
    return String(content);
  };

  // Generate mock modified text based on suggestions
  const generateModifiedText = (originalText: string, suggestion: ActionSuggestion, parsedContent: any): string => {
    switch (suggestion.type) {
      case 'add_to_summary':
        // For Professional Summary leadership emphasis
        if (suggestion.suggestion.toLowerCase().includes('leadership')) {
          return originalText
            .replace(
              'Cyber Security R&D',
              'Cyber Security Team Lead & Senior R&D Engineer'
            )
            .replace(
              'specializing in Windows security',
              'leading security R&D initiatives and specializing in Windows security'
            )
            .replace(
              '8+ years of experience',
              '8+ years of leadership experience'
            );
        }
        return originalText + '\n\n' + suggestion.suggestion;
        
      case 'highlight_skill':
        // For Python highlighting - find the most relevant job and enhance it
        if (suggestion.suggestion.toLowerCase().includes('python') && Array.isArray(parsedContent)) {
          // Find Team Lead position (most recent leadership role)
          const teamLeadJob = parsedContent.find(job =>
            job.title && job.title.includes('Team Lead')
          );
          
          if (teamLeadJob) {
            const before = `${teamLeadJob.title} at ${teamLeadJob.company}\n${teamLeadJob.period}\n\n${
              Array.isArray(teamLeadJob.description)
                ? teamLeadJob.description.map((d: string) => `• ${d}`).join('\n')
                : teamLeadJob.description
            }`;
            
            const after = before + '\n• Developed Python-based automation tools for security analysis and threat detection\n• Created Python scripts for vulnerability scanning and reporting';
            
            return originalText.replace(before, after);
          }
        }
        return originalText + '\n\nHighlighted: ' + suggestion.suggestion;
        
      case 'enhance_experience':
        // For CI/CD tools - add to skills section
        if (suggestion.suggestion.toLowerCase().includes('ci/cd')) {
          // Add CI/CD as a new category in skills
          return originalText + '\n\nci/cd:\n  • Jenkins\n  • GitLab CI\n  • Azure DevOps\n  • GitHub Actions';
        }
        return originalText + '\n\nEnhanced with: ' + suggestion.suggestion;
        
      default:
        return originalText + '\n\n' + suggestion.suggestion;
    }
  };

  const renderSection = (title: string, content: string | any, sectionKey: string) => {
    const suggestions = suggestionsBySection[sectionKey] || [];
    const hasSuggestions = suggestions.length > 0;

    // Parse content if it's JSON string
    let displayContent = content;
    if (typeof content === 'string' && (content.startsWith('{') || content.startsWith('['))) {
      try {
        displayContent = JSON.parse(content);
      } catch {
        // Keep as string if not valid JSON
      }
    }
    
    // Apply suggestions inline to display content
    if (hasSuggestions && Array.isArray(displayContent)) {
      let pythonAdded = false; // Track if we've already added Python bullets
      
      displayContent = displayContent.map((item) => {
        // For Python skill highlight - add to FIRST Team Lead position only
        const pythonSuggestion = suggestions.find(s =>
          s.type === 'highlight_skill' && s.suggestion.toLowerCase().includes('python')
        );
        
        if (pythonSuggestion && !pythonAdded && item.title && item.title.includes('Team Lead')) {
          pythonAdded = true; // Mark as added so we don't add again
          
          const newDescription = 'Developed Python-based automation tools for security analysis and threat detection';
          
          return {
            ...item,
            description: [
              ...(Array.isArray(item.description) ? item.description : [item.description]),
              newDescription
            ],
            _addedDescriptions: [newDescription] // Track which one is new
          };
        }
        
        return item;
      });
    }

    return (
      <Card key={sectionKey} className={`p-6 ${hasSuggestions ? 'border-green-200 bg-green-50/50' : ''}`}>
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
            {title}
            {hasSuggestions && (
              <Badge variant="outline" className="bg-green-100 text-green-700 border-green-200">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                {suggestions.length} {suggestions.length === 1 ? 'improvement' : 'improvements'}
              </Badge>
            )}
          </h3>
        </div>

        {/* Original Content */}
        <div className="space-y-3 text-sm">
          {typeof displayContent === 'string' ? (
            <p className="text-foreground whitespace-pre-wrap">{displayContent}</p>
          ) : Array.isArray(displayContent) ? (
            <div className="space-y-4">
              {displayContent.map((item, idx) => (
                <div key={idx} className="space-y-1">
                  {item.title && (
                    <p className="font-medium text-foreground">
                      {item.title} {item.company && `at ${item.company}`}
                    </p>
                  )}
                  {item.period && (
                    <p className="text-xs text-muted-foreground">{item.period}</p>
                  )}
                  {item.description && Array.isArray(item.description) && (
                    <ul className="list-none space-y-1">
                      {item.description.map((desc, i) => {
                        const isNewAddition = item._addedDescriptions &&
                          item._addedDescriptions.includes(desc);
                        
                        return (
                          <li
                            key={i}
                            className={isNewAddition
                              ? 'bg-green-100 border-l-4 border-green-500 pl-3 py-1.5 text-green-900 font-medium rounded'
                              : 'text-muted-foreground ml-4 list-disc'
                            }
                          >
                            {isNewAddition ? `• ${desc}` : desc}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                  {item.degree && (
                    <p className="text-foreground">
                      {item.degree} in {item.field} - {item.institution} ({item.year})
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(displayContent as Record<string, any>).map(([key, value]) => (
                <div key={key}>
                  <p className="font-medium text-foreground capitalize">{key.replace(/_/g, ' ')}:</p>
                  {Array.isArray(value) ? (
                    <ul className="list-disc list-inside ml-4 text-muted-foreground">
                      {value.map((item, i) => (
                        <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="ml-4 text-muted-foreground">{String(value)}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </Card>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-foreground flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              Tailored CV Preview
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              {acceptedSuggestions.length > 0 ? (
                <>
                  Showing {acceptedSuggestions.length} AI-powered {acceptedSuggestions.length === 1 ? 'enhancement' : 'enhancements'}
                </>
              ) : (
                'Click "Tailor CV" to get AI-powered suggestions'
              )}
            </p>
          </div>
          {acceptedSuggestions.length > 0 && (
            <Badge variant="outline" className="bg-green-100 text-green-700 border-green-200">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              {acceptedSuggestions.length} applied
            </Badge>
          )}
        </div>
      </div>
      
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6 max-w-4xl mx-auto">
          {/* Personal Info */}
          <Card className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200">
            <h2 className="text-2xl font-bold text-foreground mb-2">
              {cvData.cv?.original_filename?.replace('.pdf', '') || 'Your CV'}
            </h2>
            <p className="text-sm text-muted-foreground">
              Last updated: {new Date(cvData.cv?.updated_at || Date.now()).toLocaleDateString()}
            </p>
          </Card>

          {/* Summary */}
          {sections.summary && renderSection('Professional Summary', sections.summary, 'summary')}
          
          {/* Skills */}
          {sections.skills && renderSection('Skills', sections.skills, 'skills')}
          
          {/* Experience */}
          {sections.experience && renderSection('Work Experience', sections.experience, 'experience')}
          
          {/* Education */}
          {sections.education && renderSection('Education', sections.education, 'education')}
          
          {/* Certifications */}
          {sections.certifications && sections.certifications !== '[]' && 
            renderSection('Certifications', sections.certifications, 'certifications')}
        </div>
      </ScrollArea>
    </div>
  );
}