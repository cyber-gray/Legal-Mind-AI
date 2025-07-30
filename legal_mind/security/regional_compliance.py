#!/usr/bin/env python3
"""
Regional Compliance and Data Residency for Legal Mind Agent

Ensures data residency compliance and regional deployment requirements
for legal AI services across different jurisdictions.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from enum import Enum

logger = logging.getLogger(__name__)

class DataResidencyRegion(Enum):
    """Supported data residency regions"""
    US_EAST_2 = "eastus2"
    US_WEST_2 = "westus2" 
    EU_WEST = "westeurope"
    EU_NORTH = "northeurope"
    UK_SOUTH = "uksouth"
    CANADA_CENTRAL = "canadacentral"
    AUSTRALIA_EAST = "australiaeast"
    JAPAN_EAST = "japaneast"

class ComplianceJurisdiction(Enum):
    """Legal compliance jurisdictions"""
    GDPR = "gdpr"  # European Union
    CCPA = "ccpa"  # California
    PIPEDA = "pipeda"  # Canada
    PRIVACY_ACT = "privacy_act"  # Australia 
    LGPD = "lgpd"  # Brazil
    PDPA_SG = "pdpa_sg"  # Singapore

class RegionalComplianceManager:
    """
    Manages regional compliance and data residency requirements
    
    Features:
    - Data residency validation
    - Cross-border transfer controls
    - Jurisdiction-specific compliance rules
    - Conversation transcript regional storage
    - Audit trail for compliance reporting
    """
    
    def __init__(self, primary_region: DataResidencyRegion = DataResidencyRegion.US_EAST_2):
        """
        Initialize regional compliance manager
        
        Args:
            primary_region: Primary data residency region
        """
        self.primary_region = primary_region
        self.region_jurisdictions = self._get_region_jurisdictions()
        self.cross_border_restrictions = self._get_cross_border_restrictions()
        self.conversation_storage_regions = {}
        self.compliance_violations = []
        
    def _get_region_jurisdictions(self) -> Dict[DataResidencyRegion, List[ComplianceJurisdiction]]:
        """Map regions to applicable compliance jurisdictions"""
        return {
            DataResidencyRegion.US_EAST_2: [ComplianceJurisdiction.CCPA],
            DataResidencyRegion.US_WEST_2: [ComplianceJurisdiction.CCPA],
            DataResidencyRegion.EU_WEST: [ComplianceJurisdiction.GDPR],
            DataResidencyRegion.EU_NORTH: [ComplianceJurisdiction.GDPR],
            DataResidencyRegion.UK_SOUTH: [ComplianceJurisdiction.GDPR],
            DataResidencyRegion.CANADA_CENTRAL: [ComplianceJurisdiction.PIPEDA],
            DataResidencyRegion.AUSTRALIA_EAST: [ComplianceJurisdiction.PRIVACY_ACT],
            DataResidencyRegion.JAPAN_EAST: []  # Japan-specific regulations would be added here
        }
    
    def _get_cross_border_restrictions(self) -> Dict[ComplianceJurisdiction, Dict[str, Any]]:
        """Get cross-border data transfer restrictions by jurisdiction"""
        return {
            ComplianceJurisdiction.GDPR: {
                "allowed_regions": [
                    DataResidencyRegion.EU_WEST,
                    DataResidencyRegion.EU_NORTH,
                    DataResidencyRegion.UK_SOUTH
                ],
                "adequacy_decisions": [
                    DataResidencyRegion.CANADA_CENTRAL,
                    DataResidencyRegion.JAPAN_EAST
                ],
                "requires_sccs": True,  # Standard Contractual Clauses
                "requires_dpia": True   # Data Protection Impact Assessment
            },
            ComplianceJurisdiction.CCPA: {
                "allowed_regions": [
                    DataResidencyRegion.US_EAST_2,
                    DataResidencyRegion.US_WEST_2,
                    DataResidencyRegion.CANADA_CENTRAL
                ],
                "cross_border_notice_required": True,
                "user_consent_required": False
            },
            ComplianceJurisdiction.PIPEDA: {
                "allowed_regions": [
                    DataResidencyRegion.CANADA_CENTRAL,
                    DataResidencyRegion.US_EAST_2,
                    DataResidencyRegion.US_WEST_2
                ],
                "requires_privacy_policy_disclosure": True
            }
        }
    
    def validate_service_deployment(self, service_endpoints: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate that all Azure services are deployed in compliant regions
        
        Args:
            service_endpoints: Dictionary mapping service names to endpoint URLs
            
        Returns:
            Validation results with compliance status
        """
        validation_result = {
            "compliant": True,
            "primary_region": self.primary_region.value,
            "services": {},
            "violations": [],
            "recommendations": []
        }
        
        for service_name, endpoint in service_endpoints.items():
            service_region = self._extract_region_from_endpoint(endpoint)
            region_enum = self._get_region_enum(service_region)
            
            service_validation = {
                "endpoint": endpoint,
                "detected_region": service_region,
                "compliant": False,
                "issues": []
            }
            
            if region_enum == self.primary_region:
                service_validation["compliant"] = True
            else:
                validation_result["compliant"] = False
                service_validation["issues"].append(f"Service not in primary region {self.primary_region.value}")
                
                # Check if cross-border transfer is allowed
                transfer_allowed = self._check_cross_border_transfer(region_enum)
                if not transfer_allowed:
                    violation = {
                        "service": service_name,
                        "issue": "Cross-border transfer violation",
                        "current_region": service_region,
                        "required_region": self.primary_region.value
                    }
                    validation_result["violations"].append(violation)
                    self.compliance_violations.append(violation)
            
            validation_result["services"][service_name] = service_validation
        
        # Generate recommendations
        if not validation_result["compliant"]:
            validation_result["recommendations"] = self._generate_compliance_recommendations(validation_result)
        
        return validation_result
    
    def _extract_region_from_endpoint(self, endpoint: str) -> Optional[str]:
        """Extract Azure region from service endpoint URL"""
        try:
            # Handle different Azure endpoint formats
            parts = endpoint.lower().replace("https://", "").split(".")
            
            # Look for region indicators in URL parts
            for part in parts:
                # Direct region match
                for region in DataResidencyRegion:
                    if region.value in part:
                        return region.value
                
                # Handle common Azure region formats
                if "eastus2" in part or "east-us-2" in part:
                    return "eastus2"
                elif "westus2" in part or "west-us-2" in part:
                    return "westus2"
                elif "westeurope" in part or "west-europe" in part:
                    return "westeurope"
                elif "northeurope" in part or "north-europe" in part:
                    return "northeurope"
                elif "uksouth" in part or "uk-south" in part:
                    return "uksouth"
                elif "canadacentral" in part or "canada-central" in part:
                    return "canadacentral"
                elif "australiaeast" in part or "australia-east" in part:
                    return "australiaeast"
                elif "japaneast" in part or "japan-east" in part:
                    return "japaneast"
            
            logger.warning(f"Could not extract region from endpoint: {endpoint}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting region from endpoint {endpoint}: {e}")
            return None
    
    def _get_region_enum(self, region_str: Optional[str]) -> Optional[DataResidencyRegion]:
        """Convert region string to enum"""
        if not region_str:
            return None
        
        for region in DataResidencyRegion:
            if region.value == region_str:
                return region
        
        return None
    
    def _check_cross_border_transfer(self, target_region: Optional[DataResidencyRegion]) -> bool:
        """Check if cross-border transfer to target region is allowed"""
        if not target_region:
            return False
        
        # Get applicable jurisdictions for primary region
        primary_jurisdictions = self.region_jurisdictions.get(self.primary_region, [])
        
        for jurisdiction in primary_jurisdictions:
            restrictions = self.cross_border_restrictions.get(jurisdiction, {})
            
            # Check if target region is explicitly allowed
            allowed_regions = restrictions.get("allowed_regions", [])
            if target_region in allowed_regions:
                continue
            
            # Check adequacy decisions (for GDPR)
            adequacy_regions = restrictions.get("adequacy_decisions", [])
            if target_region in adequacy_regions:
                continue
            
            # If we get here, transfer may be restricted
            return False
        
        return True
    
    def _generate_compliance_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations to fix compliance issues"""
        recommendations = []
        
        if validation_result["violations"]:
            recommendations.append(
                f"Redeploy all Azure services to {self.primary_region.value} region for data residency compliance"
            )
        
        non_compliant_services = [
            name for name, details in validation_result["services"].items() 
            if not details["compliant"]
        ]
        
        if non_compliant_services:
            recommendations.append(
                f"Services requiring region migration: {', '.join(non_compliant_services)}"
            )
        
        # Add jurisdiction-specific recommendations
        primary_jurisdictions = self.region_jurisdictions.get(self.primary_region, [])
        
        if ComplianceJurisdiction.GDPR in primary_jurisdictions:
            recommendations.extend([
                "Implement Standard Contractual Clauses (SCCs) for any EU data transfers",
                "Conduct Data Protection Impact Assessment (DPIA) for AI processing",
                "Ensure explicit consent for cross-border data transfers"
            ])
        
        if ComplianceJurisdiction.CCPA in primary_jurisdictions:
            recommendations.extend([
                "Update privacy policy to disclose cross-border data transfers",
                "Implement consumer rights requests handling (access, deletion, portability)"
            ])
        
        return recommendations
    
    def log_conversation_storage(self, conversation_id: str, user_region: Optional[str] = None) -> Dict[str, Any]:
        """
        Log conversation storage location for compliance audit
        
        Args:
            conversation_id: Unique conversation identifier
            user_region: User's region if known
            
        Returns:
            Storage logging result
        """
        storage_info = {
            "conversation_id": conversation_id,
            "storage_region": self.primary_region.value,
            "user_region": user_region,
            "timestamp": datetime.utcnow().isoformat(),
            "cross_border_transfer": False,
            "compliance_notes": []
        }
        
        # Check if this constitutes a cross-border transfer
        if user_region and user_region != self.primary_region.value:
            user_region_enum = self._get_region_enum(user_region)
            if user_region_enum:
                transfer_allowed = self._check_cross_border_transfer(user_region_enum)
                storage_info["cross_border_transfer"] = True
                
                if not transfer_allowed:
                    storage_info["compliance_notes"].append("Cross-border transfer may require additional safeguards")
                
                # Add jurisdiction-specific notes
                primary_jurisdictions = self.region_jurisdictions.get(self.primary_region, [])
                if ComplianceJurisdiction.GDPR in primary_jurisdictions:
                    storage_info["compliance_notes"].append("GDPR: Data processed outside EU - Article 44-49 apply")
        
        # Store for audit trail
        self.conversation_storage_regions[conversation_id] = storage_info
        
        # Log for compliance audit
        logger.info(f"Conversation storage audit: {json.dumps(storage_info)}")
        
        return storage_info
    
    def get_data_residency_report(self) -> Dict[str, Any]:
        """Generate comprehensive data residency compliance report"""
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "primary_region": self.primary_region.value,
            "applicable_jurisdictions": [j.value for j in self.region_jurisdictions.get(self.primary_region, [])],
            "total_conversations": len(self.conversation_storage_regions),
            "cross_border_conversations": len([
                c for c in self.conversation_storage_regions.values() 
                if c["cross_border_transfer"]
            ]),
            "compliance_violations": self.compliance_violations,
            "regional_distribution": self._get_regional_distribution(),
            "compliance_recommendations": self._get_compliance_recommendations()
        }
        
        return report
    
    def _get_regional_distribution(self) -> Dict[str, int]:
        """Get distribution of conversations by user region"""
        distribution = {}
        
        for storage_info in self.conversation_storage_regions.values():
            user_region = storage_info.get("user_region", "unknown")
            distribution[user_region] = distribution.get(user_region, 0) + 1
        
        return distribution
    
    def _get_compliance_recommendations(self) -> List[str]:
        """Get current compliance recommendations"""
        recommendations = []
        
        primary_jurisdictions = self.region_jurisdictions.get(self.primary_region, [])
        
        if ComplianceJurisdiction.GDPR in primary_jurisdictions:
            recommendations.extend([
                "Regular GDPR compliance audits required",
                "Implement data subject rights handling (GDPR Articles 15-22)",
                "Maintain records of processing activities (GDPR Article 30)",
                "Appoint Data Protection Officer if required (GDPR Article 37)"
            ])
        
        if ComplianceJurisdiction.CCPA in primary_jurisdictions:
            recommendations.extend([
                "Implement CCPA consumer rights portal",
                "Update privacy policy with CCPA disclosures",
                "Train staff on CCPA compliance requirements"
            ])
        
        if self.compliance_violations:
            recommendations.append("Address identified compliance violations immediately")
        
        return recommendations

# Global regional compliance manager instance
_regional_compliance: Optional[RegionalComplianceManager] = None

def get_regional_compliance_manager() -> RegionalComplianceManager:
    """Get the global regional compliance manager instance"""
    global _regional_compliance
    if _regional_compliance is None:
        _regional_compliance = RegionalComplianceManager(DataResidencyRegion.US_EAST_2)
    return _regional_compliance
