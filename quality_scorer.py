"""
Quality Scoring Module for Legal-Mind-AI
Implements comprehensive quality assessment for legal analysis responses
"""

import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QualityMetrics:
    """Quality metrics for legal analysis responses"""
    completeness_score: float
    accuracy_indicators: float
    relevance_score: float
    structure_score: float
    citation_score: float
    overall_score: float
    suggestions: List[str]
    confidence_level: str

class LegalResponseQualityScorer:
    """
    Comprehensive quality scoring system for legal analysis responses
    """
    
    def __init__(self):
        self.legal_keywords = [
            'statute', 'regulation', 'case law', 'precedent', 'jurisdiction',
            'compliance', 'liability', 'contract', 'tort', 'constitutional',
            'amendment', 'court', 'ruling', 'decision', 'opinion'
        ]
        
        self.structure_indicators = [
            'analysis', 'conclusion', 'recommendation', 'summary',
            'findings', 'assessment', 'evaluation', 'implications'
        ]
        
        self.citation_patterns = [
            r'\d+\s+U\.S\.',  # US Reports
            r'\d+\s+S\.Ct\.',  # Supreme Court Reporter
            r'\d+\s+F\.\d+d',  # Federal Reporter
            r'\d+\s+F\.Supp',  # Federal Supplement
            r'§\s*\d+',       # Section references
            r'USC\s+§\s*\d+',  # US Code
            r'CFR\s+§\s*\d+',  # Code of Federal Regulations
        ]
    
    def analyze_response_quality(self, 
                                response: str, 
                                user_query: str,
                                agent_type: str = "unknown") -> QualityMetrics:
        """
        Comprehensive quality analysis of legal response
        
        Args:
            response: The agent's response text
            user_query: Original user query
            agent_type: Type of agent (policy_analyst, compliance_expert, etc.)
            
        Returns:
            QualityMetrics object with detailed scoring
        """
        
        # Calculate individual metrics
        completeness = self._assess_completeness(response, user_query)
        accuracy = self._assess_accuracy_indicators(response)
        relevance = self._assess_relevance(response, user_query)
        structure = self._assess_structure_quality(response)
        citations = self._assess_citations(response)
        
        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(
            completeness, accuracy, relevance, structure, citations
        )
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            completeness, accuracy, relevance, structure, citations, response
        )
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(overall_score)
        
        return QualityMetrics(
            completeness_score=completeness,
            accuracy_indicators=accuracy,
            relevance_score=relevance,
            structure_score=structure,
            citation_score=citations,
            overall_score=overall_score,
            suggestions=suggestions,
            confidence_level=confidence_level
        )
    
    def _assess_completeness(self, response: str, query: str) -> float:
        """Assess how completely the response addresses the query"""
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Extract key concepts from query
        query_words = set(re.findall(r'\b\w{4,}\b', query_lower))
        response_words = set(re.findall(r'\b\w{4,}\b', response_lower))
        
        # Calculate concept coverage
        if not query_words:
            return 0.5  # Neutral score if no key concepts
        
        coverage_ratio = len(query_words.intersection(response_words)) / len(query_words)
        
        # Bonus for comprehensive structure
        structure_bonus = 0.0
        if any(indicator in response_lower for indicator in ['analysis', 'conclusion', 'recommendation']):
            structure_bonus = 0.1
        
        # Length consideration (too short or too long can indicate issues)
        length_score = min(1.0, len(response) / 500)  # Optimal around 500+ chars
        if len(response) > 3000:  # Penalty for excessive length
            length_score *= 0.9
        
        return min(1.0, coverage_ratio + structure_bonus + (length_score * 0.2))
    
    def _assess_accuracy_indicators(self, response: str) -> float:
        """Assess indicators of accuracy and legal sophistication"""
        response_lower = response.lower()
        
        # Legal terminology usage
        legal_term_count = sum(1 for term in self.legal_keywords if term in response_lower)
        legal_sophistication = min(1.0, legal_term_count / 10)  # Max score at 10+ legal terms
        
        # Hedge language (indicates appropriate legal caution)
        hedge_patterns = [
            'may', 'could', 'might', 'potentially', 'likely', 'typically',
            'generally', 'usually', 'subject to', 'depending on'
        ]
        hedge_count = sum(1 for pattern in hedge_patterns if pattern in response_lower)
        caution_score = min(1.0, hedge_count / 5)  # Appropriate caution
        
        # Avoid definitive statements without qualification
        definitive_patterns = ['definitely', 'certainly', 'always', 'never', 'guaranteed']
        definitive_count = sum(1 for pattern in definitive_patterns if pattern in response_lower)
        certainty_penalty = max(0.0, 1.0 - (definitive_count * 0.2))  # Penalty for overconfidence
        
        return (legal_sophistication + caution_score + certainty_penalty) / 3
    
    def _assess_relevance(self, response: str, query: str) -> float:
        """Assess relevance of response to the specific query"""
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Direct query addressing
        query_keywords = re.findall(r'\b\w{3,}\b', query_lower)
        relevance_matches = sum(1 for keyword in query_keywords if keyword in response_lower)
        
        if not query_keywords:
            return 0.5
        
        direct_relevance = min(1.0, relevance_matches / len(query_keywords))
        
        # Context appropriateness (legal domain)
        legal_context_score = 1.0 if any(term in response_lower for term in self.legal_keywords) else 0.3
        
        return (direct_relevance + legal_context_score) / 2
    
    def _assess_structure_quality(self, response: str) -> float:
        """Assess the structural quality and organization of the response"""
        
        # Check for clear sections/organization
        section_indicators = [
            r'\d+\.', r'[a-z]\)', r'•', r'-', r'\*',  # Bullet points, numbers
            r'analysis:', r'conclusion:', r'recommendation:', r'summary:'  # Headers
        ]
        
        structure_elements = sum(1 for pattern in section_indicators 
                               if re.search(pattern, response.lower()))
        organization_score = min(1.0, structure_elements / 5)
        
        # Paragraph structure (not too long, not too short)
        paragraphs = response.split('\n\n')
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        if 20 <= avg_paragraph_length <= 100:
            paragraph_score = 1.0
        elif 10 <= avg_paragraph_length <= 150:
            paragraph_score = 0.8
        else:
            paragraph_score = 0.5
        
        # Logical flow indicators
        transition_words = ['however', 'therefore', 'furthermore', 'additionally', 'consequently', 'moreover']
        transition_count = sum(1 for word in transition_words if word in response.lower())
        flow_score = min(1.0, transition_count / 3)
        
        return (organization_score + paragraph_score + flow_score) / 3
    
    def _assess_citations(self, response: str) -> float:
        """Assess the presence and quality of legal citations"""
        
        citation_matches = []
        for pattern in self.citation_patterns:
            citation_matches.extend(re.findall(pattern, response))
        
        # Base score from citation presence
        if len(citation_matches) >= 3:
            citation_score = 1.0
        elif len(citation_matches) >= 1:
            citation_score = 0.7
        else:
            citation_score = 0.0
        
        # Bonus for specific legal references
        specific_references = [
            'v.', 'et al.', 'supra', 'infra', 'id.', 'ibid',
            'see also', 'cf.', 'but see'
        ]
        
        reference_bonus = sum(0.1 for ref in specific_references if ref in response.lower())
        
        return min(1.0, citation_score + reference_bonus)
    
    def _calculate_overall_score(self, completeness: float, accuracy: float, 
                               relevance: float, structure: float, citations: float) -> float:
        """Calculate weighted overall quality score"""
        
        # Weights for different aspects
        weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'relevance': 0.25,
            'structure': 0.15,
            'citations': 0.05
        }
        
        overall = (
            completeness * weights['completeness'] +
            accuracy * weights['accuracy'] +
            relevance * weights['relevance'] +
            structure * weights['structure'] +
            citations * weights['citations']
        )
        
        # Convert to 1-10 scale
        return round(overall * 10, 1)
    
    def _generate_suggestions(self, completeness: float, accuracy: float,
                            relevance: float, structure: float, citations: float,
                            response: str) -> List[str]:
        """Generate specific improvement suggestions"""
        
        suggestions = []
        
        if completeness < 0.7:
            suggestions.append("Consider addressing more aspects of the original query")
        
        if accuracy < 0.7:
            suggestions.append("Include more legal terminology and appropriate hedge language")
        
        if relevance < 0.7:
            suggestions.append("Ensure response directly addresses the specific legal question asked")
        
        if structure < 0.7:
            suggestions.append("Improve organization with clear sections and logical flow")
        
        if citations < 0.3:
            suggestions.append("Add specific legal citations and references to support analysis")
        
        if len(response) < 200:
            suggestions.append("Provide more detailed analysis and explanation")
        elif len(response) > 3000:
            suggestions.append("Consider condensing to focus on key points")
        
        return suggestions if suggestions else ["Analysis meets quality standards"]
    
    def _determine_confidence_level(self, overall_score: float) -> str:
        """Determine confidence level based on overall score"""
        if overall_score >= 9.0:
            return "Excellent"
        elif overall_score >= 8.0:
            return "High"
        elif overall_score >= 7.0:
            return "Good"
        elif overall_score >= 6.0:
            return "Moderate"
        elif overall_score >= 5.0:
            return "Fair"
        else:
            return "Needs Improvement"

# Example usage and testing
if __name__ == "__main__":
    scorer = LegalResponseQualityScorer()
    
    sample_response = """
    Based on the analysis of GDPR compliance requirements, the following assessment applies:
    
    1. Legal Framework Analysis:
    The General Data Protection Regulation (GDPR) under Article 6 requires a lawful basis 
    for processing personal data. For biometric data processing, explicit consent under 
    Article 9 may be required as it constitutes special category data.
    
    2. Compliance Requirements:
    Organizations must implement appropriate technical and organizational measures,
    conduct Data Protection Impact Assessments, and potentially appoint a Data Protection Officer.
    
    3. Recommendations:
    Therefore, companies should review their current data processing activities and
    ensure compliance with these regulatory requirements.
    
    Policy analysis complete.
    """
    
    sample_query = "What are the GDPR compliance requirements for processing biometric data?"
    
    metrics = scorer.analyze_response_quality(sample_response, sample_query, "policy_analyst")
    print(f"Overall Score: {metrics.overall_score}/10")
    print(f"Confidence Level: {metrics.confidence_level}")
    print(f"Suggestions: {metrics.suggestions}")
