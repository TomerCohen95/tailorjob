from typing import List, Dict, Any, Set


class SkillNormalizer:
    """
    Normalize skills to canonical names.
    v4.0: Eliminates semantic drift (React.js vs React vs ReactJS)
    """
    
    # Canonical skill mappings
    SKILL_MAPPINGS = {
        # Languages
        "golang": "go",
        "go lang": "go",
        "javascript": "js",
        "typescript": "ts",
        "node.js": "nodejs",
        "node": "nodejs",
        "python3": "python",
        "python 3": "python",
        "c++": "cpp",
        "c#": "csharp",
        ".net": "dotnet",
        
        # Frontend Frameworks
        "react.js": "react",
        "reactjs": "react",
        "react js": "react",
        "angular.js": "angular",
        "angularjs": "angular",
        "angular js": "angular",
        "vue.js": "vue",
        "vuejs": "vue",
        "vue js": "vue",
        "next.js": "nextjs",
        "nextjs": "nextjs",
        
        # Backend Frameworks
        "django": "django",
        "flask": "flask",
        "fastapi": "fastapi",
        "express.js": "express",
        "expressjs": "express",
        "spring boot": "spring",
        "springboot": "spring",
        
        # Cloud Platforms
        "aws": "amazon web services",
        "amazon web services": "amazon web services",
        "gcp": "google cloud",
        "google cloud platform": "google cloud",
        "google cloud": "google cloud",
        "azure": "azure",
        "azure cloud services": "azure",
        "microsoft azure": "azure",
        
        # Databases
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "mongo": "mongodb",
        "mongodb": "mongodb",
        "mysql": "mysql",
        "mssql": "sql server",
        "sql server": "sql server",
        "microsoft sql server": "sql server",
        "redis": "redis",
        "dynamodb": "dynamodb",
        "cosmosdb": "cosmosdb",
        
        # Tools & DevOps
        "git": "git",
        "github": "github",
        "gitlab": "gitlab",
        "docker": "docker",
        "k8s": "kubernetes",
        "kubernetes": "kubernetes",
        "jenkins": "jenkins",
        "circleci": "circleci",
        "github actions": "github actions",
        "gitlab ci": "gitlab ci",
        "terraform": "terraform",
        "ansible": "ansible",
        
        # Big Data & Analytics
        "spark": "apache spark",
        "apache spark": "apache spark",
        "presto": "presto",
        "trino": "trino",
        "athena": "aws athena",
        "aws athena": "aws athena",
        "drill": "apache drill",
        "apache drill": "apache drill",
        "hadoop": "hadoop",
        "kafka": "apache kafka",
        "apache kafka": "apache kafka",
    }
    
    def __init__(self):
        print("🔧 Initializing Skill Normalizer v4.0")
        print(f"   Loaded {len(self.SKILL_MAPPINGS)} skill mappings")
    
    def normalize_skill(self, skill: str) -> str:
        """
        Normalize single skill to canonical name.
        
        Examples:
            "React.js" → "react"
            "Node.js" → "nodejs"
            "AWS" → "amazon web services"
        """
        if not skill:
            return skill
        
        skill_lower = skill.lower().strip()
        return self.SKILL_MAPPINGS.get(skill_lower, skill_lower)
    
    def normalize_cv_data(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all tech fields in CV data.
        Returns new dict with normalized fields.
        """
        normalized = cv_data.copy()
        
        # Normalize all tech-related fields
        for field in ["skills", "languages", "frameworks", "cloud_platforms", "databases", "tools"]:
            if field in normalized and isinstance(normalized[field], list):
                normalized[field] = [
                    self.normalize_skill(s) 
                    for s in normalized[field]
                ]
        
        # Normalize technologies in experience entries
        if "experience" in normalized and isinstance(normalized["experience"], list):
            for exp in normalized["experience"]:
                if "technologies" in exp and isinstance(exp["technologies"], list):
                    exp["technologies"] = [
                        self.normalize_skill(t)
                        for t in exp["technologies"]
                    ]
        
        # Normalize technologies in projects
        if "projects" in normalized and isinstance(normalized["projects"], list):
            for proj in normalized["projects"]:
                if "technologies" in proj and isinstance(proj["technologies"], list):
                    proj["technologies"] = [
                        self.normalize_skill(t)
                        for t in proj["technologies"]
                    ]
        
        return normalized
    
    def normalize_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all tech fields in job requirements.
        
        Handles two formats:
        1. From database: {"must_have": ["Python 3+", ...], "nice_to_have": [...]}
        2. Structured: {"must_have": {"skills": [...], "education": {...}}}
        
        Returns new dict with normalized fields.
        """
        normalized = job_data.copy()
        
        # Handle database format: must_have/nice_to_have are lists of requirement strings
        if "must_have" in normalized and isinstance(normalized["must_have"], list):
            # Keep as list - comparator will handle parsing
            normalized["must_have"] = [
                self._normalize_requirement_string(req)
                for req in normalized["must_have"]
            ]
        elif "must_have" in normalized and isinstance(normalized["must_have"], dict):
            # Handle structured format
            if "skills" in normalized["must_have"] and isinstance(normalized["must_have"]["skills"], list):
                normalized["must_have"]["skills"] = [
                    self.normalize_skill(s)
                    for s in normalized["must_have"]["skills"]
                ]
        
        # Handle nice_to_have similarly
        if "nice_to_have" in normalized and isinstance(normalized["nice_to_have"], list):
            normalized["nice_to_have"] = [
                self._normalize_requirement_string(req)
                for req in normalized["nice_to_have"]
            ]
        elif "nice_to_have" in normalized and isinstance(normalized["nice_to_have"], dict):
            if "skills" in normalized["nice_to_have"] and isinstance(normalized["nice_to_have"]["skills"], list):
                normalized["nice_to_have"]["skills"] = [
                    self.normalize_skill(s)
                    for s in normalized["nice_to_have"]["skills"]
                ]
        
        return normalized
    
    def _normalize_requirement_string(self, requirement: str) -> str:
        """
        Normalize a requirement string like "3+ years Python" or "Azure knowledge".
        Extracts technology names and normalizes them.
        """
        if not requirement:
            return requirement
        
        req_lower = requirement.lower()
        
        # Try to normalize any tech words in the requirement
        for original, canonical in self.SKILL_MAPPINGS.items():
            if original in req_lower:
                req_lower = req_lower.replace(original, canonical)
        
        return req_lower
    
    def get_all_cv_tech(self, cv_data: Dict[str, Any]) -> Set[str]:
        """
        Extract all technical skills from CV into single set.
        Includes skills, languages, frameworks, cloud, databases, tools.
        """
        all_tech = set()
        
        for field in ["skills", "languages", "frameworks", "cloud_platforms", "databases", "tools"]:
            if field in cv_data and isinstance(cv_data[field], list):
                all_tech.update(cv_data[field])
        
        return all_tech