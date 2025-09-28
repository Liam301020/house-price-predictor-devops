// Jenkinsfile (Scripted Pipeline) — matches table: pytest, Bandit, pip-audit, SonarQube (stub)

node {
  def DOCKER_REPO = 'liamnguyen301020/house-price-predictor'

  timestamps {

    // 1) Checkout
    stage('Checkout') {
      deleteDir()
      sh '''
        set -eux
        git --version
        git clone --depth 1 https://github.com/Liam301020/house-price-predictor-devops.git .
        git log -1 --oneline
      '''
    }

    // 2) Build venv & install deps
    stage('Build (venv & deps)') {
      sh '''
        set -eux
        python3 -m venv .venv
        .venv/bin/python -m pip install --upgrade pip
        .venv/bin/pip install --no-cache-dir -r requirements.txt
      '''
    }

    // 3) Tests (pytest + coverage -> JUnit + coverage.xml)
    stage('Test') {
      sh '''
        set -eux
        PYTHONPATH=. .venv/bin/pytest \
          --maxfail=1 --disable-warnings -q \
          --junitxml=junit.xml \
          --cov=src --cov-report=xml:coverage.xml
      '''
    }

    // 4) Code Quality (SonarQube - stub only, not running scanner)
    stage('Code Quality (SonarQube - STUB)') {
      sh '''
        set -eux
        echo "[SonarQube STUB] Code quality analysis would run here in a full setup."
        echo "[SonarQube STUB] Skipped due to env constraints (permissions/arch/credentials)."
      '''
    }

    // 5) Security lint (Bandit)
    stage('Code Quality (Bandit)') {
      sh '''
        set -eux
        .venv/bin/bandit -r src -f txt -o bandit.txt || true
      '''
    }

    // 6) Dependency Security (pip-audit)
    stage('Security (pip-audit)') {
      sh '''
        set -eux
        .venv/bin/pip-audit -f json -o pip-audit.json || true
        echo "[INFO] Review pip-audit.json and document issues (severity, fix)" > security-review.txt
      '''
    }

    // 7) Build Docker artifact
    stage('Build Artifact (Docker)') {
      sh """
        set -eux
        docker build -t house-price-predictor:${BUILD_NUMBER} .
        docker images | head -n 10
      """
    }

    // 8) Deploy to local staging
    stage('Deploy (staging)') {
      sh '''
        set -eux
        docker rm -f hp-stg || true
        docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}
      '''
    }

    // 9) Release to Docker Hub
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

    // 10) Monitoring: container health + logs
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

    // 11) Alerting (stub)
    stage('Alerting (Stub)') {
      sh 'echo "[Alerting] If hp-stg crashes, notify team via Slack/Email (simulated)" > reports/alert.txt'
    }

    // 12) Publish reports
    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,security-review.txt,junit.xml,coverage.xml,reports/**', onlyIfSuccessful: false
    }
  }
}