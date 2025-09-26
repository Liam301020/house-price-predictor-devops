pipeline {
  agent any

  stages {
    stage('Build & Test (Python 3.11 container)') {
      agent {
        docker {
          image 'python:3.11-slim'   /
          args '-u root'            
        }
      }
      steps {
        sh 'python --version && pip --version'
        sh 'pip install --no-cache-dir -r requirements.txt'
        sh 'PYTHONPATH=. pytest --maxfail=1 --disable-warnings -q'
      }
    }
  }
}