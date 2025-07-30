#!/usr/bin/env python3
"""
Content Safety and PII Protection for Legal Mind Agent

Implements Azure AI Content Safety filters and PII scrubbing to ensure
compliance with data protection regulations and content policies.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import hashlib

try:
    from azure.ai.contentsafety import ContentSafetyClient
    from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import AzureError
    CONTENT_SAFETY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Azure Content Safety SDK not available: {e}")
    CONTENT_SAFETY_AVAILABLE = False
    # Mock classes for development
    class ContentSafetyClient: pass
    class AnalyzeTextOptions: pass
    class TextCategory: pass
    class DefaultAzureCredential: pass
    class AzureError(Exception): pass

logger = logging.getLogger(__name__)

class ContentSafetyFilter:
    """
    Azure AI Content Safety integration for Legal Mind Agent
    
    Features:
    - Harmful content detection and filtering
    - Custom legal content policies
    - Audit logging for compliance
    - Regional deployment compliance
    """
    
    def __init__(self, endpoint: Optional[str] = None, credential: Optional[Any] = None):
        """
        Initialize Content Safety client
        
        Args:
            endpoint: Azure Content Safety endpoint
            credential: Azure credential for authentication
        """
        self.endpoint = endpoint
        self.credential = credential or DefaultAzureCredential()
        self.client = None
        self.filter_levels = {
            "hate": 2,      # Medium filtering for hate speech
            "sexual": 4,    # High filtering for sexual content  
            "violence": 2,  # Medium filtering for violence
            "self_harm": 4  # High filtering for self-harm content
        }
        
        if CONTENT_SAFETY_AVAILABLE and endpoint:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure Content Safety client"""
        try:
            self.client = ContentSafetyClient(
                endpoint=self.endpoint,
                credential=self.credential
            )
            logger.info("Content Safety client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Content Safety client: {e}")
            self.client = None
    
    async def analyze_content(self, text: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Analyze text content for safety violations
        
        Args:
            text: Text content to analyze
            user_id: User identifier for audit logging
            
        Returns:
            Analysis results with safety scores and recommendations
        """
        analysis_result = {
            "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "safe": True,
            "categories": {},
            "blocked_reasons": [],
            "filtered_text": text,
            "audit_required": False
        }
        
        if not self.client:
            logger.warning("Content Safety client not available - allowing content")
            return analysis_result
        
        try:
            # Analyze with Azure Content Safety
            request = AnalyzeTextOptions(text=text)
            response = self.client.analyze_text(request)
            
            # Process category results
            for category_result in response.categories_analysis:
                category_name = category_result.category.lower()
                severity = category_result.severity
                
                analysis_result["categories"][category_name] = {
                    "severity": severity,
                    "threshold": self.filter_levels.get(category_name, 2)
                }
                
                # Check if content should be blocked
                if severity >= self.filter_levels.get(category_name, 2):
                    analysis_result["safe"] = False
                    analysis_result["blocked_reasons"].append(f"{category_name}: severity {severity}")
            
            # Additional legal-specific content checks
            legal_analysis = self._analyze_legal_content(text)
            analysis_result.update(legal_analysis)
            
            # Log for audit if content was blocked or flagged
            if not analysis_result["safe"] or analysis_result.get("legal_concerns"):
                analysis_result["audit_required"] = True
                self._log_content_analysis(analysis_result, text)
            
        except Exception as e:
            logger.error(f"Content safety analysis failed: {e}")
            # Fail safe - allow content but log error
            analysis_result["error"] = str(e)
        
        return analysis_result
    
    def _analyze_legal_content(self, text: str) -> Dict[str, Any]:
        """
        Analyze content for legal-specific concerns
        
        Args:
            text: Text content to analyze
            
        Returns:
            Legal content analysis results
        """
        legal_analysis = {
            "legal_concerns": [],
            "privileged_content_detected": False,
            "specific_legal_advice_detected": False,
            "client_confidential_detected": False
        }
        
        # Check for privileged content patterns
        privileged_patterns = [
            r"attorney[- ]client privilege",
            r"confidential.*communication",
            r"work product",
            r"privileged.*confidential",
            r"legal advice.*privilege"
        ]
        
        for pattern in privileged_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                legal_analysis["privileged_content_detected"] = True
                legal_analysis["legal_concerns"].append("Potential attorney-client privileged content")
                break
        
        # Check for specific legal advice (which we should not provide)
        specific_advice_patterns = [
            r"you should file a lawsuit",
            r"this is definitely illegal",
            r"you have a strong case",
            r"I recommend suing",
            r"this violates.*law.*you should"
        ]
        
        for pattern in specific_advice_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                legal_analysis["specific_legal_advice_detected"] = True
                legal_analysis["legal_concerns"].append("Potential specific legal advice")
                break
        
        # Check for client confidential information patterns
        confidential_patterns = [
            r"my client.*confidential",
            r"case number.*\d{4,}",
            r"docket.*number",
            r"settlement.*amount.*\$\d+"
        ]
        
        for pattern in confidential_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                legal_analysis["client_confidential_detected"] = True
                legal_analysis["legal_concerns"].append("Potential client confidential information")
                break
        
        return legal_analysis
    
    def _log_content_analysis(self, analysis_result: Dict[str, Any], original_text: str) -> None:
        """Log content analysis for audit purposes"""
        audit_entry = {
            "timestamp": analysis_result["timestamp"],
            "user_id": analysis_result["user_id"],
            "text_hash": analysis_result["text_hash"],
            "content_length": len(original_text),
            "safety_result": analysis_result["safe"],
            "blocked_reasons": analysis_result["blocked_reasons"],
            "legal_concerns": analysis_result.get("legal_concerns", []),
            "action_taken": "blocked" if not analysis_result["safe"] else "flagged"
        }
        
        # Log to audit system (in production, this would go to Azure Monitor/Log Analytics)
        logger.warning(f"Content safety audit: {json.dumps(audit_entry, indent=2)}")

class PIIScrubber:
    """
    PII (Personally Identifiable Information) detection and scrubbing
    
    Features:
    - Common PII pattern detection
    - Legal-specific sensitive information handling
    - Configurable scrubbing modes (replace, redact, remove)
    - Audit trail for compliance
    """
    
    def __init__(self, scrub_mode: str = "replace"):
        """
        Initialize PII scrubber
        
        Args:
            scrub_mode: How to handle PII - "replace", "redact", or "remove"
        """
        self.scrub_mode = scrub_mode
        self.pii_patterns = self._get_pii_patterns()
        self.legal_sensitive_patterns = self._get_legal_sensitive_patterns()
        
    def _get_pii_patterns(self) -> Dict[str, str]:
        """Get PII detection patterns"""
        return {
            # US Social Security Numbers
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "ssn_spaces": r"\b\d{3}\s\d{2}\s\d{4}\b",
            "ssn_nohyphen": r"\b\d{9}\b",
            
            # Email addresses
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            
            # Phone numbers
            "phone": r"\b\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b",
            "phone_international": r"\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
            
            # Credit card numbers (basic patterns)
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            
            # Driver's license patterns (US format examples)
            "drivers_license": r"\b[A-Z]\d{7,8}\b",
            
            # IP addresses
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            
            # Dates of birth (various formats)
            "dob": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",
            "dob_alt": r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        }
    
    def _get_legal_sensitive_patterns(self) -> Dict[str, str]:
        """Get legal-specific sensitive information patterns"""
        return {
            # Case numbers and docket numbers
            "case_number": r"\b(?:case|docket)\s*(?:no\.?|number|#)\s*[:\-]?\s*\d{2,}[-/]?\w*\d*\b",
            
            # Bar numbers
            "bar_number": r"\bbar\s*(?:no\.?|number|#)\s*[:\-]?\s*\d{4,}\b",
            
            # Settlement amounts
            "settlement_amount": r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:settlement|damages|award)",
            
            # Client names in legal context
            "client_reference": r"\b(?:my|our|the)\s+client\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\b",
            
            # Court names and addresses
            "court_reference": r"\b[A-Z][a-z]*\s+(?:District|Superior|Circuit|County)\s+Court\b",
            
            # Attorney names in signature blocks
            "attorney_signature": r"\b(?:Attorney for|Counsel for|Representing)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\b"
        }
    
    def scrub_text(self, text: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Scrub PII and sensitive information from text
        
        Args:
            text: Text to scrub
            user_id: User identifier for audit logging
            
        Returns:
            Scrubbing results with cleaned text and audit information
        """
        scrub_result = {
            "original_length": len(text),
            "scrubbed_text": text,
            "pii_detected": [],
            "legal_sensitive_detected": [],
            "scrub_count": 0,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scrub_mode": self.scrub_mode
        }
        
        scrubbed_text = text
        
        # Process PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, scrubbed_text, re.IGNORECASE)
            match_count = 0
            
            for match in matches:
                match_count += 1
                scrub_result["pii_detected"].append({
                    "type": pii_type,
                    "position": match.span(),
                    "length": len(match.group())
                })
                
                # Apply scrubbing based on mode
                replacement = self._get_replacement(pii_type, match.group())
                scrubbed_text = scrubbed_text.replace(match.group(), replacement, 1)
            
            scrub_result["scrub_count"] += match_count
        
        # Process legal-specific sensitive patterns
        for sensitive_type, pattern in self.legal_sensitive_patterns.items():
            matches = re.finditer(pattern, scrubbed_text, re.IGNORECASE)
            match_count = 0
            
            for match in matches:
                match_count += 1
                scrub_result["legal_sensitive_detected"].append({
                    "type": sensitive_type,
                    "position": match.span(),
                    "length": len(match.group())
                })
                
                # Apply scrubbing
                replacement = self._get_replacement(sensitive_type, match.group(), is_legal=True)
                scrubbed_text = scrubbed_text.replace(match.group(), replacement, 1)
            
            scrub_result["scrub_count"] += match_count
        
        scrub_result["scrubbed_text"] = scrubbed_text
        scrub_result["final_length"] = len(scrubbed_text)
        
        # Log if PII was detected and scrubbed
        if scrub_result["scrub_count"] > 0:
            self._log_pii_scrubbing(scrub_result)
        
        return scrub_result
    
    def _get_replacement(self, info_type: str, original_text: str, is_legal: bool = False) -> str:
        """
        Get replacement text based on scrub mode and information type
        
        Args:
            info_type: Type of information detected
            original_text: Original text that was detected
            is_legal: Whether this is legal-specific sensitive information
            
        Returns:
            Replacement text
        """
        if self.scrub_mode == "remove":
            return ""
        
        elif self.scrub_mode == "redact":
            return "[REDACTED]"
        
        else:  # replace mode
            if is_legal:
                replacements = {
                    "case_number": "[CASE NUMBER]",
                    "bar_number": "[BAR NUMBER]", 
                    "settlement_amount": "[SETTLEMENT AMOUNT]",
                    "client_reference": "[CLIENT NAME]",
                    "court_reference": "[COURT NAME]",
                    "attorney_signature": "[ATTORNEY NAME]"
                }
                return replacements.get(info_type, "[LEGAL INFO]")
            else:
                replacements = {
                    "ssn": "[SSN]",
                    "ssn_spaces": "[SSN]",
                    "ssn_nohyphen": "[SSN]",
                    "email": "[EMAIL]",
                    "phone": "[PHONE]",
                    "phone_international": "[PHONE]",
                    "credit_card": "[CREDIT CARD]",
                    "drivers_license": "[DRIVER LICENSE]",
                    "ip_address": "[IP ADDRESS]",
                    "dob": "[DATE OF BIRTH]",
                    "dob_alt": "[DATE OF BIRTH]"
                }
                return replacements.get(info_type, "[PII]")
    
    def _log_pii_scrubbing(self, scrub_result: Dict[str, Any]) -> None:
        """Log PII scrubbing for audit purposes"""
        audit_entry = {
            "timestamp": scrub_result["timestamp"],
            "user_id": scrub_result["user_id"],
            "scrub_count": scrub_result["scrub_count"],
            "pii_types": [item["type"] for item in scrub_result["pii_detected"]],
            "legal_sensitive_types": [item["type"] for item in scrub_result["legal_sensitive_detected"]],
            "scrub_mode": scrub_result["scrub_mode"],
            "text_length_change": scrub_result["final_length"] - scrub_result["original_length"]
        }
        
        # Log to audit system
        logger.info(f"PII scrubbing audit: {json.dumps(audit_entry)}")

class ComplianceCoordinator:
    """
    Coordinates content safety and PII protection for Legal Mind Agent
    
    Integrates Azure Content Safety and PII scrubbing with regional compliance
    and comprehensive audit logging.
    """
    
    def __init__(self, content_safety_endpoint: Optional[str] = None, 
                 pii_scrub_mode: str = "replace"):
        """
        Initialize compliance coordinator
        
        Args:
            content_safety_endpoint: Azure Content Safety endpoint
            pii_scrub_mode: PII scrubbing mode
        """
        self.content_filter = ContentSafetyFilter(endpoint=content_safety_endpoint)
        self.pii_scrubber = PIIScrubber(scrub_mode=pii_scrub_mode)
        self.compliance_stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "pii_scrubbed_requests": 0,
            "legal_concerns_flagged": 0
        }
    
    async def process_content(self, text: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Process content through complete compliance pipeline
        
        Args:
            text: Content to process
            user_id: User identifier
            
        Returns:
            Complete compliance processing results
        """
        self.compliance_stats["total_requests"] += 1
        
        # Step 1: Content safety analysis
        safety_result = await self.content_filter.analyze_content(text, user_id)
        
        # Step 2: PII scrubbing (always performed, even if content is blocked)
        pii_result = self.pii_scrubber.scrub_text(text, user_id)
        
        if pii_result["scrub_count"] > 0:
            self.compliance_stats["pii_scrubbed_requests"] += 1
        
        if safety_result.get("legal_concerns"):
            self.compliance_stats["legal_concerns_flagged"] += 1
        
        if not safety_result["safe"]:
            self.compliance_stats["blocked_requests"] += 1
        
        # Combine results
        compliance_result = {
            "safe": safety_result["safe"],
            "processed_text": pii_result["scrubbed_text"] if safety_result["safe"] else "[CONTENT BLOCKED]",
            "content_safety": safety_result,
            "pii_scrubbing": pii_result,
            "compliance_action": "blocked" if not safety_result["safe"] else "processed",
            "audit_required": safety_result.get("audit_required", False) or pii_result["scrub_count"] > 0
        }
        
        return compliance_result
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Get compliance processing statistics"""
        return {
            **self.compliance_stats,
            "block_rate": self.compliance_stats["blocked_requests"] / max(self.compliance_stats["total_requests"], 1),
            "pii_detection_rate": self.compliance_stats["pii_scrubbed_requests"] / max(self.compliance_stats["total_requests"], 1),
            "legal_concern_rate": self.compliance_stats["legal_concerns_flagged"] / max(self.compliance_stats["total_requests"], 1)
        }

# Global compliance coordinator instance
_compliance_coordinator: Optional[ComplianceCoordinator] = None

def get_compliance_coordinator() -> ComplianceCoordinator:
    """Get the global compliance coordinator instance"""
    global _compliance_coordinator
    if _compliance_coordinator is None:
        _compliance_coordinator = ComplianceCoordinator()
    return _compliance_coordinator
