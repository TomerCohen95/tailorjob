from typing import Dict, Any, List, Set


class CVComparator:
    """
    Compare normalized CV vs job requirements using pure set operations.
    v4.0: Zero AI involvement = 100% reproducible results.
    """
    
    def __init__(self):
        print("🔧 Initializing CV Comparator v4.0")
    
    def compare_requirements(
        self,
        cv_normalized: Dict[str, Any],
        job_normalized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare CV vs job deterministically using set operations.
        Returns match status for each requirement.
        
        This is the core comparison logic - no AI, just pure rules.
        """
        print(f"🔍 Comparing CV against job requirements")
        
        # Get all CV tech as single set
        cv_all_tech = self._get_all_cv_tech(cv_normalized)
        print(f"   CV has {len(cv_all_tech)} unique technologies")
        
        # Parse job requirements (handles both list and dict formats)
        job_must_requirements = self._parse_requirements(job_normalized.get("must_have", []))
        job_nice_requirements = self._parse_requirements(job_normalized.get("nice_to_have", []))
        
        print(f"   Job requires {len(job_must_requirements)} must-have, {len(job_nice_requirements)} nice-to-have requirements")
        
        # Compare must-have requirements
        matched_must, missing_must = self._match_requirements(
            job_must_requirements, cv_all_tech, cv_normalized, "must_have"
        )
        
        # Compare nice-to-have requirements
        matched_nice, missing_nice = self._match_requirements(
            job_nice_requirements, cv_all_tech, cv_normalized, "nice_to_have"
        )
        
        # Compare experience years
        experience_match = self._compare_experience(cv_normalized, job_normalized)
        
        # Compare education
        education_match = self._compare_education(cv_normalized, job_normalized)
        
        # Compare management requirements
        management_match = self._compare_management(cv_normalized, job_normalized)
        
        print(f"✅ Comparison complete: {len(matched_must)}/{len(job_must_requirements)} must-haves matched")
        
        return {
            "matched_must_have": matched_must,
            "missing_must_have": missing_must,
            "matched_nice_have": matched_nice,
            "missing_nice_have": missing_nice,
            "experience_match": experience_match,
            "education_match": education_match,
            "management_match": management_match
        }
    
    def _parse_requirements(self, requirements: Any) -> List[str]:
        """
        Parse job requirements from database format.
        
        Handles two formats:
        1. List of strings: ["3+ years Python", "Azure knowledge", "Bachelor's degree"]
        2. Dict with skills: {"skills": ["python", "azure"], "education": {...}}
        
        Returns list of requirement strings.
        """
        if isinstance(requirements, list):
            # Database format: list of requirement strings
            return [req for req in requirements if isinstance(req, str)]
        elif isinstance(requirements, dict):
            # Structured format: extract skills
            skills = requirements.get("skills", [])
            return skills if isinstance(skills, list) else []
        else:
            return []
    
    def _match_requirements(
        self,
        requirements: List[str],
        cv_tech: Set[str],
        cv_data: Dict[str, Any],
        req_type: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Match requirements against CV.
        
        Parses requirement strings like "3+ years Python" or "Azure knowledge"
        and checks if CV satisfies them.
        
        Returns: (matched_list, missing_list)
        """
        matched = []
        missing = []
        
        for req in requirements:
            req_lower = req.lower()
            
            # Check if this is a degree requirement
            if "degree" in req_lower or "bachelor" in req_lower or "master" in req_lower:
                # Skip - will be handled by _compare_education
                continue
            
            # Check if this is a management requirement
            if "management" in req_lower or "lead" in req_lower:
                # Skip - will be handled by _compare_management
                continue
            
            # Check if this is an experience years requirement
            if "years" in req_lower and any(word in req_lower for word in ["experience", "backend", "engineering"]):
                # Skip - will be handled by _compare_experience
                continue
            
            # Extract technology/skill name from requirement
            # e.g., "3+ years Python" → "python"
            #       "Azure knowledge" → "azure"
            tech_found = False
            for tech in cv_tech:
                if tech in req_lower or req_lower in tech:
                    matched.append({
                        "requirement": req,
                        "status": "EXACT_MATCH",
                        "evidence": f"CV lists: {tech}",
                        "requirement_type": req_type
                    })
                    tech_found = True
                    break
            
            if not tech_found:
                missing.append({
                    "requirement": req,
                    "status": "NOT_FOUND",
                    "evidence": "Not in CV",
                    "requirement_type": req_type
                })
        
        return matched, missing
    
    def _get_all_cv_tech(self, cv_data: Dict[str, Any]) -> Set[str]:
        """
        Combine all tech fields into single set.
        Includes: skills, languages, frameworks, cloud_platforms, databases, tools
        """
        all_tech = set()
        
        for field in ["skills", "languages", "frameworks", "cloud_platforms", "databases", "tools"]:
            if field in cv_data and isinstance(cv_data[field], list):
                all_tech.update(cv_data[field])
        
        return all_tech
    
    def _compare_skill_set(
        self,
        required_skills: Set[str],
        cv_skills: Set[str],
        req_type: str
    ) -> List[Dict[str, Any]]:
        """
        Compare skill sets using set intersection.
        Returns list of matched requirements with evidence.
        """
        matched = []
        
        for skill in required_skills:
            if skill in cv_skills:
                matched.append({
                    "requirement": skill,
                    "status": "EXACT_MATCH",
                    "evidence": f"CV lists: {skill}",
                    "requirement_type": req_type
                })
        
        return matched
    
    def _compare_experience(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare years of experience requirement.
        Pure arithmetic comparison.
        
        Extracts experience years from requirement strings like:
        - "7+ years backend engineering"
        - "2+ years management experience"
        """
        cv_years = cv_data.get("years_experience_total", 0) or 0
        
        # Extract experience years from must_have requirements
        job_years = 0
        experience_requirements = []
        
        must_have = job_data.get("must_have", [])
        if isinstance(must_have, list):
            for req in must_have:
                # Look for patterns like "7+ years", "2+ years"
                import re
                match = re.search(r'(\d+)\+?\s*years?', req.lower())
                if match:
                    years = int(match.group(1))
                    if years > job_years:
                        job_years = years
                    experience_requirements.append(req)
        
        if job_years == 0:
            # No experience requirement found
            return {
                "requirement": "No experience requirement",
                "status": "MET",
                "evidence": "N/A",
                "cv_years": cv_years,
                "required_years": 0
            }
        
        status = "MET" if cv_years >= job_years else "NOT_MET"
        evidence = f"CV: {cv_years} years, Required: {job_years} years"
        
        return {
            "requirement": f"{job_years}+ years experience",
            "status": status,
            "evidence": evidence,
            "cv_years": cv_years,
            "required_years": job_years
        }
    
    def _compare_education(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare education requirements.
        
        IMPORTANT: "or equivalent degree" means "or equivalent EDUCATIONAL qualification"
        (e.g., Associates, technical degree, bootcamp certificate), NOT "or equivalent experience".
        
        Experience alone does NOT satisfy a degree requirement unless the job explicitly
        says "degree OR equivalent experience" (not just "or equivalent").
        
        Parses requirements from strings like:
        - "Bachelor's degree in computer science or equivalent"
        - "Bachelor's degree or equivalent degree"
        """
        # Extract education requirements from must_have list
        must_have = job_data.get("must_have", [])
        required_degree = None
        or_equivalent = False
        degree_requirement_text = None
        
        if isinstance(must_have, list):
            for req in must_have:
                req_lower = req.lower()
                # Look for degree requirements
                if "degree" in req_lower or "bachelor" in req_lower or "master" in req_lower or "phd" in req_lower:
                    degree_requirement_text = req
                    
                    # Determine degree level
                    if "bachelor" in req_lower:
                        required_degree = "Bachelor"
                    elif "master" in req_lower:
                        required_degree = "Master"
                    elif "phd" in req_lower or "doctorate" in req_lower:
                        required_degree = "PhD"
                    else:
                        required_degree = "Bachelor"  # Default assumption
                    
                    # Check for "or equivalent" clause
                    if "or equivalent" in req_lower:
                        or_equivalent = True
                    
                    break  # Take first degree requirement found
        
        if not required_degree:
            return {
                "requirement": "No degree required",
                "status": "MET",
                "evidence": "N/A",
                "has_formal_degree": False,
                "or_equivalent_allowed": False
            }
        
        # Check for formal degree (Bachelor's or higher)
        has_degree = self._has_formal_degree(cv_data.get("education", []))
        
        # Check for equivalent educational qualifications (Associates, bootcamp, etc.)
        has_equivalent_education = self._has_equivalent_education(cv_data.get("education", []))
        
        # Meets requirement if:
        # 1. Has formal degree (Bachelor's+), OR
        # 2. Has equivalent education AND job allows "or equivalent"
        if has_degree:
            meets_requirement = True
            evidence = "Has formal degree (Bachelor's or higher)"
        elif has_equivalent_education and or_equivalent:
            meets_requirement = True
            evidence = "Has equivalent educational qualification (e.g., Associates, technical degree, bootcamp)"
        else:
            meets_requirement = False
            if or_equivalent:
                evidence = "No formal degree or equivalent educational qualification"
            else:
                evidence = "No formal degree (strict Bachelor's requirement, no equivalents allowed)"
        
        return {
            "requirement": degree_requirement_text or f"{required_degree} degree",
            "status": "MET" if meets_requirement else "NOT_MET",
            "evidence": evidence,
            "has_formal_degree": has_degree,
            "has_equivalent_education": has_equivalent_education,
            "or_equivalent_allowed": or_equivalent
        }
    
    def _has_formal_degree(self, education: List[Dict[str, Any]]) -> bool:
        """
        Check if candidate has bachelor's degree or higher.
        Looks for degree keywords in education entries.
        """
        degree_keywords = [
            "bachelor", "b.sc", "b.s.", "bsc", "ba ", "b.a.", "b.tech",
            "master", "m.sc", "m.s.", "msc", "ma ", "m.a.",
            "phd", "ph.d.", "doctorate"
        ]
        
        for edu in education:
            degree = (edu.get("degree") or "").lower()
            if any(kw in degree for kw in degree_keywords):
                return True
        
        return False
    
    def _has_equivalent_education(self, education: List[Dict[str, Any]]) -> bool:
        """
        Check if candidate has equivalent educational qualification
        (Associates, technical degree, bootcamp, professional certification).
        
        NOTE: This is for "equivalent DEGREE", not "equivalent experience".
        """
        equivalent_keywords = [
            "associate", "a.s.", "a.a.",  # Associates degrees
            "diploma", "certificate",  # Technical diplomas/certificates
            "bootcamp", "coding bootcamp",  # Bootcamps
            "professional certificate",  # Professional certifications
            "technical degree"  # Technical degrees
        ]
        
        for edu in education:
            degree = (edu.get("degree") or "").lower()
            institution = (edu.get("institution") or "").lower()
            field = (edu.get("field") or "").lower()
            
            combined = f"{degree} {institution} {field}"
            
            if any(kw in combined for kw in equivalent_keywords):
                return True
        
        return False
    
    def _compare_management(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare management requirements.
        Looks for leadership signals in CV.
        """
        mgmt_req = job_data.get("management", {})
        mgmt_required = mgmt_req.get("required", False)
        
        if not mgmt_required:
            return {
                "requirement": "No management required",
                "status": "MET",
                "evidence": "N/A"
            }
        
        # Check for management/leadership signals
        seniority_signals = cv_data.get("seniority_signals", [])
        management_keywords = ["lead", "manage", "mentor", "supervised", "directed", "team of"]
        
        has_mgmt = any(
            any(kw in sig.lower() for kw in management_keywords)
            for sig in seniority_signals
        )
        
        # Extract team size if mentioned
        required_team_size = mgmt_req.get("team_size")
        
        if has_mgmt:
            # Find team size mentions
            team_size_mention = next(
                (sig for sig in seniority_signals if "team of" in sig.lower()),
                None
            )
            if team_size_mention:
                evidence = f"Has management experience: {team_size_mention}"
            else:
                evidence = "Has leadership/management experience"
        else:
            evidence = "No management or leadership signals found"
        
        requirement_text = (
            f"Management experience (team of {required_team_size})" 
            if required_team_size 
            else "Management experience"
        )
        
        return {
            "requirement": requirement_text,
            "status": "MET" if has_mgmt else "NOT_MET",
            "evidence": evidence
        }