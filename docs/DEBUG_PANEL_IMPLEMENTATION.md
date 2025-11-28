# Debug Panel Implementation

## Overview
Added a comprehensive debug panel to the TailorCV page that displays all raw matching data in a formatted, copyable format for LLM judge evaluation.

## Changes Made

### 1. Type Definitions Updated (`src/lib/api.ts`)

**Job Interface:**
- Added `url?: string` - Optional job URL
- Added `requirements_matrix?` - Structured requirements (must_have/nice_to_have arrays)

**MatchScore Interface:**
- Added `deterministic_score?: number` - Deterministic matching score (85% must-have + 15% nice-to-have)
- Added `fit_score?: number` - LLM-based holistic fit assessment (0-100)
- Added `must_have_score?: number` - Score for must-have requirements
- Added `nice_to_have_score?: number` - Score for nice-to-have requirements
- Kept existing fields: `overall_score`, `skills_score`, `experience_score`, `qualifications_score`, `analysis`, `cached`, `created_at`

### 2. New Component (`src/components/cv/MatchDebugPanel.tsx`)

**Features:**
- Collapsible accordion with three main sections:
  1. **Job Information** - Company, title, description, requirements matrix
  2. **Candidate CV** - All parsed sections (summary, skills, experience, education, certifications)
  3. **Matcher Decision** - All scores, analysis, matched/missing items

- **Copy-to-Clipboard Functionality:**
  - Copy individual sections (job, CV, matcher decision)
  - Copy complete formatted data for LLM evaluation
  - Toast notifications on successful copy

- **Component Score Breakdown:**
  - Visual cards showing deterministic vs fit score components
  - Formula display: `Overall = (Deterministic × 0.70) + (Fit × 0.30)`
  - Sub-scores: Must-have, Nice-to-have, Skills, Experience, Qualifications

- **Formatted JSON Display:**
  - Syntax-highlighted, indented JSON
  - Monospace font for readability
  - Scrollable containers

### 3. Integration in TailorCV Page (`src/pages/TailorCV.tsx`)

**New State:**
- `cvData: CVWithSections | null` - Stores parsed CV data
- `loadingCv: boolean` - Loading state for CV data fetch

**New Functions:**
- `loadCvData()` - Fetches CV data via `cvAPI.get(primaryCvId)`

**UI Changes:**
- Debug panel appears in Match Analysis tab
- Only shows when both `matchScore` and `cvData` are loaded
- Positioned below MatchScorePanel
- Container width increased to `max-w-5xl` to accommodate wider debug panel

## Usage

1. **Navigate to TailorCV page** for any job
2. **Click "Match Analysis" tab**
3. **Click "Analyze Match"** button to generate match score
4. **Debug panel appears automatically** below the match score panel
5. **Expand sections** to view job, CV, or matcher data
6. **Click "Copy ..." buttons** to copy specific sections
7. **Click "Copy Complete Data"** to copy everything for LLM evaluation

## Data Structure for LLM Judge

The complete data includes:

```json
{
  "job": {
    "id": "...",
    "title": "...",
    "company": "...",
    "description": "...",
    "url": "...",
    "requirements_matrix": {
      "must_have": [...],
      "nice_to_have": [...]
    }
  },
  "candidate_cv": {
    "cv": { /* metadata */ },
    "sections": {
      "summary": "...",
      "skills": "...",
      "experience": "...",
      "education": "...",
      "certifications": "..."
    }
  },
  "matcher_decision": {
    "overall_score": 85,
    "deterministic_score": 88,
    "fit_score": 75,
    "must_have_score": 90,
    "nice_to_have_score": 70,
    "category_scores": {
      "skills_score": 85,
      "experience_score": 88,
      "qualifications_score": 82
    },
    "analysis": {
      "strengths": [...],
      "gaps": [...],
      "recommendations": [...],
      "matched_skills": [...],
      "missing_skills": [...],
      "matched_qualifications": [...],
      "missing_qualifications": [...]
    }
  }
}
```

## Benefits

1. **Transparency** - Full visibility into matching logic
2. **Debugging** - Easy identification of matching issues
3. **LLM Evaluation** - Copy-paste ready format for external AI judges
4. **Iterative Improvement** - Compare versions by copying data at different points
5. **Audit Trail** - Complete record of matching decisions

## Future Enhancements

- Add export to JSON file option
- Add historical comparison view (compare multiple match runs)
- Add filtering/search within debug data
- Add "Explain this decision" button that sends data to LLM for natural language explanation