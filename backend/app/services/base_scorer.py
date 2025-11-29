from typing import Dict, Any


class BaseScorer:
    """
    Calculate base scores using deterministic rules.
    v4.0: No AI involvement = 100% reproducible scores.
    """
    
    def __init__(self):
        print("🔧 Initializing Base Scorer v4.0")
    
    def calculate_base_scores(
        self,
        comparison: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate component scores from comparison results.
        Pure math based on exact matches only (no transferability yet).
        
        Returns:
            {
                "skills_score": int,
                "experience_score": int,
                "qualifications_score": int,
                "breakdown": {...}
            }
        """
        print(f"📊 Calculating base scores (deterministic)")
        
        # Skills score (must-have 80%, nice-to-have 20%)
        skills_score = self._calculate_skills_score(comparison)
        
        # Experience score
        experience_score = self._calculate_experience_score(comparison, cv_data, job_data)
        
        # Qualifications score
        qualifications_score = self._calculate_qualifications_score(comparison)
        
        breakdown = {
            "matched_must_count": len(comparison["matched_must_have"]),
            "total_must_count": len(comparison["matched_must_have"]) + len(comparison["missing_must_have"]),
            "matched_nice_count": len(comparison["matched_nice_have"]),
            "total_nice_count": len(comparison["matched_nice_have"]) + len(comparison["missing_nice_have"])
        }
        
        print(f"   Skills: {skills_score}% (exact matches only)")
        print(f"   Experience: {experience_score}%")
        print(f"   Qualifications: {qualifications_score}%")
        
        return {
            "skills_score": skills_score,
            "experience_score": experience_score,
            "qualifications_score": qualifications_score,
            "breakdown": breakdown
        }
    
    def _calculate_skills_score(self, comparison: Dict[str, Any]) -> int:
        """
        Calculate skills score from exact matches only.
        Formula: (must_have_score * 0.8) + (nice_have_score * 0.2)
        """
        total_must = len(comparison["matched_must_have"]) + len(comparison["missing_must_have"])
        matched_must = len(comparison["matched_must_have"])
        
        total_nice = len(comparison["matched_nice_have"]) + len(comparison["missing_nice_have"])
        matched_nice = len(comparison["matched_nice_have"])
        
        # Must-haves are 80% weight
        must_score = (matched_must / total_must * 100) if total_must > 0 else 100
        
        # Nice-to-haves are 20% weight
        nice_score = (matched_nice / total_nice * 100) if total_nice > 0 else 100
        
        # Weighted combination
        return int(must_score * 0.8 + nice_score * 0.2)
    
    def _calculate_experience_score(
        self,
        comparison: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> int:
        """
        Calculate experience score based on years and seniority.
        Pure rules-based scoring.
        
        Uses the experience comparison result which already parsed years from requirements.
        """
        experience_match = comparison.get("experience_match", {})
        cv_years = experience_match.get("cv_years", 0) or 0
        job_years = experience_match.get("required_years", 0) or 0
        status = experience_match.get("status", "NOT_MET")
        
        # Base score from years comparison
        if job_years == 0:
            # No requirement, score based on absolute years
            if cv_years >= 10:
                score = 100
            elif cv_years >= 5:
                score = 90
            elif cv_years >= 2:
                score = 70
            else:
                score = 50
        else:
            # Score based on meeting requirement
            if cv_years >= job_years * 1.5:
                score = 100  # 150%+ of required = excellent
            elif cv_years >= job_years:
                score = 90   # Meets requirement
            elif cv_years >= job_years * 0.75:
                score = 70   # Close to requirement (75%+)
            elif cv_years >= job_years * 0.5:
                score = 50   # Half of requirement
            else:
                score = 30   # Below half
        
        # Seniority bonus (if job requires senior/lead)
        job_level = (job_data.get("role_level") or "").lower()
        seniority_signals = cv_data.get("seniority_signals", [])
        has_senior = any(
            "senior" in sig.lower() or "lead" in sig.lower()
            for sig in seniority_signals
        )
        
        if ("senior" in job_level or "lead" in job_level) and has_senior:
            score = min(100, score + 10)  # +10% bonus for seniority match
        
        return int(score)
    
    def _calculate_qualifications_score(self, comparison: Dict[str, Any]) -> int:
        """
        Calculate qualifications score from education match.
        Simple binary: meets requirement or not.
        """
        education_match = comparison.get("education_match", {})
        
        if education_match.get("status") == "MET":
            return 100
        else:
            # Partial credit if has some experience
            # (even without formal degree or equivalent)
            return 60