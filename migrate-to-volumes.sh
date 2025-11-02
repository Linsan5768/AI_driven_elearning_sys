#!/bin/bash
# migrate-to-volumes.sh - Migrate data from bind mounts to named volumes

set -e

echo "🔄 Stopping containers..."
docker-compose down

# Get the project name (directory name or from COMPOSE_PROJECT_NAME)
PROJECT_NAME=${COMPOSE_PROJECT_NAME:-$(basename $(pwd) | tr '[:upper:]' '[:lower:]' | tr -d ' ')}
VOLUME_UPLOADS="${PROJECT_NAME}_backend_uploads"
VOLUME_COURSES="${PROJECT_NAME}_backend_courses"

echo "📦 Creating volumes..."
# Docker Compose automatically prefixes volume names with project name
# Create volumes explicitly to ensure they exist before migration
docker volume create "${VOLUME_UPLOADS}" 2>/dev/null || echo "   Volume ${VOLUME_UPLOADS} already exists"
docker volume create "${VOLUME_COURSES}" 2>/dev/null || echo "   Volume ${VOLUME_COURSES} already exists"

echo ""
echo "📋 Migrating uploads data to volume: ${VOLUME_UPLOADS}..."
if [ -d "backend/uploads" ] && [ "$(ls -A backend/uploads 2>/dev/null)" ]; then
    docker run --rm \
        -v "$(pwd)/backend/uploads:/source:ro" \
        -v "${VOLUME_UPLOADS}:/destination" \
        alpine sh -c "cp -r /source/. /destination/ && echo '✅ Uploads migrated successfully'"
    FILE_COUNT=$(ls -1 backend/uploads 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✅ Migrated ${FILE_COUNT} files"
else
    echo "   ⚠️  No uploads to migrate (directory empty or missing)"
fi

echo ""
echo "📋 Migrating courses data to volume: ${VOLUME_COURSES}..."
if [ -d "backend/courses" ] && [ "$(ls -A backend/courses 2>/dev/null)" ]; then
    docker run --rm \
        -v "$(pwd)/backend/courses:/source:ro" \
        -v "${VOLUME_COURSES}:/destination" \
        alpine sh -c "cp -r /source/. /destination/ && echo '✅ Courses migrated successfully'"
    FILE_COUNT=$(ls -1 backend/courses 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✅ Migrated ${FILE_COUNT} files"
else
    echo "   ⚠️  No courses to migrate (directory empty or missing)"
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "📊 Verification:"
echo "   Checking volumes..."
docker volume inspect "${VOLUME_UPLOADS}" >/dev/null 2>&1 && echo "   ✅ ${VOLUME_UPLOADS} exists" || echo "   ❌ ${VOLUME_UPLOADS} missing"
docker volume inspect "${VOLUME_COURSES}" >/dev/null 2>&1 && echo "   ✅ ${VOLUME_COURSES} exists" || echo "   ❌ ${VOLUME_COURSES} missing"
echo ""
echo "📝 Note: docker-compose.yml has been updated to use named volumes."
echo "   Volume names (with project prefix):"
echo "   - ${VOLUME_UPLOADS}"
echo "   - ${VOLUME_COURSES}"
echo ""
echo "⚠️  IMPORTANT: Before deleting local code, verify:"
echo "   1. Test that containers start correctly: docker-compose up -d"
echo "   2. Verify data is accessible:"
echo "      docker-compose exec backend ls -la /app/uploads"
echo "      docker-compose exec backend ls -la /app/courses"
echo "   3. Test uploading a file and generating a course"
echo ""
echo "🚀 Start containers with: docker-compose up -d"

