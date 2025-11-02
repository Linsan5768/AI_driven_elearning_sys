#!/bin/bash
# migrate-to-volumes.sh - Migrate data from bind mounts to named volumes

set -e

echo "🔄 Stopping containers..."
docker-compose down

echo "📦 Creating volumes..."
docker volume create demo_backend_uploads 2>/dev/null || echo "Volume demo_backend_uploads already exists"
docker volume create demo_backend_courses 2>/dev/null || echo "Volume demo_backend_courses already exists"

echo "📋 Migrating uploads data..."
if [ -d "backend/uploads" ] && [ "$(ls -A backend/uploads 2>/dev/null)" ]; then
    docker run --rm \
        -v "$(pwd)/backend/uploads:/source:ro" \
        -v demo_backend_uploads:/destination \
        alpine sh -c "cp -r /source/. /destination/ && echo '✅ Uploads migrated successfully'"
    echo "   Files migrated: $(ls -1 backend/uploads | wc -l | tr -d ' ') files"
else
    echo "   ⚠️  No uploads to migrate (directory empty or missing)"
fi

echo "📋 Migrating courses data..."
if [ -d "backend/courses" ] && [ "$(ls -A backend/courses 2>/dev/null)" ]; then
    docker run --rm \
        -v "$(pwd)/backend/courses:/source:ro" \
        -v demo_backend_courses:/destination \
        alpine sh -c "cp -r /source/. /destination/ && echo '✅ Courses migrated successfully'"
    echo "   Files migrated: $(ls -1 backend/courses | wc -l | tr -d ' ') files"
else
    echo "   ⚠️  No courses to migrate (directory empty or missing)"
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "📝 Note: docker-compose.yml has been updated to use named volumes:"
echo "   - backend_uploads (maps to demo_backend_uploads)"
echo "   - backend_courses (maps to demo_backend_courses)"
echo ""
echo "⚠️  IMPORTANT: Before deleting local code, verify:"
echo "   1. Update docker-compose.yml volume names to match: backend_uploads and backend_courses"
echo "   2. Test that containers start correctly: docker-compose up -d"
echo "   3. Verify data is accessible: docker-compose exec backend ls -la /app/uploads"
echo ""
echo "🚀 Start containers with: docker-compose up -d"

