#!/usr/bin/env bash
# Fetch live Jira story and prepare for Copilot pipeline
# Usage: .github/scripts/fetch-and-run.sh <ISSUE_KEY> <JIRA_BROWSE_URL>
#
# Prerequisites:
#   - JIRA_API_TOKEN environment variable set (Jira Cloud PAT or Server/DC token)
#   - docsync installed (pip install -e .)
#
# Example:
#   export JIRA_API_TOKEN="your-token"
#   .github/scripts/fetch-and-run.sh EPMCDMETST-55568 "https://jira.company.com/browse/EPMCDMETST-55568"
#   # Then in Copilot Chat: /run-pipeline EPMCDMETST-55568

set -euo pipefail

ISSUE_KEY="${1:-}"
JIRA_URL="${2:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}�����  $*${NC}"; }
log_success() { echo -e "${GREEN}��� $*${NC}"; }
log_warn() { echo -e "${YELLOW}������  $*${NC}"; }
log_error() { echo -e "${RED}��� $*${NC}"; }

# Validate inputs
if [[ -z "$ISSUE_KEY" || -z "$JIRA_URL" ]]; then
    log_error "Missing arguments"
    echo "Usage: $0 <ISSUE_KEY> <JIRA_BROWSE_URL>"
    echo "Example: $0 EPMCDMETST-55568 \"https://jira.company.com/browse/EPMCDMETST-55568\""
    exit 1
fi

# Validate JIRA_API_TOKEN
if [[ -z "${JIRA_API_TOKEN:-}" ]]; then
    log_error "JIRA_API_TOKEN environment variable not set"
    echo ""
    echo "Set it first:"
    echo "  export JIRA_API_TOKEN=\"your-personal-access-token\""
    echo ""
    echo "For Jira Cloud (atlassian.net): Create PAT at https://id.atlassian.com/manage-profile/security/api-tokens"
    echo "For Jira Server/Data Center: Use your personal access token"
    exit 1
fi

# Validate URL format
if [[ ! "$JIRA_URL" =~ ^https?:// ]]; then
    log_error "JIRA_URL must be a full URL starting with http:// or https://"
    exit 1
fi

if [[ ! "$JIRA_URL" =~ /browse/ ]]; then
    log_warn "URL doesn't contain '/browse/' — assuming it's a browse URL anyway"
fi

log_info "Fetching $ISSUE_KEY from $JIRA_URL"

# Run docsync to fetch and generate artifacts (including user-story.md)
# --non-interactive ensures no prompts block CI/automation
if docsync "$JIRA_URL" --jira-token "$JIRA_API_TOKEN" -o . --non-interactive; then
    log_success "Story fetched and artifacts generated"

    # Verify user-story.md was created/updated
    if [[ -f "user-story.md" ]]; then
        log_success "user-story.md updated with live Jira data"
        echo ""
        echo "���� Next step in Copilot Chat:"
        echo "   /run-pipeline $ISSUE_KEY"
    else
        log_warn "user-story.md not found — check output directory"
    fi
else
    log_error "Failed to fetch story from Jira"
    echo ""
    echo "Common issues:"
    echo "  - Invalid JIRA_API_TOKEN (expired or wrong permissions)"
    echo "  - JIRA_URL not accessible (VPN, firewall, wrong host)"
    echo "  - Issue key doesn't exist or you lack permission"
    echo "  - Network timeout (try increasing timeout in jira_connector.py)"
    exit 1
fi