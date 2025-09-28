// Jenkinsfile (Scripted Pipeline)

node {
  def DOCKER_REPO = 'liamnguyen301020/house-price-predictor'

  timestamps {
    stage('Checkout') {
      deleteDir()
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

// ---- Code Quality (SonarQube) ----
stage('Code Quality (SonarQube)') {
  steps {
    withCredentials([string(credentialsId: 'ef5f5354-9dd2-4fa1-a722-ec02bcf6b580', variable: 'SONAR_TOKEN')]) {
      sh '''
        sonar-scanner \
          -Dsonar.projectKey=house-price-predictor \
          -Dsonar.sources=. \
          -Dsonar.host.url=http://localhost:9000 \
          -Dsonar.login=$SONAR_TOKEN
      '''
    }
  }
}

// ---- Code Quality (Bandit) ----
stage('Code Quality (Bandit)') {
  steps {
    sh '.venv/bin/bandit -r src -f txt -o bandit.txt || true'
  }
}

    // ---- Security ----
    stage('Security (pip-audit)') {
      sh '''
        .venv/bin/pip-audit -f json -o pip-audit.json || true
        echo "[INFO] Review pip-audit.json and document issues (severity, fix)" > security-review.txt
      '''
    }

    stage('Build Artefact (Docker)') {
      sh """
        set -eux
        docker build -t house-price-predictor:${BUILD_NUMBER} .
        docker images | head -n 10
      """
    }

    stage('Deploy (staging)') {
      sh '''
        set -eux
        docker rm -f hp-stg || true
        docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}
      '''
    }

    stage('Release (Docker Hub)') {
      withCredentials([usernamePassword(
        credentialsId: 'dockerhub-creds',
        usernameVariable: 'DOCKER_USER',
        passwordVariable: 'DOCKER_PASS'
      )]) {
        sh """
          set -eux
          REPO="${DOCKER_REPO}"; [ -z "\${REPO}" ] && REPO="\${DOCKER_USER}/house-price-predictor"
          FULL_IMAGE="\${REPO}:${BUILD_NUMBER}"
          FULL_LATEST="\${REPO}:latest"

          echo "\${DOCKER_PASS}" | docker login -u "\${DOCKER_USER}" --password-stdin
          docker tag house-price-predictor:${BUILD_NUMBER} "\${FULL_IMAGE}"
          docker tag house-price-predictor:${BUILD_NUMBER} "\${FULL_LATEST}"
          docker push "\${FULL_IMAGE}"
          docker push "\${FULL_LATEST}"
          docker logout || true
        """
      }
    }

    stage('Monitoring (health-check)') {
      sh '''
        set -eux
        for i in $(seq 1 20); do
          st=$(docker inspect -f "{{.State.Health.Status}}" hp-stg || echo "starting")
          echo "hp-stg health: $st"
          [ "$st" = "healthy" ] && break
          sleep 3
        done

        mkdir -p reports
        docker logs hp-stg --since 2m > reports/app-logs.txt || true
      '''
    }

    // ---- Alerting Stub ----
    stage('Alerting (Stub)') {
      sh '''
        echo "[Alerting] If hp-stg crashes, notify team via Slack/Email (simulated)" > reports/alert.txt
      '''
    }

    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,sonar-report.txt,security-review.txt,junit.xml,reports/**', onlyIfSuccessful: false
    }
  }
}