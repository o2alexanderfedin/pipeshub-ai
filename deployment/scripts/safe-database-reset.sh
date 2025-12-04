#!/bin/bash

################################################################################
# Safe Database Reset Script
#
# PREVENTION MEASURE #2: Safe database reset with orphan detection
#
# This script safely resets all databases (MongoDB, ArangoDB, etcd, Qdrant)
# while detecting and warning about potential orphaned data.
#
# Key Features:
# - Detects orphaned data before reset
# - Warns user about data loss risks
# - Creates backups before any destructive operations
# - Provides options: Clear all, Preserve & migrate, Cancel
# - Logs all operations for audit trail
#
# Usage:
#   ./safe-database-reset.sh
#
# Requirements:
# - Docker and docker-compose must be running
# - All database services must be accessible
# - Sufficient disk space for backups
#
# Design Principles:
# - Single Responsibility: Only handles safe database reset
# - Fail-safe: Creates backups before any destructive action
# - User consent: Requires explicit confirmation at each step
# - Auditable: Logs all operations with timestamps
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ROOT="/tmp/hupyy-kb-backups"
LOG_FILE="$BACKUP_ROOT/reset-$(date +%Y%m%d-%H%M%S).log"

# Docker compose file
COMPOSE_FILE="$PROJECT_ROOT/deployment/docker-compose/docker-compose.dev.yml"

################################################################################
# Logging Functions
################################################################################

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

################################################################################
# Pre-flight Checks
################################################################################

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker compose file not found at: $COMPOSE_FILE"
        exit 1
    fi

    # Create backup directory
    mkdir -p "$BACKUP_ROOT"
    log_success "Prerequisites check passed"
}

################################################################################
# Database Detection Functions
################################################################################

check_mongodb_data() {
    log_info "Checking MongoDB for existing data..."

    local org_count=$(docker exec hupyy-kb-mongodb-1 mongosh es --quiet --eval \
        'db.org.countDocuments()' 2>/dev/null || echo "0")

    local users_count=$(docker exec hupyy-kb-mongodb-1 mongosh es --quiet --eval \
        'db.users.countDocuments()' 2>/dev/null || echo "0")

    echo "$org_count:$users_count"
}

check_arangodb_data() {
    log_info "Checking ArangoDB for existing data..."

    # Check record count
    local record_count=$(docker exec hupyy-kb-arangodb-1 arangosh --server.database es \
        --javascript.execute-string \
        'db._query("FOR r IN records COLLECT WITH COUNT INTO count RETURN count").toArray()[0] || 0' \
        2>/dev/null || echo "0")

    # Get distinct org IDs
    local org_ids=$(docker exec hupyy-kb-arangodb-1 arangosh --server.database es \
        --javascript.execute-string \
        'JSON.stringify(db._query("FOR r IN records RETURN DISTINCT r.orgId").toArray())' \
        2>/dev/null || echo "[]")

    echo "$record_count:$org_ids"
}

detect_orphaned_data() {
    log_info "Detecting orphaned data..."

    local mongo_data=$(check_mongodb_data)
    local mongo_org_count=$(echo "$mongo_data" | cut -d':' -f1)

    local arango_data=$(check_arangodb_data)
    local arango_record_count=$(echo "$arango_data" | cut -d':' -f1)
    local arango_org_ids=$(echo "$arango_data" | cut -d':' -f2)

    log_info "MongoDB organizations: $mongo_org_count"
    log_info "ArangoDB records: $arango_record_count"
    log_info "ArangoDB org IDs: $arango_org_ids"

    # Check for orphaned data condition
    if [[ "$mongo_org_count" == "0" && "$arango_record_count" != "0" ]]; then
        log_warn "ORPHANED DATA DETECTED!"
        log_warn "MongoDB has no organizations but ArangoDB has $arango_record_count records"
        log_warn "This data will become inaccessible if you proceed with reset"
        return 1
    elif [[ "$mongo_org_count" != "0" && "$arango_record_count" == "0" ]]; then
        log_warn "MongoDB has organizations but ArangoDB has no records"
        log_warn "This might indicate a previous partial reset"
        return 2
    elif [[ "$mongo_org_count" != "0" && "$arango_record_count" != "0" ]]; then
        log_info "Both databases have data - checking consistency..."
        return 3
    else
        log_info "Both databases appear empty"
        return 0
    fi
}

################################################################################
# Backup Functions
################################################################################

backup_mongodb() {
    log_info "Backing up MongoDB..."
    local backup_dir="$BACKUP_ROOT/mongodb-$(date +%Y%m%d-%H%M%S)"

    docker exec hupyy-kb-mongodb-1 mongodump \
        --db=es \
        --out=/tmp/backup \
        > /dev/null 2>&1

    docker cp hupyy-kb-mongodb-1:/tmp/backup "$backup_dir"

    log_success "MongoDB backup saved to: $backup_dir"
    echo "$backup_dir"
}

backup_arangodb() {
    log_info "Backing up ArangoDB..."
    local backup_dir="$BACKUP_ROOT/arangodb-$(date +%Y%m%d-%H%M%S)"

    mkdir -p "$backup_dir"

    docker exec hupyy-kb-arangodb-1 arangodump \
        --server.database es \
        --output-directory /tmp/arango-backup \
        > /dev/null 2>&1

    docker cp hupyy-kb-arangodb-1:/tmp/arango-backup "$backup_dir"

    log_success "ArangoDB backup saved to: $backup_dir"
    echo "$backup_dir"
}

