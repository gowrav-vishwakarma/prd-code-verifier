#!/bin/bash

# GitHub Actions Pipeline Runner with Act
# Usage: ./run-pipeline.sh [workflow_file] [event_type]
# Examples:
#   ./run-pipeline.sh                    # Run all workflows with push event
#   ./run-pipeline.sh ci.yml             # Run only ci.yml workflow
#   ./run-pipeline.sh ci.yml pull_request # Run ci.yml with pull_request event
#   ./run-pipeline.sh all push           # Run all workflows with push event

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect macOS and Apple Silicon
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ $(uname -m) == "arm64" ]]; then
            echo "macos-arm64"
        else
            echo "macos-x86_64"
        fi
    else
        echo "linux"
    fi
}

# Function to check and setup Docker socket compatibility
setup_docker_socket() {
    local platform=$(detect_platform)

    if [[ "$platform" == "macos-arm64" || "$platform" == "macos-x86_64" ]]; then
        # Check if the new Docker socket path exists
        if [ -S "$HOME/.docker/run/docker.sock" ]; then
            print_status "Found Docker socket at $HOME/.docker/run/docker.sock"

            # Check if we need to set DOCKER_HOST environment variable
            if [ -z "$DOCKER_HOST" ]; then
                export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
                print_status "Set DOCKER_HOST to $DOCKER_HOST"
            fi
        else
            print_warning "Docker socket not found at expected location"
            print_warning "Make sure Docker Desktop is running"
        fi

        # Check if /var/run/docker.sock exists (for compatibility)
        if [ -S "/var/run/docker.sock" ]; then
            print_status "Found Docker socket at /var/run/docker.sock"
        else
            print_warning "Docker socket not found at /var/run/docker.sock"
            print_warning "This is normal for newer Docker Desktop versions on macOS"
        fi
    fi
}

# Function to get platform-specific Act options
get_platform_options() {
    local platform=$(detect_platform)
    local options=""

    case $platform in
        "macos-arm64")
            # For Apple Silicon Macs, use multiple options for compatibility
            # --container-daemon-socket - disables Docker socket mounting (fixes macOS issues)
            options="--container-architecture linux/amd64 --container-daemon-socket -"
            ;;
        "macos-x86_64")
            # For Intel Macs, use similar options
            # --container-daemon-socket - disables Docker socket mounting (fixes macOS issues)
            options="--container-architecture linux/amd64 --container-daemon-socket -"
            ;;
        "linux")
            options=""
            ;;
    esac

    # Add Docker resource limits if specified
    if [ ! -z "$DOCKER_MEMORY_LIMIT" ]; then
        options="$options --env DOCKER_MEMORY_LIMIT=$DOCKER_MEMORY_LIMIT"
    fi

    if [ ! -z "$DOCKER_CPU_LIMIT" ]; then
        options="$options --env DOCKER_CPU_LIMIT=$DOCKER_CPU_LIMIT"
    fi

    echo "$options"
}

# Function to load secrets from .env file
load_secrets() {
    if [ -f ".env" ]; then
        print_status "Loading secrets from .env file..."
        # Handle .env files with spaces around = and comments
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip empty lines and comments
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                # Check if line contains = sign
                if [[ "$line" =~ = ]]; then
                    # Remove spaces around = and export the variable
                    var_name=$(echo "$line" | cut -d'=' -f1 | xargs)
                    var_value=$(echo "$line" | cut -d'=' -f2- | xargs)
                    # Remove quotes and trailing characters
                    var_value=$(echo "$var_value" | sed 's/^["'\'']//; s/["'\'']$//; s/%$//')
                    if [[ -n "$var_name" && -n "$var_value" ]]; then
                        export "$var_name=$var_value"
                        print_status "Loaded secret: $var_name"
                    fi
                fi
            fi
        done < .env
        print_success "Secrets loaded from .env"
    else
        print_warning "No .env file found. Some workflows may fail if they require secrets."
    fi
}

