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
        sh 'PYTHONPATH=. .venv/bin/pytest --maxfail=1 --disable-warnings -q'
      }
    }
  }
}