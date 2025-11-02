# Jenkins with Docker Setup Guide

## Problem Solved

Jenkins container now has Docker CLI installed and can access the Docker socket.

## Custom Jenkins Image

We created a custom Jenkins image (`jenkins-with-docker`) that:
- Includes Docker CLI
- Automatically fixes Docker socket permissions on startup
- Can build and run Docker containers from Jenkins Pipeline

## Files Created

1. **Dockerfile.jenkins** - Custom Jenkins image with Docker CLI
2. **jenkins-entrypoint.sh** - Startup script that fixes Docker socket permissions

## Usage

### Build the Custom Jenkins Image

```bash
cd /path/to/demo
docker build -t jenkins-with-docker -f Dockerfile.jenkins .
```

### Start Jenkins Container

```bash
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins-with-docker:latest
```

### Verify Docker Access

```bash
# Check Docker is accessible from Jenkins
docker exec jenkins docker ps

# Check Docker version
docker exec jenkins docker --version
```

## Jenkinsfile Updates

The Jenkinsfile has been updated to use Docker Pipeline plugin syntax:
- `docker.build()` instead of `sh 'docker build'`
- `docker.image().inside {}` for running tests
- `image.tag()` for tagging

## Troubleshooting

If Docker commands fail in Jenkins:

```bash
# Check socket permissions
docker exec jenkins ls -la /var/run/docker.sock

# Restart Jenkins container
docker restart jenkins

# Check Jenkins logs
docker logs jenkins | tail -20
```

## Next Steps

1. Access Jenkins: http://localhost:8080
2. Your existing Pipeline configuration should work now
3. Run a build to verify Docker commands execute successfully

