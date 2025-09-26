pipeline {
  agent any

  stages {
    stage('Build') {
      steps {
        echo 'Installing dependencies with pip3...'
        sh 'python3 --version && pip3 --version'
        sh 'pip3 install --no-cache-dir -r requirements.txt'
      }
    }

    stage('Test') {
      steps {
        echo 'Running pytest...'
        sh 'PYTHONPATH=. pytest --maxfail=1 --disable-warnings -q'
      }
    }
  }
}