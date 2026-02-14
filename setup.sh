#!/bin/bash

# Quantum Key Generator - Setup Script
# This script sets up both backend and frontend

set -e

echo "========================================="
echo "Quantum Key Generator - Setup Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
echo ""

# Check Node version
echo -e "${BLUE}Checking Node.js version...${NC}"
node_version=$(node --version 2>&1)
echo "Found Node $node_version"
echo ""

# Setup Backend
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setting up Backend (Python/Qiskit)${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

cd backend

# Create virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Backend setup complete!${NC}"
echo ""

# Deactivate for now
deactivate

# Setup Frontend
cd ../frontend

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setting up Frontend (React)${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
npm install

echo -e "${GREEN}✓ Frontend setup complete!${NC}"
echo ""

cd ..

# Final instructions
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup Complete! 🎉${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}To start the application:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend:${NC}"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo -e "${YELLOW}Terminal 2 - Frontend:${NC}"
echo "  cd frontend"
echo "  npm start"
echo ""
echo -e "${BLUE}Then open http://localhost:3000 in your browser${NC}"
echo ""
