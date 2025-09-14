pipeline {
  agent any
  environment {
    IMAGE = 'ghcr.io/ckrikas/api-service'
  }
  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Docker login') {
      steps {
        withEnv(["DOCKER_CONFIG=${env.WORKSPACE}/.docker"]) {
          withCredentials([string(credentialsId: 'ghcr_pat', variable: 'TOKEN')]) {
            sh '''
              set -eux
              mkdir -p "$DOCKER_CONFIG"
              docker logout ghcr.io || true
              echo "$TOKEN" | docker login ghcr.io -u ckrikas --password-stdin
              jq . "$DOCKER_CONFIG/config.json" || cat "$DOCKER_CONFIG/config.json" || true
            '''
          }
        }
      }
    }

    stage('Build') {
      steps {
        script { env.TAG = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim() }
        sh '''
          set -e
          docker build -t ${IMAGE}:${TAG} -t ${IMAGE}:latest .
        '''
      }
    }

    stage('Push') {
      steps {
        withEnv(["DOCKER_CONFIG=${env.WORKSPACE}/.docker"]) {
          sh '''
            set -eux
            docker push ${IMAGE}:${TAG}
            # "best effort" for latest; don’t fail the build if GHCR rejects it
            docker push ${IMAGE}:latest || echo "WARN: latest push failed; continuing"
          '''
        }
      }
    }

    stage('Trigger deploy') {
      when { expression { currentBuild.currentResult == 'SUCCESS' } }
      steps { build job: 'deploy-prod', wait: false }
    }
  }

  post {
    always { sh 'docker logout ghcr.io || true' }
  }
}
