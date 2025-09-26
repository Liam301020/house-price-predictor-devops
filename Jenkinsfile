pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        echo 'Installing dependencies...'
        sh 'pip install --no-cache-dir -r requirements.txt'
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