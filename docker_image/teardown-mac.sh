#!/bin/bash
set -e

echo "=========================================="
echo "Moodle Complete Teardown Script for Mac"
echo "=========================================="
echo ""
echo "This will remove:"
echo "  - All running containers"
echo "  - Docker volumes (including database data)"
echo "  - Docker images (my-moodle and my-moodle-db)"
echo "  - Networks"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Teardown cancelled."
    exit 0
fi

echo ""
echo "Starting teardown process..."

# Stop and remove containers with docker-compose
echo "Stopping and removing containers..."
docker-compose -f docker-compose-client.yml down -v 2>/dev/null || echo "No docker-compose setup found"

# Stop individual containers if they exist
echo "Ensuring containers are stopped..."
docker stop moodle moodle-db 2>/dev/null || true
# docker rm moodle moodle-db 2>/dev/null || true

# Remove the external volume
echo "Removing external volume..."
docker volume rm moodle_mariadb_data 2>/dev/null || echo "Volume moodle_mariadb_data not found"

# Remove any other moodle-related volumes
echo "Removing any other moodle volumes..."
docker volume ls | grep moodle | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true

# Remove Docker images
echo "Removing Docker images..."
# docker rmi my-moodle:installed 2>/dev/null || echo "Image my-moodle:installed not found"
# docker rmi my-moodle-db:installed 2>/dev/null || echo "Image my-moodle-db:installed not found"

# Remove any dangling images
echo "Removing dangling images..."
docker image prune -f

# Remove networks
echo "Removing networks..."
docker network rm moodle-network 2>/dev/null || echo "Network moodle-network not found"
docker network prune -f

# Clean up build cache (optional but recommended)
echo "Cleaning up build cache..."
docker builder prune -f

echo ""
echo "=========================================="
echo "Teardown Complete! ✨"
echo "=========================================="
echo ""
echo "Verification:"
echo ""

# Show remaining containers
echo "Remaining containers:"
docker ps -a | grep moodle || echo "  No moodle containers found ✓"
echo ""

# Show remaining volumes
echo "Remaining volumes:"
docker volume ls | grep moodle || echo "  No moodle volumes found ✓"
echo ""

# Show remaining images
echo "Remaining images:"
docker images | grep my-moodle || echo "  No moodle images found ✓"
echo ""

# Show disk space reclaimed
echo "Docker disk usage:"
docker system df
echo ""

echo "All Moodle components have been removed!"
echo ""
echo "Optional: To clean ALL unused Docker resources, run:"
echo "  docker system prune -a --volumes"
echo ""