# Function to setup Docker resource configurations
setup_docker_resources() {
    local resource_profile="$1"

    case $resource_profile in
        "ec2-t2-micro")
            export DOCKER_MEMORY_LIMIT="1g"
            export DOCKER_CPU_LIMIT="1"
            export EC2_SIMULATED_RAM="1g"
            print_status "Simulating EC2 t2.micro: 1GB RAM, 1 vCPU"
            ;;
        "ec2-t2-small")
            export DOCKER_MEMORY_LIMIT="2g"
            export DOCKER_CPU_LIMIT="1"
            export EC2_SIMULATED_RAM="2g"
            print_status "Simulating EC2 t2.small: 2GB RAM, 1 vCPU"
            ;;
        "ec2-t2-medium")
            export DOCKER_MEMORY_LIMIT="4g"
            export DOCKER_CPU_LIMIT="2"
            export EC2_SIMULATED_RAM="4g"
            print_status "Simulating EC2 t2.medium: 4GB RAM, 2 vCPU"
            ;;
        "ec2-t2-large")
            export DOCKER_MEMORY_LIMIT="8g"
            export DOCKER_CPU_LIMIT="2"
            export EC2_SIMULATED_RAM="8g"
            print_status "Simulating EC2 t2.large: 8GB RAM, 2 vCPU"
            ;;
        "ec2-t3-micro")
            export DOCKER_MEMORY_LIMIT="1g"
            export DOCKER_CPU_LIMIT="2"
            export EC2_SIMULATED_RAM="1g"
            print_status "Simulating EC2 t3.micro: 1GB RAM, 2 vCPU"
            ;;
        "ec2-t3-small")
            export DOCKER_MEMORY_LIMIT="2g"
            export DOCKER_CPU_LIMIT="2"
            export EC2_SIMULATED_RAM="2g"
            print_status "Simulating EC2 t3.small: 2GB RAM, 2 vCPU"
            ;;
        "ec2-t3-medium")
            export DOCKER_MEMORY_LIMIT="4g"
            export DOCKER_CPU_LIMIT="2"
            export EC2_SIMULATED_RAM="4g"
            print_status "Simulating EC2 t3.medium: 4GB RAM, 2 vCPU"
            ;;
        "ec2-t3-large")
            export DOCKER_MEMORY_LIMIT="8g"
            export DOCKER_CPU_LIMIT="2"
            export EC2_SIMULATED_RAM="8g"
            print_status "Simulating EC2 t3.large: 8GB RAM, 2 vCPU"
            ;;
        "minimal")
            export DOCKER_MEMORY_LIMIT="512m"
            export DOCKER_CPU_LIMIT="0.5"
            print_status "Using minimal resources: 512MB RAM, 0.5 CPU"
            ;;
        "small")
            export DOCKER_MEMORY_LIMIT="1g"
            export DOCKER_CPU_LIMIT="1"
            print_status "Using small resources: 1GB RAM, 1 CPU"
            ;;
        "medium")
            export DOCKER_MEMORY_LIMIT="2g"
            export DOCKER_CPU_LIMIT="2"
            print_status "Using medium resources: 2GB RAM, 2 CPU"
            ;;
        "large")
            export DOCKER_MEMORY_LIMIT="4g"
            export DOCKER_CPU_LIMIT="4"
            print_status "Using large resources: 4GB RAM, 4 CPU"
            ;;
        "xlarge")
            export DOCKER_MEMORY_LIMIT="8g"
            export DOCKER_CPU_LIMIT="8"
            print_status "Using xlarge resources: 8GB RAM, 8 CPU"
            ;;
        "custom")
            if [ -z "$DOCKER_MEMORY_LIMIT" ] || [ -z "$DOCKER_CPU_LIMIT" ]; then
                print_error "Custom resource profile requires DOCKER_MEMORY_LIMIT and DOCKER_CPU_LIMIT environment variables"
                exit 1
            fi
            print_status "Using custom resources: ${DOCKER_MEMORY_LIMIT} RAM, ${DOCKER_CPU_LIMIT} CPU"
            ;;
        *)
            print_warning "Unknown resource profile: $resource_profile. Using default Docker settings."
            unset DOCKER_MEMORY_LIMIT
            unset DOCKER_CPU_LIMIT
            ;;
    esac
}

