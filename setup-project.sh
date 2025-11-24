#!/bin/bash

# TailorJob Project Setup Script
# This script helps you set up the complete development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup process
main() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║   TailorJob.ai Development Setup         ║"
    echo "╔═══════════════════════════════════════════╗"
    echo -e "${NC}"

    # Step 1: Check prerequisites
    print_step "Checking prerequisites..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi
    print_success "Python $(python3 --version) found"

    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18 or higher."
        exit 1
    fi
    print_success "Node $(node --version) found"

    if ! command_exists npm; then
        print_error "npm is not installed."
        exit 1
    fi
    print_success "npm $(npm --version) found"

    # Check for Supabase CLI
    if command_exists supabase; then
        print_success "Supabase CLI $(supabase --version) found"
        HAS_SUPABASE_CLI=true
    else
        print_warning "Supabase CLI not found (optional)"
        HAS_SUPABASE_CLI=false
    fi

    # Step 2: Backend setup
    print_step "Setting up Python backend..."
    
    if [ ! -d "backend/venv" ]; then
        cd backend
        print_step "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
        
        print_step "Installing Python dependencies..."
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        print_success "Python dependencies installed"
        cd ..
    else
        print_success "Backend virtual environment already exists"
    fi

    # Step 3: Environment configuration
    print_step "Checking environment configuration..."
    
    if [ ! -f "backend/.env" ]; then
        print_warning "backend/.env not found"
        echo "Creating backend/.env from template..."
        cp backend/.env.example backend/.env
        print_success "Created backend/.env"
        print_warning "⚠️  You need to edit backend/.env with your credentials:"
        echo "   - SUPABASE_URL"
        echo "   - SUPABASE_KEY"
        echo "   - UPSTASH_REDIS_URL"
        echo "   - AZURE_OPENAI_ENDPOINT"
        echo "   - AZURE_OPENAI_KEY"
    else
        print_success "backend/.env exists"
    fi

    if [ ! -f ".env" ]; then
        print_warning ".env not found in root"
        if [ -f ".env.local" ]; then
            print_success ".env.local exists (frontend config)"
        else
            print_warning "No frontend .env file found"
        fi
    else
        print_success ".env exists (frontend config)"
    fi

    # Step 4: Database migration status
    print_step "Checking database migration status..."
    
    if [ "$HAS_SUPABASE_CLI" = true ]; then
        print_success "Supabase CLI available - you can use 'supabase db push'"
        
        # Check if linked
        if [ -f "supabase/.temp/project-ref" ]; then
            PROJECT_REF=$(cat supabase/.temp/project-ref)
            print_success "Project linked: $PROJECT_REF"
        else
            print_warning "Project not linked yet"
            echo "   Run: supabase link --project-ref YOUR_PROJECT_REF"
        fi
    else
        print_warning "Without Supabase CLI, you need to apply migrations manually:"
        echo "   1. Go to https://supabase.com/dashboard"
        echo "   2. SQL Editor → New Query"
        echo "   3. Copy SQL from: supabase/migrations/20240122000000_add_cv_tables.sql"
        echo "   4. Run it"
    fi

    # Step 5: Summary and next steps
    echo -e "\n${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Setup Complete! 🎉              ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}\n"

    echo "📋 Next Steps:"
    echo ""
    echo "1️⃣  Configure your credentials:"
    echo "   ${YELLOW}code backend/.env${NC}"
    echo "   Add your Supabase, Upstash, and Azure OpenAI credentials"
    echo ""
    
    echo "2️⃣  Apply database migration:"
    if [ "$HAS_SUPABASE_CLI" = true ]; then
        echo "   ${YELLOW}supabase link --project-ref YOUR_PROJECT_REF${NC}"
        echo "   ${YELLOW}supabase db push${NC}"
    else
        echo "   Copy SQL from supabase/migrations/20240122000000_add_cv_tables.sql"
        echo "   Paste in Supabase Dashboard → SQL Editor"
    fi
    echo ""
    
    echo "3️⃣  Create Supabase Storage bucket:"
    echo "   • Go to Supabase Dashboard → Storage"
    echo "   • Create bucket: ${YELLOW}cv-uploads${NC}"
    echo "   • Set to Private"
    echo ""
    
    echo "4️⃣  Start the backend server:"
    echo "   ${YELLOW}cd backend${NC}"
    echo "   ${YELLOW}source venv/bin/activate${NC}"
    echo "   ${YELLOW}uvicorn app.main:app --reload${NC}"
    echo ""
    
    echo "5️⃣  Test the API:"
    echo "   Visit: ${YELLOW}http://localhost:8000/docs${NC}"
    echo ""
    
    echo "📚 Documentation:"
    echo "   • GETTING_STARTED.md - Quick start guide"
    echo "   • CLI_COMMANDS.md - All available commands"
    echo "   • backend/README.md - Backend documentation"
    echo "   • DATABASE_SCHEMA_EXPLAINED.md - Database structure"
    echo ""
    
    echo "💡 Your frontend is already running on:"
    echo "   ${YELLOW}http://localhost:5173${NC}"
}

# Run main function
main "$@"