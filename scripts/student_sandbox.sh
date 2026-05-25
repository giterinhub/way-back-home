#!/bin/bash
# =============================================================================
# Way Back Home - Student Sandbox Environment Initializer
# =============================================================================
#
# This script sets up a clean, localized sub-environment for a student
# executing the entire workshop (Levels 0-5) in record time using
# Google AI Studio and billing-free SQLite / local-first mocks.
#
# Run this from the repository root: ./scripts/student_sandbox.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print Banner
echo -e "${CYAN}"
echo "================================================================="
echo "🎓 WAY BACK HOME - STUDENT SANDBOX INITIALIZER"
echo "================================================================="
echo -e "${NC}"

# =============================================================================
# Step 1: Pre-flight Checks
# =============================================================================
echo -e "${CYAN}[1/4] Running pre-flight configuration checks...${NC}"

# Check for GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ ERROR: GEMINI_API_KEY environment variable is not set!${NC}"
    echo -e "   Please claim a free Gemini API key from Google AI Studio:"
    echo -e "   👉 https://aistudio.google.com/"
    echo -e "   Then export it before running this script:"
    echo -e "   ${YELLOW}export GEMINI_API_KEY=\"your_key_here\"${NC}"
    echo ""
    exit 1
else
    echo -e "${GREEN}✅ GEMINI_API_KEY detected! (Length: ${#GEMINI_API_KEY} chars)${NC}"
fi

# Check Git Branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$CURRENT_BRANCH" != "feature/aistudio" ]; then
    echo -e "${YELLOW}⚠️  WARNING: You are on branch '${CURRENT_BRANCH}'.${NC}"
    echo -e "   For the billing-free AI Studio experience, you should be on ${GREEN}feature/aistudio${NC}."
    echo -e "   Switching to 'feature/aistudio' automatically..."
    git checkout feature/aistudio || {
        echo -e "${RED}❌ Failed to checkout feature/aistudio branch. Please do so manually.${NC}"
    }
else
    echo -e "${GREEN}✅ Active Git Branch: ${CURRENT_BRANCH}${NC}"
fi

# Check Python 3
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo -e "${RED}❌ ERROR: Python is not installed. Python 3.10+ is required.${NC}"
    exit 1
else
    PY_CMD="python3"
    if ! command -v python3 &>/dev/null; then PY_CMD="python"; fi
    PY_VER=$($PY_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✅ Python detected: Version $PY_VER${NC}"
fi

# Check Node/NPM for frontend (Optional)
if ! command -v npm &>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: npm (Node.js) is not installed.${NC}"
    echo -e "   Frontends will run in cloud-map viewer mode (recommended for speed anyway!)${NC}"
else
    echo -e "${GREEN}✅ Node/npm detected: $(npm -v)${NC}"
fi

echo ""

# =============================================================================
# Step 2: Initialize Root Virtual Environment
# =============================================================================
echo -e "${CYAN}[2/4] Setting up root virtual environment and dependencies...${NC}"
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment .venv..."
    $PY_CMD -m venv .venv
fi

# Activate virtual environment
if [ -d ".venv/Scripts" ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "Installing/upgrading fundamental python tooling..."
pip install --upgrade pip setuptools --quiet

echo -e "${GREEN}✅ Virtual environment successfully configured and activated!${NC}"
echo ""

# =============================================================================
# Step 3: Run Workshop Registration
# =============================================================================
echo -e "${CYAN}[3/4] Registering as a student in the active workshop...${NC}"

# Run setup.sh to reserve identity and generate config.json
chmod +x ./scripts/setup.sh
./scripts/setup.sh

if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ ERROR: Setup script failed to generate config.json.${NC}"
    exit 1
fi

# Source environment variables automatically if set_env.sh was created
if [ -f "set_env.sh" ]; then
    chmod +x set_env.sh
    source set_env.sh
fi

echo ""

# =============================================================================
# Step 4: Environment Ready and Walkthrough Invitation
# =============================================================================
echo -e "${CYAN}[4/4] Finalizing student workspace...${NC}"

echo -e "${GREEN}================================================================="
echo "🎉 STUDENT SANDBOX PREPARATION COMPLETE!"
echo "================================================================="
echo -e "${NC}"
echo -e "You are now running in a premium, 100% billing-free local student sandbox!"
echo -e "Your configuration is saved in: ${YELLOW}config.json${NC}"
echo ""
echo -e "To start the guided workshop walkthrough:"
echo -e "👉 Please open the file: ${YELLOW}student_walkthrough.md${NC} in the workspace or artifact directory."
echo ""
echo -e "Happy hacking, Space Explorer! 🚀"
echo "================================================================="