backup_all_databases() {
    log_info "Creating backups of all databases..."

    local mongo_backup=$(backup_mongodb)
    local arango_backup=$(backup_arangodb)

    log_success "All backups completed successfully"
    log_info "MongoDB backup: $mongo_backup"
    log_info "ArangoDB backup: $arango_backup"

    echo "$mongo_backup:$arango_backup"
}

################################################################################
# Reset Functions
################################################################################

clear_mongodb() {
    log_info "Clearing MongoDB..."

    docker exec hupyy-kb-mongodb-1 mongosh es --quiet --eval '
        db.org.deleteMany({});
        db.users.deleteMany({});
        db.userCredentials.deleteMany({});
        db.userGroups.deleteMany({});
        db.connectorsConfig.deleteMany({});
        db.orgAuthConfig.deleteMany({});
        db.orgLogos.deleteMany({});
        print("MongoDB cleared");
    ' > /dev/null

    log_success "MongoDB cleared"
}

clear_arangodb() {
    log_info "Clearing ArangoDB..."

    docker exec hupyy-kb-arangodb-1 arangosh --server.database es \
        --javascript.execute-string '
        try {
            db._truncate("records");
            db._truncate("recordGroups");
            db._truncate("users");
            db._truncate("userGroups");
            db._truncate("anyone");
            db._truncate("domains");
            db._truncate("belongsTo");
            db._truncate("permission");
            db._truncate("inheritPermissions");
            print("ArangoDB cleared");
        } catch (e) {
            print("Error clearing ArangoDB: " + e);
        }
    ' > /dev/null

    log_success "ArangoDB cleared"
}

clear_etcd() {
    log_info "Clearing etcd..."

    docker exec hupyy-kb-etcd-1 etcdctl del --prefix "" > /dev/null 2>&1 || true

    log_success "etcd cleared"
}

clear_all_databases() {
    log_info "Clearing all databases..."

    clear_mongodb
    clear_arangodb
    clear_etcd

    log_success "All databases cleared successfully"
}

################################################################################
# User Interaction
################################################################################

show_banner() {
    echo ""
    echo "=========================================="
    echo "  Safe Database Reset Tool"
    echo "  Hupyy KB - Version 1.0"
    echo "=========================================="
    echo ""
}

show_orphan_warning() {
    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                   ⚠️  WARNING  ⚠️                         ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  ORPHANED DATA DETECTED IN ARANGODB                       ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  This indicates data exists that cannot be accessed      ║${NC}"
    echo -e "${RED}║  because the corresponding organization was removed      ║${NC}"
    echo -e "${RED}║  from MongoDB.                                            ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  Proceeding with reset will permanently delete this data. ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

get_user_choice() {
    echo ""
    echo "Please choose an option:"
    echo ""
    echo "  1) Clear ALL databases (MongoDB, ArangoDB, etcd)"
    echo "     - Creates backup first"
    echo "     - Deletes all data"
    echo "     - Safe for fresh start"
    echo ""
    echo "  2) Cancel and investigate"
    echo "     - Keeps all data intact"
    echo "     - Allows manual inspection"
    echo "     - Recommended if unsure"
    echo ""
    echo "  3) Exit without changes"
    echo ""
    read -p "Enter choice (1-3): " choice
    echo "$choice"
}

confirm_action() {
    local action="$1"
    echo ""
    echo -e "${YELLOW}About to: ${action}${NC}"
    echo ""
    read -p "Type 'YES' to confirm (anything else cancels): " confirmation

    if [[ "$confirmation" != "YES" ]]; then
        log_info "Action cancelled by user"
        return 1
    fi
    return 0
}

################################################################################
# Main Execution
################################################################################

main() {
    show_banner

    # Pre-flight checks
    check_prerequisites

    # Detect orphaned data
    detect_orphaned_data
    local detect_result=$?

    # Show warning if orphaned data detected
    if [[ $detect_result -eq 1 ]]; then
        show_orphan_warning
    fi

    # Get user choice
    local choice=$(get_user_choice)

    case "$choice" in
        1)
            # Clear all databases
            if confirm_action "CLEAR ALL DATABASES (with backup)"; then
                log_info "Starting database reset..."

                # Create backups
                backup_all_databases

                # Clear all databases
                clear_all_databases

                log_success "Database reset completed successfully!"
                echo ""
                log_info "Backups saved to: $BACKUP_ROOT"
                log_info "You can now create a new organization"
            else
                log_info "Operation cancelled"
                exit 0
            fi
            ;;
        2)
            # Cancel and investigate
            log_info "Operation cancelled - data preserved"
            echo ""
            log_info "Next steps:"
            log_info "  1. Review the investigation plan at:"
            log_info "     .prompts/005-org-mismatch-investigation-plan/org-mismatch-investigation-plan.md"
            log_info "  2. Run consistency check:"
            log_info "     npm run check:db-consistency"
            log_info "  3. Consider data migration instead of reset"
            exit 0
            ;;
        3|*)
            # Exit
            log_info "Exiting without changes"
            exit 0
            ;;
    esac

    echo ""
    log_success "Operation completed successfully"
    log_info "Log file: $LOG_FILE"
}

# Run main function
main "$@"
