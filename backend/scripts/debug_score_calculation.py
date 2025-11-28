#!/usr/bin/env python3
"""Debug score calculation for the Microsoft job"""

# From check_job_requirements.py output:
must_haves = [
    "6+ years computer security industry experience",      # MET (experience)
    "3+ years experience researching threat protection",   # MET (experience)
    "Code fluency in C, Python or Rust",                   # MET (skill)
    "Knowledge of MITRE ATT&CK",                           # NOT MET (skill)
    "BSc or M.Sc. in Computer Science"                     # MET (qualification)
]

nice_to_haves = [
    "Hands-on knowledge of AI/LLM fundamentals",           # NOT MET
    "Familiarity with OAuth and identity protocols",       # NOT MET
    "Industry recognized author of security research",     # NOT MET
    "Experience leading a project from start to finish",   # MET
    "Familiarity with cloud environments"                  # NOT MET
]

# Calculate must-have score
must_have_met = 4  # All except MITRE
must_have_not_met = 1  # MITRE
must_have_total = 5

must_have_score = (must_have_met * 1.0) / must_have_total * 100
print(f"Must-have score: {must_have_met}/{must_have_total} = {must_have_score}%")

# Calculate nice-to-have score
nice_met = 1  # Leading project
nice_not_met = 4
nice_total = 5

nice_score = (nice_met * 1.0) / nice_total * 100
print(f"Nice-to-have score: {nice_met}/{nice_total} = {nice_score}%")

# Overall score OLD (70% must-have, 30% nice-to-have)
old_overall_score = (must_have_score * 0.7) + (nice_score * 0.3)
print(f"\n--- OLD Scoring (v2.4) ---")
print(f"Overall score: ({must_have_score} * 0.7) + ({nice_score} * 0.3) = {old_overall_score}%")

# Overall score NEW (85% must-have, 15% nice-to-have)
new_overall_score = (must_have_score * 0.85) + (nice_score * 0.15)
print(f"\n--- NEW Scoring (v2.5) ---")
print(f"Overall score: ({must_have_score} * 0.85) + ({nice_score} * 0.15) = {new_overall_score}%")
print(f"Improvement: +{new_overall_score - old_overall_score}%")

# Category scores (for display)
print("\n--- Category Scores (Display Only) ---")

# Skills: C/Python/Rust (MET), MITRE (NOT MET)
skills_met = 1
skills_total = 2
skills_score = (skills_met / skills_total) * 100
print(f"Skills: {skills_met}/{skills_total} = {skills_score}%")

# Experience: 6+ years (MET), 3+ years (MET)
exp_met = 2
exp_total = 2
exp_score = (exp_met / exp_total) * 100
print(f"Experience: {exp_met}/{exp_total} = {exp_score}%")

# Qualifications: BSc/MSc (MET)
qual_met = 1
qual_total = 1
qual_score = (qual_met / qual_total) * 100
print(f"Qualifications: {qual_met}/{qual_total} = {qual_score}%")

print(f"\n✅ NEW Expected overall: {new_overall_score}%")
print(f"✅ Expected skills: {skills_score}%")
print(f"✅ Expected experience: {exp_score}%")
print(f"✅ Expected qualifications: {qual_score}%")