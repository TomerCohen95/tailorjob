# Interactive CV Tailoring UI - Implementation Plan

## Overview
Transform the CV tailoring workflow from a simple "export PDF" button into an interactive experience where users can:
1. See AI-generated recommendations for tailoring their CV
2. Accept/reject individual suggestions
3. Preview the tailored CV in real-time
4. Export the final version as PDF

## Current State vs. Desired State

### Current (Basic)
- User clicks "Export PDF"
- Backend extracts CV facts
- Generates PDF directly
- Downloads immediately

### Desired (Interactive)
1. User clicks "Tailor CV" button
2. Backend generates intelligent recommendations
3. User reviews recommendations in interactive UI
4. User accepts/rejects each suggestion
5. Live preview updates in real-time
6. User exports when satisfied

## Architecture Design

### Backend Changes

#### 1. New Endpoint: `/api/tailor/analyze`
```python
POST /api/tailor/analyze
Request: {
  "cv_id": "uuid",
  "job_id": "uuid"
}

Response: {
  "tailoring_session_id": "uuid",
  "recommendations": [
    {
      "id": "rec_1",
      "section": "summary",
      "type": "rewrite",
      "original": "Current summary text...",
      "suggested": "Tailored summary highlighting...",
      "reasoning": "Emphasizes X which matches job requirement Y",
      "impact": "high",  // high, medium, low
      "status": "pending"  // pending, accepted, rejected
    },
    {
      "id": "rec_2",
      "section": "skills",
      "type": "add",
      "suggested": "Docker, Kubernetes",
      "reasoning": "Job requires container orchestration experience",
      "impact": "medium"
    },
    {
      "id": "rec_3",
      "section": "experience",
      "type": "highlight",
      "experience_id": "exp_1",
      "original": "Led team of 5 engineers...",
      "suggested": "Led cross-functional team of 5 engineers in cloud migration project...",
      "reasoning": "Matches 'cloud migration' requirement",
      "impact": "high"
    }
  ],
  "cv_preview": {
    "personal_info": {...},
    "summary": "original summary",
    "experience": [...],
    ...
  }
}
```

#### 2. New Endpoint: `/api/tailor/apply`
```python
POST /api/tailor/apply
Request: {
  "session_id": "uuid",
  "accepted_recommendations": ["rec_1", "rec_3"],
  "rejected_recommendations": ["rec_2"]
}

Response: {
  "tailored_cv": {
    "personal_info": {...},
    "summary": "tailored summary with accepted changes",
    ...
  }
}
```

#### 3. Enhanced PDF Generation
```python
POST /api/tailor/generate-pdf
Request: {
  "session_id": "uuid",
  "cv_data": {...}  // Already tailored with accepted recommendations
}

Response: PDF file
```

### Frontend Changes

#### 1. New Component: `TailoringWorkflow.tsx`
```tsx
interface TailoringWorkflowProps {
  cvId: string;
  jobId: string;
  onComplete: () => void;
}

// Steps:
// 1. Analyzing (loading spinner)
// 2. Recommendations (interactive list)
// 3. Preview (side-by-side comparison)
// 4. Export (PDF download)
```

#### 2. New Component: `RecommendationCard.tsx`
```tsx
interface Recommendation {
  id: string;
  section: string;
  type: 'rewrite' | 'add' | 'remove' | 'highlight';
  original?: string;
  suggested: string;
  reasoning: string;
  impact: 'high' | 'medium' | 'low';
  status: 'pending' | 'accepted' | 'rejected';
}

// Features:
// - Show before/after comparison
// - Accept/Reject buttons
// - Impact badge (color-coded)
// - Reasoning tooltip
```

#### 3. New Component: `CVPreview.tsx`
```tsx
// Live-updating preview that shows:
// - Original CV (left) vs Tailored CV (right)
// - Highlighted changes
// - Section-by-section comparison
// - Responsive design (stacked on mobile)
```

## UI/UX Flow

### Step 1: Trigger Tailoring
**Location**: TailorCV page, Match Analysis tab

**Button**: "Tailor CV for this Job" (replaces simple "Export PDF")

**Action**: Opens modal/drawer with tailoring workflow

### Step 2: Analysis Phase
**UI**: 
- Loading spinner with progress messages
  - "Analyzing job requirements..."
  - "Extracting key skills..."
  - "Generating recommendations..."
- Takes 5-10 seconds

