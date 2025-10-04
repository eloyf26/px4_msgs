#!/bin/bash
# AirSim Environment Installer
# Downloads and sets up AirSim pre-built environments

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
AIRSIM_ENV_DIR="$HOME/AirSimEnvironments"
ENVIRONMENT="blocks"  # Default environment

# Function to display usage
show_usage() {
    echo -e "${BLUE}AirSim Environment Installer${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --blocks        Install Blocks environment (default, ~400MB, fast)"
    echo "  --landscape     Install Landscape Mountains environment (~5GB, realistic outdoor)"
    echo "  --city          Install City Environment (~8GB, urban)"
    echo "  --dir PATH      Install to custom directory (default: ~/AirSimEnvironments)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --blocks                    # Install Blocks to default location"
    echo "  $0 --landscape --dir /opt/     # Install Landscape to /opt/"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --blocks)
            ENVIRONMENT="blocks"
            shift
            ;;
        --landscape)
            ENVIRONMENT="landscape"
            shift
            ;;
        --city)
            ENVIRONMENT="city"
            shift
            ;;
        --dir)
            AIRSIM_ENV_DIR="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Environment-specific settings
case $ENVIRONMENT in
    blocks)
        ENV_NAME="Blocks"
        ENV_VERSION="1.8.1"
        ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/Blocks.zip"
        ENV_SIZE="~400MB"
        ENV_DIR="LinuxBlocks${ENV_VERSION}"
        ENV_EXEC="Blocks.sh"
        ;;
    landscape)
        ENV_NAME="Landscape Mountains"
        ENV_VERSION="1.8.1"
        ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/LandscapeMountains.zip"
        ENV_SIZE="~5GB"
        ENV_DIR="LinuxLandscapeMountains${ENV_VERSION}"
        ENV_EXEC="LandscapeMountains.sh"
        ;;
    city)
        ENV_NAME="City Environment"
        ENV_VERSION="1.8.1"
        ENV_URL="https://github.com/microsoft/AirSim/releases/download/v1.8.1/CityEnviron.zip"
        ENV_SIZE="~8GB"
        ENV_DIR="LinuxCityEnviron${ENV_VERSION}"
        ENV_EXEC="CityEnviron.sh"
        ;;
esac

echo -e "${GREEN}=== AirSim Environment Installer ===${NC}"
echo -e "${BLUE}Environment: ${ENV_NAME}${NC}"
echo -e "${BLUE}Version: ${ENV_VERSION}${NC}"
echo -e "${BLUE}Size: ${ENV_SIZE}${NC}"
echo -e "${BLUE}Install location: ${AIRSIM_ENV_DIR}/${ENV_DIR}${NC}"
echo ""

# Create directory
echo -e "${YELLOW}Creating installation directory...${NC}"
mkdir -p "$AIRSIM_ENV_DIR"
cd "$AIRSIM_ENV_DIR"

# Check if already installed
if [ -d "$ENV_DIR" ]; then
    echo -e "${YELLOW}Warning: ${ENV_DIR} already exists${NC}"
    read -p "Do you want to re-download? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Using existing installation${NC}"
        echo -e "${GREEN}Environment ready at: ${AIRSIM_ENV_DIR}/${ENV_DIR}/LinuxNoEditor/${ENV_EXEC}${NC}"
        exit 0
    fi
    rm -rf "$ENV_DIR"
fi

# Download
echo -e "${YELLOW}Downloading ${ENV_NAME}...${NC}"
echo -e "${BLUE}This may take a while depending on your internet connection${NC}"
wget --progress=bar:force "$ENV_URL" -O "${ENV_NAME}.zip"

# Verify download
if [ ! -f "${ENV_NAME}.zip" ]; then
    echo -e "${RED}Error: Download failed${NC}"
    exit 1
fi

echo -e "${GREEN}Download complete!${NC}"

# Extract
echo -e "${YELLOW}Extracting environment...${NC}"
unzip -q "${ENV_NAME}.zip"
rm "${ENV_NAME}.zip"

echo -e "${GREEN}Extraction complete!${NC}"

# Make executable
chmod +x "${ENV_DIR}/LinuxNoEditor/${ENV_EXEC}"

# Verify installation
if [ -f "${ENV_DIR}/LinuxNoEditor/${ENV_EXEC}" ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          Installation Successful!                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Environment installed at:${NC}"
    echo -e "  ${AIRSIM_ENV_DIR}/${ENV_DIR}"
    echo ""
    echo -e "${BLUE}To launch AirSim:${NC}"
    echo -e "  ${GREEN}cd ${AIRSIM_ENV_DIR}/${ENV_DIR}/LinuxNoEditor${NC}"
    echo -e "  ${GREEN}./${ENV_EXEC}${NC}"
    echo ""
    echo -e "${YELLOW}Note: First launch may take several minutes to load${NC}"
    echo ""
else
    echo -e "${RED}Error: Installation verification failed${NC}"
    exit 1
fi
