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
                        sh 'docker build -t ${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG} -t ${DOCKER_IMAGE_BACKEND}:latest .'
                    }
                }
            }
        }

        stage('Build Frontend') {
            steps {
                script {
                    dir('frontend') {
                        sh 'docker build -t ${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG} -t ${DOCKER_IMAGE_FRONTEND}:latest .'
                    }
                }
            }
        }

        stage('Test Backend') {
            steps {
                script {
                    sh '''
                        docker run --rm ${DOCKER_IMAGE_BACKEND}:${IMAGE_TAG} python -c "import flask; print('Backend dependencies OK')"
                    '''
                }
            }
        }

        stage('Test Frontend Build') {
            steps {
                script {
                    sh '''
                        docker run --rm ${DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG} nginx -t
                    '''
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
                    sh '''
                        # Stop existing containers
                        docker-compose down || true
                        
                        # Start new containers
                        docker-compose up -d
                        
                        # Wait for services to be healthy
                        sleep 10
                        
                        # Verify backend is responding
                        curl -f http://localhost:8001/api/game-state || exit 1
                        
                        # Verify frontend is responding
                        curl -f http://localhost/ || exit 1
                    '''
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

