#!/bin/bash
# Azure Region Availability Checker for Legal Mind Agent
# This script validates regional availability for required Azure services

set -e

#!/bin/bash
# Azure Region Availability Checker for Legal Mind Agent
# This script validates regional availability for required Azure services

set -e

# Define service availability by region (using arrays instead of associative arrays for macOS compatibility)
REGIONS=("eastus2" "westus2" "northeurope" "uksouth" "australiaeast" "japaneast" "eastus" "westus" "southcentralus")

# Service availability mapping
get_services_for_region() {
    case $1 in
        "eastus2") echo "agents,model-router,app-service,container-apps,cognitive-services" ;;
        "westus2") echo "agents,model-router,app-service,container-apps,cognitive-services" ;;
        "northeurope") echo "agents,model-router,app-service,container-apps,cognitive-services" ;;
        "uksouth") echo "agents,model-router,app-service,container-apps,cognitive-services" ;;
        "australiaeast") echo "agents,app-service,container-apps,cognitive-services" ;;
        "japaneast") echo "agents,app-service,container-apps,cognitive-services" ;;
        "eastus") echo "app-service,container-apps,cognitive-services" ;;
        "westus") echo "app-service,container-apps,cognitive-services" ;;
        "southcentralus") echo "app-service,container-apps,cognitive-services" ;;
        *) echo "" ;;
    esac
}

# Required services for Legal Mind Agent
REQUIRED_SERVICES=("agents" "app-service" "cognitive-services")
OPTIONAL_SERVICES=("model-router" "container-apps")

function check_region_support() {
    local region=$1
    local services=$(get_services_for_region "$region")
    
    if [[ -z "$services" ]]; then
        echo "❌ Region '$region' is not in our validated list"
        return 1
    fi
    
    echo "🌍 Checking region: $region"
    echo "📋 Available services: $services"
    
    # Check required services
    local missing_required=()
    for service in "${REQUIRED_SERVICES[@]}"; do
        if [[ ! "$services" =~ $service ]]; then
            missing_required+=($service)
        fi
    done
    
    # Check optional services
    local missing_optional=()
    for service in "${OPTIONAL_SERVICES[@]}"; do
        if [[ ! "$services" =~ $service ]]; then
            missing_optional+=($service)
        fi
    done
    
    if [[ ${#missing_required[@]} -eq 0 ]]; then
        echo "✅ All required services available"
        
        if [[ ${#missing_optional[@]} -eq 0 ]]; then
            echo "🎯 Perfect match - all services available!"
            return 0
        else
            echo "⚠️  Missing optional services: ${missing_optional[*]}"
            echo "💡 Deployment will work but some features may be limited"
            return 0
        fi
    else
        echo "❌ Missing required services: ${missing_required[*]}"
        echo "🚫 Cannot deploy to this region"
        return 1
    fi
}

function show_recommendations() {
    echo ""
    echo "🏆 Recommended regions (all services available):"
    for region in "${REGIONS[@]}"; do
        local services=$(get_services_for_region "$region")
        local has_all=true
        
        for service in "${REQUIRED_SERVICES[@]}" "${OPTIONAL_SERVICES[@]}"; do
            if [[ ! "$services" =~ $service ]]; then
                has_all=false
                break
            fi
        done
        
        if [[ "$has_all" == true ]]; then
            echo "  ✅ $region (Full feature set)"
        fi
    done
    
    echo ""
    echo "⚠️  Limited regions (missing some optional services):"
    for region in "${REGIONS[@]}"; do
        local services=$(get_services_for_region "$region")
        local has_required=true
        local has_all=true
        
        # Check required services
        for service in "${REQUIRED_SERVICES[@]}"; do
            if [[ ! "$services" =~ $service ]]; then
                has_required=false
                break
            fi
        done
        
        # Check optional services
        for service in "${OPTIONAL_SERVICES[@]}"; do
            if [[ ! "$services" =~ $service ]]; then
                has_all=false
            fi
        done
        
        if [[ "$has_required" == true && "$has_all" == false ]]; then
            local missing=()
            for service in "${OPTIONAL_SERVICES[@]}"; do
                if [[ ! "$services" =~ $service ]]; then
                    missing+=($service)
                fi
            done
            echo "  ⚠️  $region (Missing: ${missing[*]})"
        fi
    done
}

function main() {
    echo "🔍 Azure Region Availability Checker for Legal Mind Agent"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Required services: ${REQUIRED_SERVICES[*]}"
    echo "Optional services: ${OPTIONAL_SERVICES[*]}"
    echo ""
    
    if [[ $# -eq 0 ]]; then
        show_recommendations
    else
        local region=$1
        check_region_support "$region"
        
        if [[ $? -ne 0 ]]; then
            echo ""
            show_recommendations
            exit 1
        fi
    fi
    
    echo ""
    echo "💡 Usage examples:"
    echo "   ./check-regions.sh                    # Show all recommendations"
    echo "   ./check-regions.sh eastus2           # Check specific region"
    echo "   ./deploy-complete.sh                 # Uses recommended region (eastus2)"
}

main "$@"
