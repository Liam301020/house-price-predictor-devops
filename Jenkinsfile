// Jenkinsfile (Scripted Pipeline)

node {
  timestamps {
    stage('Checkout') {
      deleteDir() // dọn sạch workspace
      sh '''
        set -eux
        git --version
        git clone --depth 1 https://github.com/Liam301020/house-price-predictor-devops.git .
        git log -1 --oneline
      '''
    }

    stage('Build (create venv & install deps)') {
      sh '''
        set -eux
        python3 -m venv .venv
        .venv/bin/python -m pip install --upgrade pip
        .venv/bin/pip install --no-cache-dir -r requirements.txt
      '''
    }

    stage('Test') {
      sh 'PYTHONPATH=. .venv/bin/pytest --maxfail=1 --disable-warnings -q --junitxml=junit.xml'
    }

    stage('Code Quality (Bandit)') {
      sh '.venv/bin/bandit -r src -f txt -o bandit.txt || true'
    }

    stage('Security (pip-audit)') {
      sh '.venv/bin/pip-audit -f json -o pip-audit.json || true'
    }

    stage('Build Artefact (Docker)') {
      sh '''
        set -eux
        docker build -t house-price-predictor:${BUILD_NUMBER} .
        docker images | head -n 10
      '''
    }

    stage('Deploy (staging)') {
      sh '''
        set -eux
        docker rm -f hp-stg || true
        docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}
      '''
    }

    // post
    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,junit.xml', onlyIfSuccessful: false
    }
  }
}