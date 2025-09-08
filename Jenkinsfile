pipeline {
  agent any
  environment {
    IMAGE = "ghcr.io/ckrikas/api-service"
  }
  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Docker login') {
      steps {
        withCredentials([string(credentialsId: 'ghcr-token', variable: 'TOKEN')]) {
          sh 'echo $TOKEN | docker login ghcr.io -u ckrikas --password-stdin'
        }
      }
    }

    stage('Build & Push (buildx)') {
      steps {
        sh '''
          set -e
          docker buildx create --use --name builder || true
          docker buildx build --platform linux/amd64 \
            -t ${IMAGE}:${GIT_COMMIT} -t ${IMAGE}:latest \
            --push .
        '''
      }
    }

    stage('Trigger deploy') {
      when { branch 'main' }
      steps { build job: 'deploy-prod', wait: false }
    }
  }
  post { always { sh 'docker logout ghcr.io || true' } }
}
