#!/bin/bash

# Setup script for zip code lookup and environment variable configuration
# Usage: ./setup_location.sh <zip_code>

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
BACKEND_DIR="."
ENV_FILE="$BACKEND_DIR/.env"
API_ENDPOINT="http://localhost:8000/api/v1/zip"

# Function to display usage
show_usage() {
    echo -e "${BLUE}Usage:${NC} $0 <zip_code>"
    echo ""
    echo -e "${YELLOW}Description:${NC}"
    echo "  This script looks up a zip code using the /zip endpoint and configures"
    echo "  LATITUDE and LONGITUDE environment variables in the backend/.env file."
    echo ""
    echo -e "${YELLOW}Arguments:${NC}"
    echo "  zip_code    A valid US zip code (e.g., 90210, 10001)"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 90210     # Beverly Hills, CA"
    echo "  $0 10001     # New York, NY"
    echo "  $0 94102     # San Francisco, CA"
    echo ""
    echo -e "${YELLOW}Requirements:${NC}"
    echo "  - curl (for API requests)"
    echo "  - jq (for JSON parsing)"
    echo "  - Backend API server running on localhost:8000"
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=()

    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi

    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Error:${NC} Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo -e "${YELLOW}Installation instructions:${NC}"
        for dep in "${missing_deps[@]}"; do
            case $dep in
                curl)
                    echo "  macOS: brew install curl"
                    echo "  Ubuntu/Debian: apt-get install curl"
                    ;;
                jq)
                    echo "  macOS: brew install jq"
                    echo "  Ubuntu/Debian: apt-get install jq"
                    ;;
            esac
        done
        return 1
    fi

    return 0
}

# Function to validate zip code format
validate_zip_code() {
    local zip_code="$1"

    # Check if zip code is 5 digits or 5+4 format
    if [[ ! $zip_code =~ ^[0-9]{5}(-[0-9]{4})?$ ]]; then
        echo -e "${RED}Error:${NC} Invalid zip code format. Use 5-digit (12345) or 9-digit (12345-6789) format."
        return 1
    fi

    return 0
}

# Function to check if API server is running
check_api_server() {
    echo -e "${BLUE}Checking if API server is running...${NC}"

    if ! curl -s -f "$API_ENDPOINT" &> /dev/null; then
        # Try the health endpoint instead
        if ! curl -s -f "http://localhost:8000/api/v1/health" &> /dev/null; then
            echo -e "${RED}Error:${NC} API server is not running on localhost:8000"
            echo ""
            echo -e "${YELLOW}To start the server:${NC}"
            echo "  cd backend"
            echo "  python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
            return 1
        fi
    fi

    echo -e "${GREEN}✓${NC} API server is running"
    return 0
}

# Function to lookup zip code
lookup_zip_code() {
    local zip_code="$1"

    echo -e "${BLUE}Looking up zip code: ${zip_code}${NC}"

    # Prepare the JSON payload
    local json_payload=$(jq -n --arg zip "$zip_code" '{zip_code: $zip, country: "US"}')

    # Make the API request
    local response
    response=$(curl -s -X POST "$API_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    local curl_exit_code=$?

    if [ $curl_exit_code -ne 0 ]; then
        echo -e "${RED}Error:${NC} Failed to make API request (curl exit code: $curl_exit_code)"
        return 1
    fi

    # Check if the response contains an error
    local error_message
    error_message=$(echo "$response" | jq -r '.detail // empty' 2>/dev/null)

    if [ -n "$error_message" ]; then
        echo -e "${RED}Error:${NC} API returned an error: $error_message"
        return 1
    fi

    # Extract coordinates from response
    local latitude longitude city state status

    status=$(echo "$response" | jq -r '.status // empty')
    if [ "$status" != "ok" ]; then
        echo -e "${RED}Error:${NC} Zip code lookup failed with status: $status"
        return 1
    fi

    latitude=$(echo "$response" | jq -r '.latitude // empty')
    longitude=$(echo "$response" | jq -r '.longitude // empty')
    city=$(echo "$response" | jq -r '.city // empty')
    state=$(echo "$response" | jq -r '.state // empty')

    if [ -z "$latitude" ] || [ -z "$longitude" ]; then
        echo -e "${RED}Error:${NC} Could not extract coordinates from response"
        echo -e "${YELLOW}Response:${NC} $response"
        return 1
    fi

    echo -e "${GREEN}✓${NC} Found location: $city, $state"
    echo -e "${GREEN}✓${NC} Coordinates: $latitude, $longitude"

    # Store the coordinates for use in update_env_file
    export FOUND_LATITUDE="$latitude"
    export FOUND_LONGITUDE="$longitude"
    export FOUND_CITY="$city"
    export FOUND_STATE="$state"

    return 0
}

# Function to update .env file
update_env_file() {
    echo -e "${BLUE}Updating environment variables...${NC}"

    # Create backend directory if it doesn't exist
    if [ ! -d "$BACKEND_DIR" ]; then
        echo -e "${YELLOW}Warning:${NC} Backend directory not found, creating it..."
        mkdir -p "$BACKEND_DIR"
    fi

    # Create or backup existing .env file
    if [ -f "$ENV_FILE" ]; then
        echo -e "${BLUE}Backing up existing .env file...${NC}"
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Create a temporary file for the new .env content
    local temp_env_file=$(mktemp)

    # Copy existing content (excluding LATITUDE and LONGITUDE) if .env exists
    if [ -f "$ENV_FILE" ]; then
        grep -v '^LATITUDE=' "$ENV_FILE" | grep -v '^LONGITUDE=' > "$temp_env_file" || true
    fi

    # Add the new coordinates
    echo "LATITUDE=$FOUND_LATITUDE" >> "$temp_env_file"
    echo "LONGITUDE=$FOUND_LONGITUDE" >> "$temp_env_file"

    # Move temp file to .env
    mv "$temp_env_file" "$ENV_FILE"

    echo -e "${GREEN}✓${NC} Updated $ENV_FILE with:"
    echo -e "    ${YELLOW}LATITUDE=${NC}$FOUND_LATITUDE"
    echo -e "    ${YELLOW}LONGITUDE=${NC}$FOUND_LONGITUDE"

    source $ENV_FILE 2>/dev/null

    return 0
}

# Main function
main() {
    echo -e "${BLUE}=== Zip Code Location Setup ===${NC}"
    echo ""

    # Check arguments
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error:${NC} No zip code provided"
        echo ""
        show_usage
        exit 1
    fi

    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi

    local zip_code="$1"

    # Validate inputs and dependencies
    if ! check_dependencies; then
        exit 1
    fi

    if ! validate_zip_code "$zip_code"; then
        exit 1
    fi

    if ! check_api_server; then
        exit 1
    fi

    # Perform zip code lookup
    if ! lookup_zip_code "$zip_code"; then
        exit 1
    fi

    # Update environment file
    if ! update_env_file; then
        exit 1
    fi

    echo ""
    echo -e "${GREEN}=== Setup Complete ===${NC}"
    echo -e "${GREEN}✓${NC} Location: $FOUND_CITY, $FOUND_STATE"
    echo -e "${GREEN}✓${NC} Environment variables updated in $ENV_FILE"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Restart your backend server to load the new environment variables"
    echo "  2. Test nearby places search with the configured coordinates"
    echo ""
    echo -e "${YELLOW}Example API test:${NC}"
    echo "  curl -X POST http://localhost:8000/api/v1/nearby \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"location\": \"$FOUND_LATITUDE,$FOUND_LONGITUDE\", \"radius\": 1500, \"type\": \"restaurant\"}'"
}

# Run main function with all arguments
main "$@"
