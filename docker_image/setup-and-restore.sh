#!/bin/bash
set -euo pipefail
set -x

# Check if backup file path is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path-to-backup.mbz> [category-id] [shortname] [fullname]"
    echo ""
    echo "Example: $0 /path/to/backup-moodle2-course-8-newcourse-20251022-0949-nu.mbz 1 mycourse \"My Course\""
    echo ""
    echo "If category-id, shortname, and fullname are not provided, they will be auto-generated."
    exit 1
fi

BACKUP_FILE="$1"
CATEGORY_ID="${2:-1}" # Default to category 1 (Miscellaneous)
SHORTNAME="${3:-restored_$(date +%Y%m%d_%H%M%S)}" # Auto-generate if not provided
FULLNAME="${4:-Restored Course $(date +"%Y-%m-%d %H:%M:%S")}" # Auto-generate if not provided

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "============================================"
echo "Moodle Setup and Course Restore for Debian"
echo "============================================"
echo "Backup file: $BACKUP_FILE"
echo "Category ID: $CATEGORY_ID"
echo "Short name: $SHORTNAME"
echo "Full name: $FULLNAME"
echo "============================================"
echo "============================================"
echo ""

# Step 1: Run setup-client.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/setup-client.sh"

if [ -f "$SETUP_SCRIPT" ]; then
    "$SETUP_SCRIPT"
else
    echo "ERROR: setup-client.sh not found!"
    echo "Please ensure the setup script is in the same directory as restore_and_setup.sh."
    exit 1
fi
echo "Please ensure the setup script is in the same directory as restore_and_setup.sh."
    exit 1

# Wait a bit more to ensure everything is fully ready
echo ""
echo "Waiting additional 10 seconds for Moodle to be fully ready..."
sleep 10

# Step 2: Copy backup file to container
echo ""
echo "Step 2: Copying backup file to Moodle container..."
BACKUP_FILENAME=$(basename "$BACKUP_FILE")
docker cp "$BACKUP_FILE" moodle:/tmp/

# Fix permissions so www-data can read it
echo "Fixing file permissions..."
docker exec moodle chown www-data:www-data /tmp/"$BACKUP_FILENAME"
docker exec moodle chmod 644 /tmp/"$BACKUP_FILENAME"

# Verify the file was copied successfully and has correct permissions
echo "Verifying file copy and permissions..."
docker exec moodle ls -lh /tmp/"$BACKUP_FILENAME"

# Step 3: Restore the course
echo ""
echo "Step 3: Restoring course from backup..."
docker exec -u www-data moodle /usr/local/bin/php /var/www/html/admin/cli/restore_backup.php \
    --file="/tmp/$BACKUP_FILENAME" \
    --categoryid="$CATEGORY_ID" \
    --shortname="$SHORTNAME" \
    --fullname="$FULLNAME" \
    --showdebugging

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ Course restored successfully!"
    echo "============================================"
    echo "Course details:"
    echo "  Short name: $SHORTNAME"
    echo "  Full name: $FULLNAME"
    echo "  Category ID: $CATEGORY_ID"
    echo ""
    echo "Access Moodle at: http://localhost:8080"
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: Admin123!"
    echo "============================================"

    # Step 4: Clean up backup file from container
    echo ""
    echo "Cleaning up temporary files..."
    docker exec moodle rm "/tmp/$BACKUP_FILENAME"
else
    echo ""
    echo "============================================"
    echo "❌ ERROR: Course restore failed!"
    echo "============================================"
    echo "Check the output above for details."
    echo ""
    echo "You can manually retry with:"
    echo "docker exec -u www-data moodle /usr/local/bin/php /var/www/html/admin/cli/restore_backup.php \\"
    echo "  --file=/tmp/$BACKUP_FILENAME \\"
    echo "  --categoryid=$CATEGORY_ID \\"
    echo "  --shortname=\"$SHORTNAME\" \\"
    echo "  --fullname=\"$FULLNAME\" \\"
    echo "  --showdebugging"
    echo ""
    echo "Backup file left in container at: /tmp/$BACKUP_FILENAME"
    exit 1
fi
