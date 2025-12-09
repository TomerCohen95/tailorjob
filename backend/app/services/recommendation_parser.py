"""
Recommendation Parser Service

Converts text-based recommendations from cv_matcher_v5 into structured,
actionable suggestions for the interactive CV tailoring UI.
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum


class ActionType(str, Enum):
    """Types of actions that can be suggested"""
    ADD_METRIC = "add_metric"
    HIGHLIGHT_SKILL = "highlight_skill"
    ENHANCE_EXPERIENCE = "enhance_experience"
    ADD_TO_SUMMARY = "add_to_summary"
    EMPHASIZE_ACHIEVEMENT = "emphasize_achievement"
    EXPAND_DESCRIPTION = "expand_description"


class ImpactLevel(str, Enum):
    """Impact level of a suggestion"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionableSuggestion:
    """Structured representation of a single actionable suggestion"""
    
    def __init__(
        self,
        id: str,
        type: ActionType,
        section: str,
        suggestion: str,
        reasoning: str,
        impact: ImpactLevel,
        original_text: str,
        target: Optional[str] = None,
        examples: Optional[List[str]] = None
    ):
        self.id = id
        self.type = type
        self.section = section
        self.suggestion = suggestion
        self.reasoning = reasoning
        self.impact = impact
        self.original_text = original_text
        self.target = target
        self.examples = examples or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "type": self.type.value,
            "section": self.section,
            "suggestion": self.suggestion,
            "reasoning": self.reasoning,
            "impact": self.impact.value,
            "original_text": self.original_text,
            "target": self.target,
            "examples": self.examples
        }


