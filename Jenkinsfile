pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', url: 'https://github.com/Liam301020/house-price-predictor-devops.git'
      }
    }

    stage('Build (create venv & install deps)') {
      steps {
        sh '''
          python3 -m venv .venv
          .venv/bin/python -m pip install --upgrade pip
          .venv/bin/pip install --no-cache-dir -r requirements.txt
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          mkdir -p reports
          PYTHONPATH=. .venv/bin/pytest --maxfail=1 --disable-warnings -q --junitxml=reports/junit.xml
        '''
      }
    }

    stage('Code Quality (Bandit)') {
      steps {
        sh '''
          mkdir -p reports
          .venv/bin/bandit -r src -f txt -o reports/bandit.txt || true
        '''
      }
    }

    stage('Security (pip-audit)') {
      steps {
        sh '''
          mkdir -p reports
          .venv/bin/pip-audit -f json -o reports/pip-audit.json || true
        '''
      }
    }

    stage('Build Artefact (Docker)') {
      steps {
        sh '''
          docker build -t house-price-predictor:${BUILD_NUMBER} .
          docker images | head -n 10
        '''
      }
    }

    stage('Deploy (staging)') {
      steps {
        sh '''
          docker rm -f hp-stg || true
          docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}
        '''
      }
    }
  }

  post {
    always {
      junit 'reports/junit.xml'
      archiveArtifacts artifacts: 'reports/**', onlyIfSuccessful: false
    }
  }
}