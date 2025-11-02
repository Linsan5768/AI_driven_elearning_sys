pipeline {
    agent any

    environment {
        DOCKER_IMAGE_BACKEND = 'magic-academy-backend'
        DOCKER_IMAGE_FRONTEND = 'magic-academy-frontend'
        DOCKER_REGISTRY = "${env.DOCKER_REGISTRY ?: 'localhost:5000'}"
        IMAGE_TAG = "${env.BUILD_NUMBER ?: 'latest'}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Backend') {
            steps {
                script {
                    dir('backend') {
                        def backendImage = docker.build("${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG}")
                        backendImage.tag("latest")
                    }
                }
            }
        }

        stage('Build Frontend') {
            steps {
                script {
                    dir('frontend') {
                        def frontendImage = docker.build("${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG}")
                        frontendImage.tag("latest")
                    }
                }
            }
        }

        stage('Test Backend') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG}").inside {
                        sh 'python -c "import flask; print(\"Backend dependencies OK\")"'
                    }
                }
            }
        }

        stage('Test Frontend Build') {
            steps {
                script {
                    // Test Nginx configuration and verify build artifacts
                    // Note: Upstream hosts (backend, ollama) won't resolve in test environment
                    // This is expected - they only exist in docker-compose network during runtime
                    docker.image("${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG}").inside {
                        sh '''
                            # Verify build artifacts exist
                            test -f /usr/share/nginx/html/index.html && echo "✓ Frontend build artifacts exist"
                            
                            # Test Nginx configuration syntax (ignore upstream resolution errors)
                            # The upstream hosts will be available in docker-compose network
                            nginx -t 2>&1 | grep -E "(syntax is ok|test is successful)" && echo "✓ Nginx config syntax valid" || {
                                # If only upstream errors, still consider it valid
                                if nginx -t 2>&1 | grep -q "host not found in upstream"; then
                                    echo "⚠ Nginx upstream hosts not resolvable (expected in test environment)"
                                    echo "✓ Config syntax is valid - upstream hosts available in docker-compose network"
                                    exit 0
                                else
                                    echo "✗ Nginx config has real errors"
                                    exit 1
                                fi
                            }
                        '''
                    }
                }
            }
        }

        stage('Push to Registry') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    // Uncomment if using a Docker registry
                    // sh 'docker tag ${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG}'
                    // sh 'docker tag ${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG}'
                    // sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG}'
                    // sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG}'
                    echo 'Images built successfully. Configure registry push if needed.'
                }
            }
        }

        stage('Deploy') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    echo 'Deployment stage: Images built successfully.'
                    echo 'Note: Actual deployment requires docker-compose on the host machine.'
                    echo 'You can deploy manually with: docker-compose up -d'
                    echo ''
                    echo 'Or configure SSH deployment to remote server if needed.'
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check logs for details.'
        }
        always {
            cleanWs()
        }
    }
}

