from app.services.cv_extractor_v4 import CVExtractorV4
from app.services.skill_normalizer import SkillNormalizer
from app.services.cv_comparator import CVComparator
from app.services.base_scorer import BaseScorer
from app.services.transferability_assessor import TransferabilityAssessor
from app.services.final_scorer import FinalScorer
from app.services.explanation_generator import ExplanationGenerator
from typing import Dict, Any
from datetime import datetime
import json


class CVMatcherServiceV4:
    """
    CV Matcher v4.0 - Extract → Normalize → Compare → Score → Explain
    
    Architecture:
    1. Extract CV facts (AI - zero hallucination)
    2. Normalize skills (Rules - eliminate semantic drift)
    3. Compare requirements (Rules - 100% reproducible)
    4. Base scoring (Rules - deterministic)
    5. Transferability assessment (AI - narrow scope)
    6. Final scoring (Rules + AI transferability)
    7. Explanation generation (AI - constrained)
    """
    
    def __init__(self):
        print("🔧 Initializing CV Matcher v4.0")
        
        self.extractor = CVExtractorV4()
        self.normalizer = SkillNormalizer()
        self.comparator = CVComparator()
        self.base_scorer = BaseScorer()
        self.transferability = TransferabilityAssessor()
        self.final_scorer = FinalScorer()
        self.explanation = ExplanationGenerator()
        
        print("✅ CV Matcher v4.0 initialized successfully")
    
    async def analyze_match(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for v4.0 matching.
        
        Args:
            cv_data: CV with sections (from database)
            job_data: Job with requirements_matrix
        
        Returns:
            Match analysis with scores, strengths, gaps, recommendations
        """
        
        print(f"\n{'='*60}")
        print(f"🎯 [v4.0] Analyzing CV match for job: {job_data.get('title')}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Extract CV facts (AI - zero hallucination)
            cv_text = self._format_cv_text(cv_data)
            cv_extracted = await self.extractor.extract_cv_facts(cv_text)
            
            # Step 2: Job requirements (already extracted by scraper)
            job_requirements = job_data.get("requirements_matrix", {})
            
            if not job_requirements:
                print("⚠️ No requirements_matrix in job data, cannot match")
                return self._generate_fallback_result()
            
            # Step 3: Normalize (Rules)
            cv_normalized = self.normalizer.normalize_cv_data(cv_extracted)
            job_normalized = self.normalizer.normalize_job_data(job_requirements)
            
            # Step 4: Deterministic comparison (Rules)
            comparison = self.comparator.compare_requirements(cv_normalized, job_normalized)
            
            # Step 5A: Base scoring (Rules)
            base_scores = self.base_scorer.calculate_base_scores(
                comparison, cv_normalized, job_normalized
            )
            
            # Step 5B: Transferability assessment (AI - narrow scope)
            cv_all_skills = list(self.normalizer.get_all_cv_tech(cv_normalized))
            transferability = await self.transferability.assess_missing_skills(
                cv_skills=cv_all_skills,
                missing_requirements=comparison["missing_must_have"],
                cv_years=cv_normalized.get("years_experience_total", 0) or 0,
                cv_domain=cv_normalized.get("domain_expertise", []),
                job_domain=job_normalized.get("domain", "")
            )
            
            # Step 5C: Final scoring (Rules + transferability)
            scores = self.final_scorer.calculate_final_scores(
                base_scores, transferability, comparison
            )
            
            # Step 6: AI explanation (Constrained)
            explanation = await self.explanation.generate_explanation(
                cv_normalized, job_normalized, comparison, transferability, scores
            )
            
            # Build final result
            result = self._build_final_result(
                scores, comparison, transferability, explanation, cv_normalized, job_normalized
            )
            
            print(f"\n{'='*60}")
            print(f"✅ [v4.0] Match analysis complete: {result['overall_score']}% match")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"❌ [v4.0] Match analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _format_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """
        Format CV sections into text for extraction.
        Handles both string and structured data formats.
        """
        sections = cv_data.get("sections", {})
        
        text_parts = []
        
        # Summary
        if "summary" in sections and sections["summary"]:
            text_parts.append(f"SUMMARY:\n{sections['summary']}\n")
        
        # Experience
        if "experience" in sections and sections["experience"]:
            exp = sections["experience"]
            if isinstance(exp, str):
                text_parts.append(f"EXPERIENCE:\n{exp}\n")
            elif isinstance(exp, list):
                text_parts.append(f"EXPERIENCE:\n{json.dumps(exp, indent=2)}\n")
        
        # Skills
        if "skills" in sections and sections["skills"]:
            skills = sections["skills"]
            if isinstance(skills, str):
                text_parts.append(f"SKILLS:\n{skills}\n")
            elif isinstance(skills, dict):
                text_parts.append(f"SKILLS:\n{json.dumps(skills, indent=2)}\n")
        
        # Education
        if "education" in sections and sections["education"]:
            edu = sections["education"]
            if isinstance(edu, str):
                text_parts.append(f"EDUCATION:\n{edu}\n")
            elif isinstance(edu, list):
                text_parts.append(f"EDUCATION:\n{json.dumps(edu, indent=2)}\n")
        
        # Certifications
        if "certifications" in sections and sections["certifications"]:
            certs = sections["certifications"]
            if isinstance(certs, str):
                text_parts.append(f"CERTIFICATIONS:\n{certs}\n")
            elif isinstance(certs, list):
                text_parts.append(f"CERTIFICATIONS:\n{json.dumps(certs, indent=2)}\n")
        
        return "\n".join(text_parts) if text_parts else "No CV data available"
    
    def _build_final_result(
        self,
        scores: Dict[str, Any],
        comparison: Dict[str, Any],
        transferability: Dict[str, Any],
        explanation: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build final match result in expected format"""
        
        # Extract matched/missing skill lists
        matched_skills = [r["requirement"] for r in comparison["matched_must_have"]]
        missing_skills = [r["requirement"] for r in comparison["missing_must_have"]]
        
        # Extract education details
        education_match = comparison.get("education_match", {})
        matched_qualifications = []
        missing_qualifications = []
        
        if education_match.get("status") == "MET":
            matched_qualifications.append(education_match["evidence"])
        else:
            if education_match.get("requirement"):
                missing_qualifications.append(education_match["requirement"])
        
        # Build result
        return {
            # Scores
            "overall_score": scores["overall_score"],
            "skills_score": scores["skills_score"],
            "experience_score": scores["experience_score"],
            "qualifications_score": scores["qualifications_score"],
            
            # Additional score details
            "base_skills_score": scores.get("base_skills_score", scores["skills_score"]),
            "scoring_method": scores.get("scoring_method", "v4.0"),
            
            # Skills matching
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            
            # Qualifications
            "matched_qualifications": matched_qualifications,
            "missing_qualifications": missing_qualifications,
            
            # Explanations
            "strengths": explanation.get("strengths", []),
            "gaps": explanation.get("gaps", []),
            "recommendations": explanation.get("recommendations", []),
            
            # Transferability details
            "transferability_details": transferability.get("assessments", []),
            
            # Metadata
            "analyzed_at": datetime.utcnow().isoformat(),
            "matcher_version": "4.0"
        }
    
    def _generate_fallback_result(self) -> Dict[str, Any]:
        """Generate fallback result when matching fails"""
        return {
            "overall_score": 0,
            "skills_score": 0,
            "experience_score": 0,
            "qualifications_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "matched_qualifications": [],
            "missing_qualifications": [],
            "strengths": [],
            "gaps": ["Unable to analyze match - missing job requirements"],
            "recommendations": ["Ensure job has requirements_matrix populated"],
            "transferability_details": [],
            "analyzed_at": datetime.utcnow().isoformat(),
            "matcher_version": "4.0",
            "scoring_method": "v4.0 (fallback)"
        }