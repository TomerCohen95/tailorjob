# CV Parsing UX Flow Diagrams

## System Architecture

```mermaid
graph TB
    subgraph "Frontend (React)"
        Upload[Upload CV Page]
        Context[CV Parsing Context]
        Toast[Parsing Toast Component]
        Celebration[Completion Notification]
        Dashboard[Dashboard]
        CVPreview[CV Preview Page]
        Nav[Navigation Bar]
    end
    
    subgraph "Backend (FastAPI)"
        API[CV API Endpoints]
        Queue[Redis Queue]
        Worker[CV Worker]
    end
    
    subgraph "Storage"
        Supabase[(Supabase DB)]
        Redis[(Redis Cache)]
        Storage[Supabase Storage]
    end
    
    Upload -->|1. Upload File| API
    API -->|2. Store File| Storage
    API -->|3. Create CV Record| Supabase
    API -->|4. Enqueue Job| Queue
    
    Queue -->|5. Dequeue Job| Worker
    Worker -->|6. Update Progress| Redis
    Worker -->|7. Parse Content| Worker
    Worker -->|8. Save Sections| Supabase
    Worker -->|9. Create Notification| Supabase
    
    Context -->|Poll Progress| API
    API -->|Read Progress| Redis
    Context -->|Update State| Toast
    Context -->|Update State| Dashboard
    Context -->|Update State| CVPreview
    Context -->|Update State| Nav
    
    Worker -->|Completion| Context
    Context -->|Trigger| Celebration
```

## User Flow - Happy Path

```mermaid
sequenceDiagram
    actor User
    participant Upload as Upload Page
    participant Context as Parsing Context
    participant API as Backend API
    participant Worker as CV Worker
    participant Toast as Parsing Toast
    participant Celebration as Success Notification
    
    User->>Upload: 1. Select & upload CV file
    Upload->>API: 2. POST /api/cv/upload
    API->>API: 3. Store file, create DB record
    API->>Worker: 4. Enqueue parsing job
    API->>Upload: 5. Return cv_id + job_id
    
    Upload->>Context: 6. startParsing(cv_id)
    Context->>Toast: 7. Show "Parsing Started"
    
    Note over User,Toast: User can navigate anywhere
    
    User->>Dashboard: 8. Navigate to dashboard
    
    loop Every 2 seconds
        Context->>API: 9. GET /api/cv/{cv_id}/progress
        Worker->>API: (Background) Update progress
        API->>Context: 10. Return progress data
        Context->>Toast: 11. Update progress bar
        Context->>Dashboard: 12. Update status card
    end
    
    Worker->>Worker: 13. Complete parsing
    Worker->>API: 14. Update status to "parsed"
    Worker->>API: 15. Create notification
    
    Context->>API: 16. Poll detects completion
    Context->>Celebration: 17. Show celebration 🎉
    Context->>Toast: 18. Hide parsing toast
    
    User->>Celebration: 19. Click "View Your CV"
    Celebration->>CVPreview: 20. Navigate with parsed data
```

## Component State Flow

```mermaid
stateDiagram-v2
    [*] --> Idle: App starts
    Idle --> Uploading: User uploads CV
    Uploading --> Parsing: Upload complete
    Parsing --> Parsed: Worker completes
    Parsing --> Error: Worker fails
    Parsed --> [*]: User dismisses
    Error --> Idle: User retries
    
    state Parsing {
        [*] --> Stage1: Extracting text (20%)
        Stage1 --> Stage2: Parsing summary (40%)
        Stage2 --> Stage3: Parsing experience (60%)
        Stage3 --> Stage4: Parsing education (80%)
        Stage4 --> Stage5: Parsing skills (90%)
        Stage5 --> [*]: Finalizing (100%)
    }
```

## Page-Level UX States

### Dashboard States

```mermaid
stateDiagram-v2
    [*] --> NoCV: First visit
    NoCV --> Parsing: Upload CV
    Parsing --> Parsed: Success
    Parsing --> Error: Failed
    Parsed --> Parsing: Upload new CV
    Error --> Parsing: Retry
    
    state NoCV {
        [*] --> ShowEmptyState
        ShowEmptyState --> ShowUploadPrompt
    }
    
    state Parsing {
        [*] --> ShowProgressCard
        ShowProgressCard --> UpdateProgress: Every 2s
        UpdateProgress --> ShowProgressCard
    }
    
    state Parsed {
        [*] --> ShowCVSummary
        ShowCVSummary --> ShowMatchingJobs
    }
```

### CVPreview States

```mermaid
stateDiagram-v2
    [*] --> CheckCV: Page load
    CheckCV --> NoCV: No CV found
    CheckCV --> Parsing: CV parsing
    CheckCV --> Parsed: CV ready
    
    state NoCV {
        [*] --> ShowEmptyMessage
        ShowEmptyMessage --> ShowUploadButton
        ShowUploadButton --> [*]: Click redirects to upload
    }
    
    state Parsing {
        [*] --> ShowParsingIndicator
        ShowParsingIndicator --> ShowProgressBar
        ShowProgressBar --> ShowStageInfo
        ShowStageInfo --> PollProgress
        PollProgress --> ShowProgressBar: Update
        PollProgress --> Parsed: Complete
    }
    
    state Parsed {
        [*] --> ShowCVSections
        ShowCVSections --> EnableActions
    }
```

