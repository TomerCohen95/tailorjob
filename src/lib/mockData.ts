export interface ParsedCV {
  id: string;
  summary: string;
  skills: string[];
  experience: Array<{
    title: string;
    company: string;
    period: string;
    description: string[];
  }>;
  education: Array<{
    degree: string;
    institution: string;
    year: string;
  }>;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  description: string;
  createdAt: string;
}

export interface TailoredCV {
  jobId: string;
  content: string;
  revisions: Revision[];
}

export interface Revision {
  id: string;
  timestamp: string;
  type: 'ai' | 'user';
  content: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export const mockParsedCV: ParsedCV = {
  id: '1',
  summary: 'Experienced full-stack developer with 5+ years in building scalable web applications. Proficient in React, Node.js, and cloud technologies. Passionate about creating user-centric solutions and mentoring junior developers.',
  skills: [
    'React', 'TypeScript', 'Node.js', 'Python', 'AWS', 'Docker', 
    'PostgreSQL', 'GraphQL', 'REST APIs', 'CI/CD', 'Agile/Scrum'
  ],
  experience: [
    {
      title: 'Senior Full-Stack Developer',
      company: 'TechCorp Inc.',
      period: '2021 - Present',
      description: [
        'Led development of microservices architecture serving 1M+ users',
        'Implemented CI/CD pipelines reducing deployment time by 60%',
        'Mentored team of 5 junior developers',
        'Architected and built real-time collaboration features'
      ]
    },
    {
      title: 'Full-Stack Developer',
      company: 'StartupXYZ',
      period: '2019 - 2021',
      description: [
        'Built and maintained core product features using React and Node.js',
        'Optimized database queries improving performance by 40%',
        'Collaborated with design team to implement pixel-perfect UIs',
        'Participated in code reviews and technical planning sessions'
      ]
    },
    {
      title: 'Junior Developer',
      company: 'Digital Solutions Ltd.',
      period: '2018 - 2019',
      description: [
        'Developed responsive web applications using modern JavaScript frameworks',
        'Fixed bugs and implemented new features based on client feedback',
        'Worked in agile environment with 2-week sprints'
      ]
    }
  ],
  education: [
    {
      degree: 'BSc Computer Science',
      institution: 'University of Technology',
      year: '2018'
    }
  ]
};

export const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior React Developer',
    company: 'Acme Corp',
    description: `We are seeking a Senior React Developer to join our growing team...

Key Responsibilities:
- Lead frontend architecture decisions
- Mentor junior developers
- Build scalable React applications
- Collaborate with design and backend teams

Requirements:
- 5+ years of React experience
- Strong TypeScript skills
- Experience with state management (Redux, Zustand)
- Knowledge of modern build tools and CI/CD
- Excellent communication skills`,
    createdAt: '2024-01-15'
  },
  {
    id: '2',
    title: 'Full-Stack Engineer',
    company: 'InnovateTech',
    description: `Join our team as a Full-Stack Engineer working on cutting-edge SaaS products...

What you'll do:
- Build and maintain full-stack features
- Work with React, Node.js, and PostgreSQL
- Participate in architectural decisions
- Deploy to AWS cloud infrastructure

Requirements:
- 4+ years full-stack experience
- Strong JavaScript/TypeScript
- Database design experience
- Cloud platform knowledge (AWS/GCP)`,
    createdAt: '2024-01-20'
  }
];

export const mockTailoredCV = `# JOHN DOE
Senior Full-Stack Developer | React & Node.js Specialist

## PROFESSIONAL SUMMARY
Experienced full-stack developer with 5+ years building scalable web applications, specializing in React and TypeScript. Proven track record of leading frontend architecture decisions and mentoring development teams. Expert in modern JavaScript ecosystems and state management solutions.

## TECHNICAL SKILLS
**Frontend:** React, TypeScript, Redux, Zustand, Next.js, Tailwind CSS
**Backend:** Node.js, Express, GraphQL, REST APIs
**Tools & Practices:** Git, CI/CD, Agile/Scrum, Code Review
**Cloud & DevOps:** AWS, Docker, Kubernetes

## PROFESSIONAL EXPERIENCE

### Senior Full-Stack Developer | TechCorp Inc. | 2021 - Present
- **Led frontend architecture decisions** for microservices platform serving 1M+ users
- **Mentored team of 5 junior developers** on React best practices and TypeScript
- Built scalable React applications using modern state management (Redux, Context API)
- Implemented CI/CD pipelines reducing deployment time by 60%
- Collaborated closely with design team ensuring pixel-perfect UI implementation

### Full-Stack Developer | StartupXYZ | 2019 - 2021
- Built and maintained core product features using **React, TypeScript, and Node.js**
- Established code review processes improving code quality and team collaboration
- Optimized application performance and database queries (40% improvement)
- Worked in agile environment with cross-functional teams

### Junior Developer | Digital Solutions Ltd. | 2018 - 2019
- Developed responsive web applications using modern JavaScript frameworks
- Participated in agile sprints and team code reviews
- Gained foundational experience in full-stack development

## EDUCATION
**BSc Computer Science** | University of Technology | 2018

## KEY ACHIEVEMENTS
- Led migration from class components to hooks improving codebase maintainability
- Established component library used across 3 product teams
- Reduced bundle size by 35% through code splitting and optimization
`;

export const mockChatMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'assistant',
    content: "I've tailored your CV to emphasize your React expertise and leadership experience. The key changes include highlighting your frontend architecture work and mentorship experience. What would you like to adjust?",
    timestamp: new Date().toISOString()
  }
];

export const mockRevisions: Revision[] = [
  {
    id: '1',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    type: 'ai',
    content: 'Initial AI-tailored version'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    type: 'user',
    content: 'User edited summary section'
  },
  {
    id: '3',
    timestamp: new Date().toISOString(),
    type: 'ai',
    content: 'AI enhanced skills section'
  }
];
