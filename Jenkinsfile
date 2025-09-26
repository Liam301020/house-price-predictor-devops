pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build (create venv & install deps)') {
      steps {
        sh 'python3 -m venv .venv'
        sh '.venv/bin/python -m pip install --upgrade pip'
        sh '.venv/bin/pip install --no-cache-dir -r requirements.txt'
      }
    }

    stage('Test') {
      steps {
        sh 'PYTHONPATH=. .venv/bin/pytest --maxfail=1 --disable-warnings -q --junitxml=junit.xml'
      }
    }

    stage('Code Quality (Bandit)') {
      steps {
        sh '.venv/bin/bandit -r src -f txt -o bandit.txt || true'
      }
    }

    stage('Security (pip-audit)') {
      steps {
        sh '.venv/bin/pip-audit -f json -o pip-audit.json || true'
      }
    }

    stage('Build Artefact (Docker)') {
      steps {
        sh 'docker build -t house-price-predictor:${BUILD_NUMBER} .'
        sh 'docker images | head -n 10'
      }
    }

    stage('Deploy (staging)') {
      steps {
        sh 'docker rm -f hp-stg || true'
        sh 'docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}'
      }
    }
  }

  post {
    always {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,junit.xml', onlyIfSuccessful: false
    }
  }
}