# Function to setup secrets for Act
setup_act_secrets() {
    print_status "Setting up secrets for Act..."

    # Create secrets file in the expected location for Act
    SECRETS_FILE=".secrets"

    # Clear the file first
    > "$SECRETS_FILE"

    # Add secrets from environment variables
    if [ ! -z "$DISCORD_WEBHOOK" ]; then
        echo "DISCORD_WEBHOOK=$DISCORD_WEBHOOK" >> "$SECRETS_FILE"
        print_status "Added DISCORD_WEBHOOK secret"
    fi

    if [ ! -z "$GITHUB_TOKEN" ]; then
        echo "GITHUB_TOKEN=$GITHUB_TOKEN" >> "$SECRETS_FILE"
        print_status "Added GITHUB_TOKEN secret"
    fi

    # Add any other secrets your workflows might need
    if [ ! -z "$COVERAGE_REPORTER_TOKEN" ]; then
        echo "COVERAGE_REPORTER_TOKEN=$COVERAGE_REPORTER_TOKEN" >> "$SECRETS_FILE"
        print_status "Added COVERAGE_REPORTER_TOKEN secret"
    fi

    # Check if secrets file has content
    if [ -s "$SECRETS_FILE" ]; then
        print_success "Secrets configured for Act in $SECRETS_FILE"
        echo "$SECRETS_FILE"
    else
        print_warning "No secrets found. Some workflows may fail."
        rm -f "$SECRETS_FILE"
        echo ""
    fi
}

# Function to show help
show_help() {
    echo "GitHub Actions Pipeline Runner with Act"
    echo ""
    echo "Usage: $0 [workflow_file] [event_type]"
    echo ""
    echo "Arguments:"
    echo "  workflow_file    Specific workflow file to run (e.g., ci.yml)"
    echo "                   Use 'all' to run all workflows"
    echo "  event_type       GitHub event type (default: push)"
    echo ""
    echo "Examples:"
echo "  $0                    # Run all workflows with push event"
echo "  $0 ci.yml             # Run only ci.yml workflow"
echo "  $0 ci.yml pull_request # Run ci.yml with pull_request event"
echo "  $0 all push           # Run all workflows with push event"
echo "  $0 ci.yml --resources minimal  # Test with minimal resources (512MB RAM)"
echo "  $0 ci.yml --resources large    # Test with large resources (4GB RAM)"
echo "  $0 ci.yml --resources custom   # Test with custom resources (set DOCKER_MEMORY_LIMIT, DOCKER_CPU_LIMIT)"
echo "  $0 deploy-dev.yml --resources ec2-t2-small  # Test deployment on EC2 t2.small (2GB RAM)"
echo "  $0 deploy-dev.yml --resources ec2-t3-medium # Test deployment on EC2 t3.medium (4GB RAM)"
    echo ""
    echo "Secrets:"
    echo "  Create a .env file with your secrets:"
    echo "    DISCORD_WEBHOOK=https://discord.com/api/webhooks/..."
    echo "    GITHUB_TOKEN=your-github-token"
    echo "    COVERAGE_REPORTER_TOKEN=your-coverage-token"
    echo ""
    echo "Options:"
echo "  --help, -h           Show this help message"
echo "  --dry-run            Show what would be executed without running"
echo "  --verbose            Enable verbose output"
echo "  --resources, -r      Docker resource profile:"
echo "                        EC2 Simulation: ec2-t2-micro, ec2-t2-small, ec2-t2-medium, ec2-t2-large"
echo "                                       ec2-t3-micro, ec2-t3-small, ec2-t3-medium, ec2-t3-large"
echo "                        Standard: minimal, small, medium, large, xlarge, custom"
    echo ""
    echo "Installation:"
    echo "  If Act is not installed, run these commands:"
    echo "    # Install Act"
    echo "    curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    echo ""
    echo "    # Move to system path"
    echo "    sudo mv bin/act /usr/local/bin/act"
    echo ""
    echo "    # Clean up"
    echo "    rmdir bin"
    echo ""
    echo "Prerequisites:"
    echo "  - Docker Desktop running"
    echo "  - Act installed (see installation above)"
    echo "  - .env file with secrets (optional)"
    echo ""
    echo "macOS Notes:"
echo "  - For Apple Silicon (M-series) Macs, the script automatically uses"
echo "    linux/amd64 container architecture and disables Docker socket mounting"
echo "    to resolve compatibility issues with Docker Desktop on macOS"
echo "  - Make sure Docker Desktop is running and properly configured"
echo "  - If you encounter Docker socket mounting issues, the script uses"
echo "    --container-daemon-socket - to disable socket mounting (GitHub issue #2239)"
}

# Parse command line arguments
WORKFLOW_FILE=""
EVENT_TYPE="push"
DRY_RUN=false
VERBOSE=false
RESOURCE_PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --resources|-r)
            RESOURCE_PROFILE="$2"
            shift 2
            ;;
        -*)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [ -z "$WORKFLOW_FILE" ]; then
                WORKFLOW_FILE="$1"
            elif [ -z "$EVENT_TYPE" ]; then
                EVENT_TYPE="$1"
            else
                print_error "Too many arguments"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Act is installed