class RecommendationParser:
    """
    Parses text recommendations from cv_matcher into structured actions.
    
    Detects patterns like:
    - "Add team size metrics to your..."
    - "Highlight Python projects in..."
    - "Add quantifiable impact to..."
    - "Emphasize [skill] as it relates to..."
    """
    
    # Patterns for different action types
    PATTERNS = {
        ActionType.ADD_METRIC: [
            r"add.*metric",
            r"quantif(?:y|iable)",
            r"add.*team size",
            r"add.*scale",
            r"add.*numbers",
        ],
        ActionType.HIGHLIGHT_SKILL: [
            r"highlight.*(?:skill|technology|experience)",
            r"emphasize.*(?:skill|technology)",
        ],
        ActionType.ENHANCE_EXPERIENCE: [
            r"expand.*experience",
            r"enhance.*(?:description|role)",
            r"add.*detail.*to",
        ],
        ActionType.ADD_TO_SUMMARY: [
            r"add.*(?:to|in).*summary",
            r"highlight.*prominently",
            r"emphasize.*in.*summary",
        ],
        ActionType.EMPHASIZE_ACHIEVEMENT: [
            r"emphasize.*achievement",
            r"highlight.*accomplishment",
        ],
        ActionType.EXPAND_DESCRIPTION: [
            r"expand.*(?:brief|mention)",
            r"add.*specific.*(?:technologies|projects)",
        ],
    }
    
    def __init__(self):
        # Compile regex patterns
        self.compiled_patterns = {
            action_type: [re.compile(pattern, re.IGNORECASE) 
                         for pattern in patterns]
            for action_type, patterns in self.PATTERNS.items()
        }
    
    def parse_recommendations(
        self,
        match_analysis: Dict[str, Any],
        cv_data: Optional[Dict[str, Any]] = None
    ) -> List[ActionableSuggestion]:
        """
        Parse text recommendations into structured actions.
        
        Args:
            match_analysis: Output from cv_matcher_v5 containing recommendations
            cv_data: Optional CV data for context
            
        Returns:
            List of actionable suggestions
        """
        # Recommendations can be at top level or inside 'analysis' object
        recommendations = match_analysis.get("recommendations", [])
        if not recommendations and "analysis" in match_analysis:
            recommendations = match_analysis["analysis"].get("recommendations", [])
        
        if not recommendations:
            return []
        
        suggestions = []
        for idx, rec_text in enumerate(recommendations):
            suggestion = self._parse_single_recommendation(
                rec_text, 
                idx, 
                cv_data
            )
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _parse_single_recommendation(
        self,
        text: str,
        index: int,
        cv_data: Optional[Dict[str, Any]]
    ) -> Optional[ActionableSuggestion]:
        """Parse a single recommendation text into structured action"""
        
        # Detect action type
        action_type = self._detect_action_type(text)
        if not action_type:
            # Default to enhance_experience if can't classify
            action_type = ActionType.ENHANCE_EXPERIENCE
        
        # Extract components
        section = self._extract_section(text)
        target = self._extract_target(text)
        examples = self._extract_examples(text)
        reasoning = self._extract_reasoning(text)
        impact = self._determine_impact(text, action_type)
        
        # Clean up the suggestion text (remove reasoning/examples)
        suggestion = self._clean_suggestion_text(text)
        
        return ActionableSuggestion(
            id=f"action_{index + 1}",
            type=action_type,
            section=section,
            suggestion=suggestion,
            reasoning=reasoning,
            impact=impact,
            original_text=text,
            target=target,
            examples=examples
        )
    
    def _detect_action_type(self, text: str) -> Optional[ActionType]:
        """Detect the type of action from recommendation text"""
        text_lower = text.lower()
        
        # Check each pattern
        for action_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return action_type
        
        return None
    
    def _extract_section(self, text: str) -> str:
        """Extract which CV section the recommendation applies to"""
        text_lower = text.lower()
        
        if "summary" in text_lower:
            return "summary"
        elif "experience" in text_lower or "role" in text_lower:
            return "experience"
        elif "skill" in text_lower:
            return "skills"
        elif "education" in text_lower:
            return "education"
        elif "project" in text_lower:
            return "projects"
        else:
            return "experience"  # Default
    
    def _extract_target(self, text: str) -> Optional[str]:
        """Extract the specific target (e.g., role name, skill name)"""
        # Look for quoted text or text after "to your"
        
        # Pattern: "to your [TARGET]"
        match = re.search(r'to your ([^(,\-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern: quoted text
        match = re.search(r'["\']([^"\']+)["\']', text)
        if match:
            return match.group(1).strip()
        
        # Pattern: after "in" or "for"
        match = re.search(r'(?:in|for) ([A-Z][a-zA-Z\s]+)', text)
        if match:
            target = match.group(1).strip()
            # Stop at common words
            for stop_word in ['if', 'to', 'as', 'with', '-']:
                if stop_word in target:
                    target = target.split(stop_word)[0].strip()
            return target
        
        return None
    
    def _extract_examples(self, text: str) -> List[str]:
        """Extract example text from parentheses or 'e.g.' sections"""
        examples = []
        
        # Pattern: (e.g., "example")
        matches = re.findall(r'\(e\.g\.,?\s*["\']?([^)"\']+)["\']?\)', text)
        examples.extend(matches)
        
        # Pattern: text in parentheses with quotes
        matches = re.findall(r'\(["\']([^"\']+)["\']\)', text)
        examples.extend(matches)
        
        return [ex.strip() for ex in examples if ex.strip()]
    
    def _extract_reasoning(self, text: str) -> str:
        """Extract the reasoning/why from the recommendation"""
        # Look for patterns like "to strengthen", "which", "as it"
        
        # Pattern: "to [REASON]"
        match = re.search(r'to (strengthen|demonstrate|improve|show|highlight) ([^.]+)', text, re.IGNORECASE)
        if match:
            return f"To {match.group(1)} {match.group(2)}".strip()
        
        # Pattern: "- [REASON]"
        match = re.search(r'\s*-\s*(.+)$', text)
        if match:
            return match.group(1).strip()
        
        # Pattern: "job requires/mentions [REASON]"
        match = re.search(r'job (?:requires|mentions|needs) ([^.]+)', text, re.IGNORECASE)
        if match:
            return f"Job requires {match.group(1)}".strip()
        
        return "Improves match with job requirements"
    
    def _clean_suggestion_text(self, text: str) -> str:
        """Clean up suggestion text by removing examples and reasoning"""
        # Remove parenthetical examples
        clean = re.sub(r'\s*\([^)]*\)', '', text)
        
        # Remove " - reasoning" suffix
        clean = re.sub(r'\s*-\s*[^.]+$', '', clean)
        
        # Remove "to strengthen..." suffix
        clean = re.sub(r'\s+to (?:strengthen|demonstrate|improve|show).*$', '', clean, flags=re.IGNORECASE)
        
        return clean.strip()
    
    def _determine_impact(self, text: str, action_type: ActionType) -> ImpactLevel:
        """Determine impact level based on text and action type"""
        text_lower = text.lower()
        
        # High impact keywords
        high_keywords = ["required", "must", "critical", "essential", "key"]
        if any(keyword in text_lower for keyword in high_keywords):
            return ImpactLevel.HIGH
        
        # Metrics and quantifiable improvements are usually high impact
        if action_type == ActionType.ADD_METRIC:
            return ImpactLevel.HIGH
        
        # Highlighting required skills is high impact
        if "job requires" in text_lower and action_type == ActionType.HIGHLIGHT_SKILL:
            return ImpactLevel.HIGH
        
        # Summary additions are medium-high impact
        if action_type == ActionType.ADD_TO_SUMMARY:
            return ImpactLevel.MEDIUM
        
        return ImpactLevel.MEDIUM


# Singleton instance
_parser_instance = None

def get_parser() -> RecommendationParser:
    """Get singleton parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = RecommendationParser()
    return _parser_instance