## Notification System Flow

```mermaid
graph LR
    subgraph "Trigger Events"
        E1[CV Upload]
        E2[Parsing Start]
        E3[Progress Update]
        E4[Parsing Complete]
        E5[Parsing Error]
    end
    
    subgraph "Notification Types"
        N1[Toast: Persistent Progress]
        N2[Toast: Completion Celebration]
        N3[Dashboard Card: Detailed Status]
        N4[Nav Icon: Active Indicator]
        N5[Database: Permanent Record]
    end
    
    E1 --> N1
    E2 --> N1
    E3 --> N1
    E3 --> N3
    E4 --> N2
    E4 --> N5
    E5 --> N3
    
    N1 -.-> N4
    N3 -.-> N4
```

## Data Flow Architecture

```mermaid
graph TB
    subgraph "Frontend State"
        LS[localStorage]
        Context[Parsing Context]
        Components[UI Components]
    end
    
    subgraph "API Layer"
        Progress[/api/cv/:id/progress]
        Status[/api/cv/:id]
        Notifications[/api/cv/notifications]
    end
    
    subgraph "Backend State"
        Redis[(Redis - Progress)]
        Postgres[(Postgres - CV Data)]
        Worker[CV Worker]
    end
    
    Context <-->|Read/Write| LS
    Context -->|Poll| Progress
    Context -->|Fetch| Status
    Context -->|Fetch| Notifications
    
    Progress -->|Read| Redis
    Status -->|Read| Postgres
    Notifications -->|Read| Postgres
    
    Worker -->|Write Progress| Redis
    Worker -->|Write Status| Postgres
    Worker -->|Create| Postgres
    
    Context -->|Update| Components
```

## Mobile vs Desktop Experience

```mermaid
graph TB
    subgraph "Desktop Experience"
        D1[Full-width Toast at top]
        D2[Large progress cards]
        D3[Detailed stage information]
        D4[Action buttons prominent]
    end
    
    subgraph "Mobile Experience"
        M1[Compact bottom toast]
        M2[Swipeable mini-cards]
        M3[Essential info only]
        M4[Thumb-friendly buttons]
        M5[Haptic feedback]
    end
    
    subgraph "Shared Logic"
        Context[Parsing Context]
        API[API Calls]
    end
    
    Context --> D1
    Context --> D2
    Context --> M1
    Context --> M2
    
    API --> D3
    API --> M3
```

## Error Handling Flow

```mermaid
flowchart TD
    Start[User uploads CV] --> Upload{Upload Success?}
    
    Upload -->|Yes| Queue{Queue Job?}
    Upload -->|No| E1[Show upload error]
    
    Queue -->|Yes| Parse{Parsing Success?}
    Queue -->|No| E2[Show queue error + retry]
    
    Parse -->|Yes| Success[Show celebration]
    Parse -->|Timeout| E3[Show timeout + retry]
    Parse -->|Error| E4[Show parse error + retry]
    
    E1 --> End1[User retries upload]
    E2 --> Retry1[Auto-retry in 5s]
    E3 --> Retry2[Manual retry button]
    E4 --> Retry3[Manual retry button]
    
    Retry1 --> Queue
    Retry2 --> Parse
    Retry3 --> Parse
    
    Success --> End2[User continues]
```

## Performance Optimization

```mermaid
graph TB
    subgraph "Optimization Strategies"
        O1[Smart Polling]
        O2[Shared Context]
        O3[localStorage Cache]
        O4[Request Batching]
        O5[Progressive Enhancement]
    end
    
    subgraph "Results"
        R1[Reduced API Calls]
        R2[Faster Perception]
        R3[Survives Refresh]
        R4[Lower Server Load]
        R5[Works Offline]
    end
    
    O1 --> R1
    O1 --> R4
    O2 --> R1
    O3 --> R3
    O3 --> R5
    O4 --> R4
    O5 --> R2
```

## Implementation Phases Timeline

```mermaid
gantt
    title CV Parsing UX Overhaul Timeline
    dateFormat YYYY-MM-DD
    section Phase 1: Foundation
    Context Provider           :done, p1a, 2024-01-15, 2d
    Backend Progress API       :done, p1b, 2024-01-15, 2d
    Redis Progress Storage     :done, p1c, 2024-01-16, 1d
    
    section Phase 2: Visual
    Parsing Toast              :active, p2a, 2024-01-17, 2d
    Celebration Notification   :p2b, 2024-01-18, 1d
    Dashboard Status Card      :p2c, 2024-01-19, 1d
    
    section Phase 3: Pages
    CVPreview Updates          :p3a, 2024-01-20, 1d
    Dashboard Integration      :p3b, 2024-01-21, 1d
    Navigation Updates         :p3c, 2024-01-21, 1d
    
    section Phase 4: Polish
    Smart Polling              :p4a, 2024-01-22, 1d
    Progress Estimator         :p4b, 2024-01-23, 1d
    Mobile Optimization        :p4c, 2024-01-24, 1d
    
    section Phase 5: Testing
    Integration Testing        :p5a, 2024-01-25, 1d
    E2E Testing                :p5b, 2024-01-26, 1d
    Production Deploy          :milestone, p5c, 2024-01-27, 0d