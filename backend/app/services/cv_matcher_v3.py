from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import os


class CVMatcherServiceV3:
    """
    AI-First CV-to-Job matching service using Azure OpenAI.
    Version 3.0: Simplified architecture with AI-driven holistic evaluation
    
    Key Changes from v2.x:
    - Single unified AI evaluation (not separate verify + fit calls)
    - AI outputs component scores holistically (not rigid categorization)
    - Minimal preprocessing (2 rules: degree equivalency, domain mismatch)
    - 60% AI weight + 40% safety rails (not 30% AI)
    """

    def __init__(self):
        self.client = None
        print(f"🔧 Initializing CV Matcher Service v3.0")
        print(f"   Endpoint: {settings.AZURE_OPENAI_ENDPOINT or '(not set)'}")
        print(f"   API Key: {'✓ Set' if settings.AZURE_OPENAI_KEY else '✗ Not set'}")
        print(f"   Deployment: {settings.AZURE_OPENAI_DEPLOYMENT or '(not set)'}")

        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
            try:
                self.client = AsyncAzureOpenAI(
                    api_key=settings.AZURE_OPENAI_KEY,
                    api_version="2024-02-15-preview",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
                print(f"✅ CV Matcher v3.0 client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize CV Matcher client: {e}")
        else:
            print(f"⚠️ Azure OpenAI not configured - CV matching unavailable")

    async def analyze_match(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Main entry point for v3.0 matching"""
        
        if not self.client:
            raise Exception("Azure OpenAI not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY.")

        print(f"🎯 [v3.0] Analyzing CV match for job: {job_data.get('title')}")

        requirements_matrix = job_data.get("requirements_matrix")
        
        if not requirements_matrix:
            print("⚠️ No requirements matrix found, using legacy matching...")
            return await self._analyze_match_legacy(cv_data, job_data)

        # Step 1: Minimal preprocessing (2 rules only)
        preprocessing = self._preprocess_minimal(cv_data, requirements_matrix)
        
        # Step 2: Unified AI evaluation
        ai_result = await self._evaluate_match_holistically(cv_data, requirements_matrix, preprocessing)
        
        # Step 3: Apply safety rails
        final_result = self._apply_safety_rails(ai_result, preprocessing, cv_data)
        
        # Step 4: Calculate final score (60% AI + 40% components)
        analysis = self._calculate_final_score(final_result, preprocessing)
        
        # Step 5: Generate recommendations
        analysis["recommendations"] = await self._generate_recommendations(cv_data, ai_result, requirements_matrix)
        
        print(f"✅ [v3.0] Match analysis complete: {analysis['overall_score']}% match")
        
        # Log for review
        self._log_match_analysis(cv_data, job_data, analysis)
        
        return analysis

    def _preprocess_minimal(self, cv_data: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply ONLY critical rules that AI struggles with.
        v3.0: Reduced from 6+ rules to 2 essential rules.
        Returns context for AI, not pre-scored results.
        """
        years_exp = self._get_years_of_experience(cv_data)
        has_cs_degree = self._has_cs_degree(cv_data)
        
        return {
            "years_of_experience": years_exp,
            "degree_equivalent": has_cs_degree or (years_exp >= 5),
            "has_formal_degree": has_cs_degree,
            "domain_analysis": self._analyze_domain_mismatch(cv_data, requirements)
        }
    
    def _analyze_domain_mismatch(self, cv_data: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        Detect if job domain != CV domain (for AI context).
        Returns: {type: "SAME/ADJACENT/ORTHOGONAL", severity: "none/moderate/severe", explanation: str}
        """
        frontend_keywords = ["react", "angular", "vue", "html", "css", "typescript", "javascript"]
        must_haves = requirements.get("must_have", [])
        
        # Count frontend requirements
        frontend_count = sum(
            1 for req in must_haves 
            if any(kw in req.lower() for kw in frontend_keywords)
        )
        is_frontend_job = frontend_count >= 4
        
        # Check if CV has frontend skills
        skills = self._get_listed_skills(cv_data)
        has_frontend = any(
            any(kw in skill.lower() for kw in frontend_keywords)
            for skill in skills
        )
        
        if is_frontend_job and not has_frontend:
            return {
                "type": "ORTHOGONAL",
                "severity": "severe" if frontend_count >= 6 else "moderate",
                "explanation": f"Job requires {frontend_count} frontend skills, CV shows backend/infrastructure focus"
            }
        
        return {
            "type": "SAME",
            "severity": "none",
            "explanation": "Domain alignment acceptable"
        }
    
    def _get_years_of_experience(self, cv_data: Dict[str, Any]) -> float:
        """Calculate total years of professional experience from CV"""
        experience = cv_data.get("experience", [])
        
        if not experience:
            return 0.0
        
        total_years = 0.0
        current_year = datetime.now().year
        
        for exp in experience:
            period = exp.get("period", "")
            try:
                if '–' in period or '-' in period:
                    separator = '–' if '–' in period else '-'
                    parts = period.split(separator)
                    
                    if len(parts) >= 2:
                        start_str = parts[0].strip()
                        end_str = parts[1].strip()
                        
                        # Extract year from start
                        start_year = None
                        for word in start_str.split():
                            if word.isdigit() and len(word) == 4:
                                start_year = int(word)
                                break
                        
                        # Extract year from end
                        end_year = current_year if 'present' in end_str.lower() or 'current' in end_str.lower() else None
                        if not end_year:
                            for word in end_str.split():
                                if word.isdigit() and len(word) == 4:
                                    end_year = int(word)
                                    break
                        
                        if start_year and end_year:
                            years = max(0, end_year - start_year)
                            total_years += years
            except:
                continue
        
        return total_years
    
    def _has_cs_degree(self, cv_data: Dict[str, Any]) -> bool:
        """Check if candidate has CS-related degree"""
        education = cv_data.get("education", [])
        
        cs_keywords = [
            "computer science", "software engineering", "computer engineering",
            "information system", "cyber", "software and information",
            " cs ", " cs,", "computer sci", "information tech"
        ]
        
        degree_keywords = ["b.sc", "bachelor", "b.s.", "bsc", "ba ", "b.a.", "b.tech"]
        
        for edu in education:
            degree_lower = edu.get("degree", "").lower()
            field_lower = edu.get("field", "").lower()
            institution_lower = edu.get("institution", "").lower()
            
            has_degree = any(kw in degree_lower for kw in degree_keywords)
            is_cs_field = any(kw in field_lower for kw in cs_keywords)
            is_tech_uni = any(name in institution_lower for name in [
                "institute of technology", "engineering", "polytechnic", "computer"
            ])
            
            if has_degree and (is_cs_field or is_tech_uni):
                return True
        
        return False
    
    def _get_listed_skills(self, cv_data: Dict[str, Any]) -> List[str]:
        """Extract all skills mentioned in CV"""
        skills = []
        skills_section = cv_data.get("skills", {})
        
        if isinstance(skills_section, dict):
            for category, items in skills_section.items():
                if isinstance(items, list):
                    skills.extend(items)
        elif isinstance(skills_section, list):
            skills = skills_section
        
        return [s.lower() for s in skills if isinstance(s, str)]

    async def _evaluate_match_holistically(
        self,
        cv_data: Dict[str, Any],
        requirements: Dict[str, Any],
        preprocessing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Single comprehensive AI evaluation replacing separate verify + fit calls.
        v3.0: AI outputs all scores and reasoning in one pass.
        """
        
        cv_text = self._format_cv_for_prompt(cv_data)
        must_haves = requirements.get("must_have", [])
        nice_to_haves = requirements.get("nice_to_have", [])
        
        prompt = f"""
You are an expert technical recruiter evaluating candidate fit for a role.

CANDIDATE CV:
{cv_text}

JOB REQUIREMENTS:
MUST-HAVE:
{json.dumps(must_haves, indent=2)}

NICE-TO-HAVE:
{json.dumps(nice_to_haves, indent=2)}

CONTEXT (from preprocessing):
- Years of Experience: {preprocessing['years_of_experience']} years
- Formal CS Degree: {preprocessing['has_formal_degree']}
- Degree Requirement Met: {preprocessing['degree_equivalent']} {'(via formal degree)' if preprocessing['has_formal_degree'] else f"(via {preprocessing['years_of_experience']}+ years experience)"}
- Domain Analysis: {preprocessing['domain_analysis']['explanation']}

YOUR TASK:
Provide a comprehensive evaluation considering TRANSFERABILITY and EXPERIENCE, not just exact tech matches.

CRITICAL EVALUATION RULES:

1. EXPERIENCE IS THE PRIMARY SIGNAL
   - 10+ years software engineering = STRONG foundation, even if domain differs
   - Senior engineers learn new frameworks in 3-6 months (React, TypeScript, etc.)
   - Domain expertise (cybersecurity, backend, distributed systems) demonstrates problem-solving ability
   
2. TRANSFERABILITY SCORING
   - **SAME domain** (backend→backend, frontend→frontend): Missing specific tech = minor gap
   - **ADJACENT domain** (backend→DevOps, security→backend): Transferable, moderate ramp-up
   - **ORTHOGONAL domain** (backend→frontend, data→security): Significant ramp-up, cap at 60%
   
3. COMPONENT SCORING GUIDELINES (0-100 each):

   **Skills Score** - Technical capabilities
   - Exact match (React + has React): 90-100%
   - Transferable (Python expert, React required): 40-60% (learnable)
   - Adjacent tech (Angular + need React): 60-80%
   - Senior engineer, wrong domain: 30-45% (strong foundation, new domain)
   - Junior, wrong domain: 10-25%
   
   **Experience Score** - Years and quality
   - 10+ years relevant domain: 90-100%
   - 10+ years adjacent domain: 70-85%
   - 10+ years orthogonal domain: 60-75%
   - 5-10 years relevant: 70-85%
   - 1-5 years relevant: 50-70%
   - <1 year or student: 20-40%
   
   **Qualifications Score** - Education and credentials
   - B.Sc/B.A/B.Tech in CS/Engineering: 100%
   - 5+ years experience (no formal degree): 100% (meets "OR equivalent experience" clause)
   - Technical bootcamp + some experience: 70-85%
   - Self-taught + projects: 50-70%

4. EVIDENCE REQUIREMENTS & DEGREE FORMATTING
   - Cite SPECIFIC CV content: "Led ITDR team at Microsoft (2021-2025)"
   - Don't claim missing evidence when it's in CV
   - When citing degree requirement satisfaction:
     * If formal degree: "Has Bachelor's degree in Computer Science"
     * If experience only: "Meets degree requirement via 10+ years of professional experience"
     * NEVER say "Degree Equivalent: True" - be explicit about HOW requirement is met

5. OVERALL SCORE CALCULATION
   - For SAME domain: Can reach 85-100% if most requirements met
   - For ADJACENT domain: Cap at 75-85% even if senior
   - For ORTHOGONAL domain: Cap at 50-65% even with 10+ years
   - Missing critical frameworks in ORTHOGONAL domain: 35-55% range

REQUIREMENT VERIFICATION:
For each requirement, determine:
- **MET**: Explicit evidence in CV (quote it)
- **PARTIALLY_MET**: Related experience or transferable skill
- **NOT_MET**: No evidence or transferability

OUTPUT FORMAT (valid JSON only):
{{
  "requirement_evaluations": [
    {{
      "requirement": "1+ years React.js",
      "status": "NOT_MET",
      "evidence": "CV shows Python, C#, Rust but no frontend frameworks. However, 10+ years engineering provides strong foundation to learn React in 3-6 months.",
      "transferability_note": "Learnable framework for senior engineer"
    }}
  ],
  "component_scores": {{
    "skills_score": 35,
    "experience_score": 85,
    "qualifications_score": 100
  }},
  "overall_score": 52,
  "reasoning": "10+ years senior software engineering at Microsoft with large-scale production systems (10M users). Backend/cybersecurity focus is orthogonal to frontend requirements, limiting immediate fit. However, strong technical fundamentals and proven ability to deliver complex systems. React, TypeScript, HTML/CSS are learnable frameworks within 3-6 months for a senior engineer.",
  "domain_fit": "ORTHOGONAL",
  "transferability_assessment": "High potential to succeed after 3-6 month ramp-up period",
  "strengths": [
    "Meets degree requirement via 10+ years of professional software engineering experience",
    "10+ years in software engineering with focus on backend and cybersecurity",
    "Scaled ITDR solution to protect over 10 million users globally at Microsoft",
    "Experience with Azure Cloud Services"
  ]
}}

IMPORTANT: Be realistic but fair. A senior engineer with 10 years should NOT score 0% on skills just because they lack one specific framework.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low for consistency, not 0 to allow reasoning
                max_tokens=2500
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result[7:-3]
            elif result.startswith("```"):
                result = result[3:-3]
            
            ai_result = json.loads(result)
            print(f"🤖 AI Evaluation: overall={ai_result['overall_score']}%, skills={ai_result['component_scores']['skills_score']}%, exp={ai_result['component_scores']['experience_score']}%")
            print(f"   Domain: {ai_result.get('domain_fit', 'N/A')}, Reasoning: {ai_result['reasoning'][:100]}...")
            
            return ai_result
            
        except Exception as e:
            print(f"❌ AI evaluation failed: {e}")
            return self._generate_fallback_scores(cv_data, requirements, preprocessing)

    def _apply_safety_rails(
        self,
        ai_result: Dict[str, Any],
        preprocessing: Dict[str, Any],
        cv_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply bounds to prevent unrealistic scores.
        Goal: Catch AI mistakes, not override good reasoning.
        """
        overall = ai_result["overall_score"]
        scores = ai_result["component_scores"]
        domain = preprocessing["domain_analysis"]
        years_exp = preprocessing["years_of_experience"]
        
        # Safety Rail 1: Severe domain mismatch cap
        if domain["severity"] == "severe":
            if overall > 55:
                print(f"⚠️ Applied severe domain mismatch cap: overall {overall}% → 55%")
                overall = 55
            if scores["skills_score"] > 40:
                print(f"⚠️ Applied severe domain mismatch cap: skills {scores['skills_score']}% → 40%")
                scores["skills_score"] = 40
        
        elif domain["severity"] == "moderate":
            if overall > 70:
                print(f"⚠️ Applied moderate domain mismatch cap: overall {overall}% → 70%")
                overall = 70
            if scores["skills_score"] > 60:
                print(f"⚠️ Applied moderate domain mismatch cap: skills {scores['skills_score']}% → 60%")
                scores["skills_score"] = 60
        
        # Safety Rail 2: Experience score floor
        if years_exp >= 10:
            min_exp_score = 75
        elif years_exp >= 5:
            min_exp_score = 60
        else:
            min_exp_score = 0
        
        if scores["experience_score"] < min_exp_score:
            print(f"⚠️ Boosting experience score: {scores['experience_score']}% → {min_exp_score}%")
            scores["experience_score"] = min_exp_score
        
        # Safety Rail 3: Qualification score for 10+ years
        if years_exp >= 10 and scores["qualifications_score"] < 90:
            print(f"⚠️ Boosting qualifications: {scores['qualifications_score']}% → 90% (10+ years)")
            scores["qualifications_score"] = 90
        
        return {
            **ai_result,
            "overall_score": overall,
            "component_scores": scores
        }

    def _calculate_final_score(
        self,
        ai_result: Dict[str, Any],
        preprocessing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine AI holistic assessment with component average.
        v3.0: 60% AI holistic + 40% component average
        """
        ai_overall = ai_result["overall_score"]
        component_scores = ai_result["component_scores"]
        
        # Component average
        component_avg = sum(component_scores.values()) / len(component_scores)
        
        # Weighted combination: AI gets more weight (60% vs 40%)
        final_score = (ai_overall * 0.6) + (component_avg * 0.4)
        
        # Generate lists for frontend
        requirement_evals = ai_result.get("requirement_evaluations", [])
        matched_skills = [r["requirement"] for r in requirement_evals if r["status"] == "MET"]
        missing_skills = [r["requirement"] for r in requirement_evals if r["status"] == "NOT_MET"]
        gaps = [r["requirement"] for r in requirement_evals if r["status"] == "NOT_MET"]
        strengths = [r["evidence"] for r in requirement_evals if r["status"] == "MET"][:5]
        
        return {
            "overall_score": int(final_score),
            "ai_holistic_score": int(ai_overall),
            "component_average": int(component_avg),
            "skills_score": int(component_scores["skills_score"]),
            "experience_score": int(component_scores["experience_score"]),
            "qualifications_score": int(component_scores["qualifications_score"]),
            
            "domain_fit": ai_result.get("domain_fit", "UNKNOWN"),
            "transferability_assessment": ai_result.get("transferability_assessment", ""),
            "reasoning": ai_result.get("reasoning", ""),
            
            "strengths": strengths,
            "gaps": gaps,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_qualifications": [],
            "missing_qualifications": [],
            
            "scoring_method": "v3.0 (60% AI holistic + 40% components)",
            "domain_mismatch": preprocessing["domain_analysis"]["severity"] != "none",
            "domain_mismatch_severity": preprocessing["domain_analysis"]["severity"],
            "domain_explanation": preprocessing["domain_analysis"]["explanation"]
        }

    async def _generate_recommendations(
        self,
        cv_data: Dict[str, Any],
        ai_result: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for CV improvement"""
        
        requirement_evals = ai_result.get("requirement_evaluations", [])
        missing = [r for r in requirement_evals if r["status"] == "NOT_MET"][:5]
        partial = [r for r in requirement_evals if r["status"] == "PARTIALLY_MET"][:3]
        
        if not missing and not partial:
            return ["Your CV is well-matched to this role! Focus on tailoring your summary and highlighting relevant achievements."]
        
        cv_summary = self._format_cv_for_prompt(cv_data)
        
        gaps_text = "GAPS TO ADDRESS:\n"
        for r in missing:
            gaps_text += f"- {r['requirement']} ({r.get('transferability_note', 'Required')})\n"
        
        if partial:
            gaps_text += "\nPARTIALLY MET (strengthen these):\n"
            for r in partial:
                gaps_text += f"- {r['requirement']}\n"
        
        prompt = f"""
You are a CV consultant helping improve a candidate's CV.

CANDIDATE CV:
{cv_summary}

{gaps_text}

Provide ONLY 3-4 HIGH-IMPACT, ACTIONABLE recommendations. Quality over quantity.

CRITICAL RULES:
1. Group similar gaps together - ONE recommendation for all related missing skills
2. Focus on HIGHEST IMPACT changes that will improve the match score most
3. Be concise - one sentence per recommendation
4. Prioritize: Skills gaps first, then Experience reframing, then new sections

GOOD EXAMPLE (concise and high-impact):
1. "Add frontend technologies (React, TypeScript, HTML/CSS) to Skills as 'Currently Learning' or in a separate 'Technical Interests' section"
2. "Highlight transferable experience: rephrase backend work to emphasize problem-solving and system design skills applicable to any tech stack"
3. "Create a Projects section with any side projects demonstrating full-stack or frontend work"

BAD EXAMPLE (too detailed and repetitive):
1. "Add React.js to skills"
2. "Add TypeScript to skills"
3. "Rephrase first bullet in Microsoft section"
4. "Rephrase second bullet in Microsoft section"
5. "Update summary line 1"
6. "Update summary line 2"
7. "Add certifications section"

Return ONLY a JSON array:
["recommendation 1", "recommendation 2", ...]
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a CV consultant. Return only valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result[7:-3]
            elif result.startswith("```"):
                result = result[3:-3]
            
            recommendations = json.loads(result)
            return recommendations if isinstance(recommendations, list) else []
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return [f"Address missing requirement: {r['requirement']}" for r in missing[:5]]

    def _generate_fallback_scores(
        self,
        cv_data: Dict[str, Any],
        requirements: Dict[str, Any],
        preprocessing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback scoring if AI fails"""
        years_exp = preprocessing["years_of_experience"]
        
        # Simple heuristics
        experience_score = min(years_exp * 8, 85)
        qualifications_score = 100 if preprocessing["degree_equivalent"] else 60
        skills_score = 50  # Neutral default
        
        if preprocessing["domain_analysis"]["severity"] == "severe":
            skills_score = 25
        
        overall = (skills_score + experience_score + qualifications_score) / 3
        
        return {
            "requirement_evaluations": [],
            "component_scores": {
                "skills_score": skills_score,
                "experience_score": experience_score,
                "qualifications_score": qualifications_score
            },
            "overall_score": int(overall),
            "reasoning": "Fallback scoring used due to AI error",
            "domain_fit": "UNKNOWN",
            "transferability_assessment": "Unable to assess"
        }

    def _format_cv_for_prompt(self, cv_data: Dict[str, Any]) -> str:
        """Helper to format CV data into readable string for LLM"""
        text = f"Summary: {cv_data.get('summary', '')}\n\n"
        
        text += "Skills:\n"
        skills = cv_data.get('skills', {})
        if isinstance(skills, dict):
            for cat, items in skills.items():
                text += f"{cat}: {', '.join(items)}\n"
        elif isinstance(skills, list):
            text += f"{', '.join(skills)}\n"
            
        text += "\nExperience:\n"
        for exp in cv_data.get('experience', []):
            text += f"- {exp.get('title')} at {exp.get('company')} ({exp.get('period')})\n"
            desc = exp.get('description', [])
            if isinstance(desc, list):
                for item in desc:
                    text += f"  * {item}\n"
            else:
                text += f"  * {desc}\n"
        
        text += "\nEducation:\n"
        for edu in cv_data.get('education', []):
            text += f"- {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')} ({edu.get('year', '')})\n"
                
        return text

    async def _analyze_match_legacy(self, cv_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy matching for jobs without structured requirements"""
        print("⚠️ Using legacy matching (no requirements matrix)")
        
        # Simple fallback
        return {
            "overall_score": 50,
            "skills_score": 50,
            "experience_score": 50,
            "qualifications_score": 50,
            "strengths": ["Legacy matching used"],
            "gaps": ["Requires structured job requirements"],
            "recommendations": ["Add structured requirements to job posting"],
            "matched_skills": [],
            "missing_skills": [],
            "matched_qualifications": [],
            "missing_qualifications": []
        }

    def _log_match_analysis(self, cv_data: Dict[str, Any], job_data: Dict[str, Any], analysis: Dict[str, Any]):
        """Log match analysis for review"""
        try:
            log_dir = Path("logs/match_analysis_v3")
            log_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = log_dir / f"{date_str}.jsonl"
            timestamp = datetime.utcnow().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "cv_id": cv_data.get("id", "unknown"),
                "job_id": job_data.get("id", "unknown"),
                "match_result": analysis,
                "version": "3.0"
            }
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Failed to log analysis: {e}")


# Singleton instance
cv_matcher_service_v3 = CVMatcherServiceV3()