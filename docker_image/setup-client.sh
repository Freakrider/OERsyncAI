#!/bin/bash
set -e

echo "Setting up Moodle with pre-installed database..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Clean up any existing setup
echo "Cleaning up any existing containers and volumes..."
sudo docker compose -f "$SCRIPT_DIR/docker-compose-client.yml" down -v 2>/dev/null || true
sudo docker volume rm moodle_mariadb_data 2>/dev/null || true

# Load Docker images
echo "Loading Docker images..."
sudo docker load -i "$SCRIPT_DIR/my-moodle.tar"
sudo docker load -i "$SCRIPT_DIR/my-moodle-db.tar"

# Create the volume
echo "Creating MariaDB volume..."
sudo docker volume create moodle_mariadb_data

# Extract database data BEFORE starting containers
echo "Restoring database data..."
sudo docker run --rm \
    -v moodle_mariadb_data:/var/lib/mysql \
    -v "$SCRIPT_DIR":/backup \
    alpine sh -c "tar -xzf /backup/mariadb-data.tar.gz -C /var/lib/ && chown -R 999:999 /var/lib/mysql"

# Verify extraction worked
echo "Verifying database files..."
sudo docker run --rm -v moodle_mariadb_data:/var/lib/mysql alpine sh -c "
    echo 'Files in /var/lib/mysql:' && ls -la /var/lib/mysql | head -20 && \
    echo '' && \
    echo 'Checking for moodle database:' && ls -la /var/lib/mysql/moodle 2>/dev/null | head -10 || echo 'ERROR: moodle database not found!'
"

# Check if moodle database exists
if ! sudo docker run --rm -v moodle_mariadb_data:/var/lib/mysql alpine test -d /var/lib/mysql/moodle; then
    echo "ERROR: Database restoration failed! The moodle database folder was not found."
    echo "Please check mariadb-data.tar.gz file."
    exit 1
fi

echo "Database files verified successfully!"

# Start services
echo "Starting Moodle services..."
sudo docker compose -f "$SCRIPT_DIR/docker-compose-client.yml" up -d

echo ""
echo "Waiting for services to start (30 seconds)..."
sleep 30

# Final verification
echo "Checking database tables..."
sudo docker exec moodle-db mysql -u root -prootpass moodle \
    -e "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'moodle';" 2>/dev/null \
    || echo "Warning: Could not verify tables"

echo ""
echo "Setup complete! Moodle should be available at http://localhost:8080"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: Admin123!"
echo ""
echo "Useful commands:"
echo "  sudo docker compose -f docker-compose-client.yml logs -f moodle"
echo "  sudo docker compose -f docker-compose-client.yml ps"
echo "  sudo docker compose -f docker-compose-client.yml down"