### Step 3: Recommendations Review
**Layout**: Split view
- **Left**: List of recommendations (scrollable)
- **Right**: Live preview of CV

**Recommendation Card**:
```
┌─────────────────────────────────────────┐
│ 🎯 High Impact                          │
│                                         │
│ Summary Rewrite                         │
│ ────────────────────────────────────   │
│ Original:                               │
│ "Experienced developer..."              │
│                                         │
│ Suggested:                              │
│ "Senior Cloud Developer with 5+..."    │
│                                         │
│ 💡 Why: Emphasizes cloud experience    │
│    mentioned in job requirements        │
│                                         │
│ [✓ Accept]  [✗ Reject]                 │
└─────────────────────────────────────────┘
```

**Features**:
- Filter by section (Summary, Skills, Experience, etc.)
- Filter by impact (High, Medium, Low)
- "Accept All" / "Reject All" buttons
- Show/hide rejected recommendations
- Counter: "3 of 8 recommendations accepted"

### Step 4: Preview & Export
**Layout**: 
- **Left**: Final preview (like actual PDF)
- **Right**: Export options

**Export Options**:
- Template selection (Modern/Classic)
- File name customization
- "Download PDF" button
- "Save as revision" button (optional)

## Implementation Phases

### Phase 1: Backend Intelligence (Week 1)
- [ ] Create CV Analyzer service
  - Extract job requirements
  - Match with CV content
  - Generate specific recommendations
- [ ] Implement recommendation engine
  - Summary rewriting
  - Skill highlighting
  - Experience enhancement
  - Achievement highlighting
- [ ] Create tailoring session management
  - Store recommendations
  - Track accept/reject status
  - Generate final tailored CV

### Phase 2: Frontend UI Components (Week 1-2)
- [ ] Create `TailoringWorkflow` main component
- [ ] Build `RecommendationCard` with interactions
- [ ] Implement `CVPreview` with diff highlighting
- [ ] Add state management (recommendations, preview)
- [ ] Implement accept/reject logic

### Phase 3: Integration & Polish (Week 2)
- [ ] Connect frontend to backend
- [ ] Add loading states and error handling
- [ ] Implement responsive design
- [ ] Add animations and transitions
- [ ] Test entire workflow

### Phase 4: Advanced Features (Week 3)
- [ ] Add "Edit mode" - manual text editing
- [ ] Implement undo/redo for recommendations
- [ ] Add comparison sliders (before/after)
- [ ] Save multiple tailored versions
- [ ] Export to different formats (DOCX, HTML)

## Technical Considerations

### AI Recommendations Quality
- Use GPT-4 for high-quality suggestions
- Provide specific, actionable recommendations
- Include reasoning for transparency
- Prioritize by impact on match score

### Performance
- Cache recommendations (Redis, 1 hour)
- Lazy load preview updates
- Debounce preview regeneration
- Stream recommendations as they're generated

### State Management
- Use React Context or Zustand
- Persist session in localStorage
- Allow resuming interrupted sessions

### Accessibility
- Keyboard navigation for recommendations
- Screen reader friendly
- High contrast mode support
- Focus management in modals

## Success Metrics

### User Engagement
- % of users who use tailoring vs. direct export
- Average number of recommendations accepted
- Time spent reviewing recommendations
- Conversion from preview to export

### Quality
- User satisfaction ratings
- CV match score improvement
- Interview rate increase
- User feedback on recommendations

## Next Steps

1. **Review and Approve Plan**: Discuss architecture decisions
2. **Create Backend Services**: Start with recommendation engine
3. **Design UI Mockups**: Get user feedback on flow
4. **Implement MVP**: Focus on core workflow first
5. **Iterate Based on Usage**: Add advanced features based on data

## Files to Create/Modify

### Backend
- `backend/app/services/cv_analyzer.py` (new)
- `backend/app/services/recommendation_engine.py` (new)
- `backend/app/api/routes/tailor.py` (modify - add new endpoints)
- `backend/app/models/tailoring.py` (new - Pydantic models)

### Frontend
- `src/components/tailoring/TailoringWorkflow.tsx` (new)
- `src/components/tailoring/RecommendationCard.tsx` (new)
- `src/components/tailoring/CVPreview.tsx` (new)
- `src/components/tailoring/RecommendationFilters.tsx` (new)
- `src/contexts/TailoringContext.tsx` (new)
- `src/pages/TailorCV.tsx` (modify - integrate workflow)

### API
- `src/lib/api.ts` (modify - add tailoring endpoints)