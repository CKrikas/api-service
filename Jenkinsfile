pipeline {
  agent any
  environment {
    IMAGE = "ghcr.io/CKrikas/api-service"
  }
  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Unit tests') {
      when { expression { fileExists('package.json') || fileExists('pyproject.toml') } }
      steps {
        sh '''
          if [ -f package.json ]; then echo "TODO: pnpm test (skipping)"; fi
          if [ -f pyproject.toml ] || [ -f requirements.txt ]; then echo "TODO: pytest (skipping)"; fi
        '''
      }
    }

    stage('Build image') {
      steps { sh 'docker build -t $IMAGE:$GIT_COMMIT -t $IMAGE:latest .' }
    }

    stage('Login GHCR') {
      steps {
        withCredentials([string(credentialsId: 'ghcr-token', variable: 'TOKEN')]) {
          sh 'echo $TOKEN | docker login ghcr.io -u CKrikas --password-stdin'
        }
      }
    }

    stage('Push image') {
      steps {
        sh '''
          docker push $IMAGE:$GIT_COMMIT
          docker push $IMAGE:latest
        '''
      }
    }

    stage('Notify/Deploy trigger') {
      when { branch 'main' }
      steps {
        echo 'Images pushed. The infra pipeline (Ansible) will deploy.'
      }
    }
  }
  post { always { sh 'docker logout ghcr.io || true' } }
}
