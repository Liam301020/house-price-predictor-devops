pipeline {
  agent any

  stages {
    stage('Build (create venv & install deps)') {
      steps {
        sh 'python3 -m venv .venv'
        sh '.venv/bin/python -m pip install --upgrade pip'
        sh '.venv/bin/pip install --no-cache-dir -r requirements.txt'
      }
    }

    stage('Test') {
      steps {
        sh 'PYTHONPATH=. .venv/bin/pytest --junitxml=reports/junit.xml --maxfail=1 --disable-warnings -q'
      }
      post {
        always {
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', fingerprint: true
        }
      }
    }

    stage('Code Quality (Bandit)') {
      steps {
        sh '.venv/bin/bandit -r src -f txt -o reports/bandit.txt || true'
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/bandit.txt', fingerprint: true
        }
      }
    }
    stage('Security (pip-audit)') {
        steps {
            sh '.venv/bin/pip-audit -r requirements.txt -f json -o reports/pip-audit.json || true'
        }
        post {
            always {
                archiveArtifacts artifacts: 'reports/pip-audit.json', fingerprint: true
            }
        }
    }
  }
}