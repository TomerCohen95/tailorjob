from typing import Dict, Any


class FinalScorer:
    """
    Combine base scores + transferability into final score.
    v4.0: Formula is deterministic, only transferability ratings vary slightly.
    """
    
    def __init__(self):
        print("🔧 Initializing Final Scorer v4.0")
    
    def calculate_final_scores(
        self,
        base_scores: Dict[str, Any],
        transferability: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate final scores using hybrid approach.
        Base scores (deterministic) + Transferability credits (AI-assisted)
        
        Returns:
            {
                "overall_score": int,
                "skills_score": int,
                "experience_score": int,
                "qualifications_score": int,
                "base_skills_score": int,
                "transferability_details": [...],
                "scoring_method": str
            }
        """
        print(f"📊 Calculating final scores with transferability")
        
        # Add transferability credits to skills score
        skills_score = self._calculate_skills_with_transferability(
            base_scores, transferability, comparison
        )
        
        # Experience and qualifications remain from base scores
        experience_score = base_scores["experience_score"]
        qualifications_score = base_scores["qualifications_score"]
        
        # Overall score (weighted average)
        # Skills: 50%, Experience: 35%, Qualifications: 15%
        overall_score = int(
            skills_score * 0.5 +
            experience_score * 0.35 +
            qualifications_score * 0.15
        )
        
        print(f"   Final Skills: {skills_score}% (base: {base_scores['skills_score']}%)")
        print(f"   Final Overall: {overall_score}%")
        
        return {
            "overall_score": overall_score,
            "skills_score": skills_score,
            "experience_score": experience_score,
            "qualifications_score": qualifications_score,
            "base_skills_score": base_scores["skills_score"],
            "transferability_details": transferability["assessments"],
            "scoring_method": "v4.0 (base + transferability)"
        }
    
    def _calculate_skills_with_transferability(
        self,
        base_scores: Dict[str, Any],
        transferability: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> int:
        """
        Add transferability credits to base skills score.
        
        Formula: (exact_matches + transferable_credits) / total_requirements * 100
        
        Example:
            5 must-have requirements
            3 exact matches (60%)
            2 missing with transferability 0.7 each (1.4 credits)
            Final: (3 + 1.4) / 5 = 88%
        """
        
        total_must = base_scores["breakdown"]["total_must_count"]
        exact_must = base_scores["breakdown"]["matched_must_count"]
        
        if total_must == 0:
            # No must-have requirements
            return 100
        
        # Calculate transferable credits from missing must-haves
        transferable_credit = 0.0
        missing_must_reqs = {r["requirement"] for r in comparison["missing_must_have"]}
        
        for assessment in transferability["assessments"]:
            if assessment["requirement"] in missing_must_reqs:
                transferable_credit += assessment["transferability_score"]
        
        # Must-have score with transferability
        must_score_with_transfer = ((exact_must + transferable_credit) / total_must * 100)
        
        # Nice-to-have score (no transferability for now - can be added later)
        total_nice = base_scores["breakdown"]["total_nice_count"]
        exact_nice = base_scores["breakdown"]["matched_nice_count"]
        nice_score = (exact_nice / total_nice * 100) if total_nice > 0 else 100
        
        # Weighted combination (80% must, 20% nice)
        final_skills = must_score_with_transfer * 0.8 + nice_score * 0.2
        
        # Cap at 100%
        return min(100, int(final_skills))