if ! command -v act &> /dev/null; then
    print_error "Act is not installed. Please install it first:"
    echo "  Run '$0 --help' for installation instructions"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop first."
    exit 1
fi

print_success "Prerequisites check passed"

# Setup Docker socket compatibility for macOS
setup_docker_socket

# Setup Docker resources if specified
if [ ! -z "$RESOURCE_PROFILE" ]; then
    setup_docker_resources "$RESOURCE_PROFILE"
fi

# Load secrets from .env file
load_secrets

# Setup secrets for Act
SECRETS_FILE=$(setup_act_secrets)

# Get platform-specific options
PLATFORM_OPTIONS=$(get_platform_options)

# Show platform detection info
PLATFORM=$(detect_platform)
case $PLATFORM in
    "macos-arm64")
        print_status "Detected Apple Silicon (M-series) Mac"
        print_warning "Using linux/amd64 container architecture and disabled Docker socket mounting for compatibility"
        ;;
    "macos-x86_64")
        print_status "Detected Intel Mac"
        print_warning "Using linux/amd64 container architecture and disabled Docker socket mounting for compatibility"
        ;;
    "linux")
        print_status "Detected Linux system"
        ;;
esac

# Build Act command
ACT_CMD="act $EVENT_TYPE"

if [ ! -z "$WORKFLOW_FILE" ] && [ "$WORKFLOW_FILE" != "all" ]; then
    ACT_CMD="$ACT_CMD --workflows $WORKFLOW_FILE"
fi

if [ ! -z "$SECRETS_FILE" ] && [ -f "$SECRETS_FILE" ]; then
    ACT_CMD="$ACT_CMD --secret-file $SECRETS_FILE"
fi

if [ ! -z "$PLATFORM_OPTIONS" ]; then
    ACT_CMD="$ACT_CMD $PLATFORM_OPTIONS"
fi

# Add platform mapping for self-hosted runners to simulate EC2 environment
ACT_CMD="$ACT_CMD -P self-hosted=node:22"

# Add AI configuration environment variables from .env file
if [ ! -z "$LM_STUDIO_BASE_URL" ]; then
    ACT_CMD="$ACT_CMD --env LM_STUDIO_BASE_URL=$LM_STUDIO_BASE_URL"
fi
if [ ! -z "$LM_STUDIO_MODEL" ]; then
    ACT_CMD="$ACT_CMD --env LM_STUDIO_MODEL=$LM_STUDIO_MODEL"
fi
if [ ! -z "$OPENAI_API_KEY" ]; then
    ACT_CMD="$ACT_CMD --env OPENAI_API_KEY=$OPENAI_API_KEY"
fi
if [ ! -z "$GEMINI_API_KEY" ]; then
    ACT_CMD="$ACT_CMD --env GEMINI_API_KEY=$GEMINI_API_KEY"
fi
if [ ! -z "$OLLAMA_BASE_URL" ]; then
    ACT_CMD="$ACT_CMD --env OLLAMA_BASE_URL=$OLLAMA_BASE_URL"
fi
if [ ! -z "$OLLAMA_MODEL" ]; then
    ACT_CMD="$ACT_CMD --env OLLAMA_MODEL=$OLLAMA_MODEL"
fi
if [ ! -z "$DEBUG" ]; then
    ACT_CMD="$ACT_CMD --env DEBUG=$DEBUG"
fi
if [ ! -z "$ENABLE_STREAMING" ]; then
    ACT_CMD="$ACT_CMD --env ENABLE_STREAMING=$ENABLE_STREAMING"
fi

if [ "$VERBOSE" = true ]; then
    ACT_CMD="$ACT_CMD --verbose"
fi

# Show what will be executed
print_status "Executing: $ACT_CMD"

if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN MODE - No actual execution"
    echo "Command that would be run:"
    echo "$ACT_CMD"
    exit 0
fi

# Execute Act
print_status "Running GitHub Actions workflow locally..."
echo ""

# Run the command
eval $ACT_CMD

# Cleanup
if [ ! -z "$SECRETS_FILE" ] && [ -f "$SECRETS_FILE" ]; then
    rm -f "$SECRETS_FILE"
fi

print_success "Pipeline execution completed!"
