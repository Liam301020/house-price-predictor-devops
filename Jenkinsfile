// Jenkinsfile (Scripted Pipeline)

node {
  def DOCKER_REPO = 'liamnguyen301020/house-price-predictor'

  timestamps {

    // NOTE: Put Jenkins & SonarQube onto the same user-defined Docker network.
    stage('Prepare Docker Network') {
      sh '''
        set -eux
        docker network create ci-net || true
        docker network connect ci-net sonarqube || true
        docker network connect ci-net jenkins   || true
      '''
    }

    stage('Checkout') {
      deleteDir()
      sh '''
        set -eux
        git --version
        git clone --depth 1 https://github.com/Liam301020/house-price-predictor-devops.git .
        git log -1 --oneline
      '''
    }

    stage('Build (venv & deps)') {
      sh '''
        set -eux
        python3 -m venv .venv
        .venv/bin/python -m pip install --upgrade pip
        .venv/bin/pip install --no-cache-dir -r requirements.txt
      '''
    }

    stage('Test') {
  sh '''
    set -eux
    PYTHONPATH=. .venv/bin/pytest \
      --maxfail=1 --disable-warnings -q \
      --junitxml=junit.xml \
      --cov=src --cov-report=xml:coverage.xml
  '''
}

    // NOTE: Self-test that the Sonar token stored in Jenkins credentials works against the SonarQube server.
    stage('Sonar token self-test') {
      withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
        sh '''
          set -eux
          docker run --rm --network ci-net curlimages/curl:8.10.1 \
            -s -u "${SONAR_TOKEN}:" http://sonarqube:9000/api/authentication/validate \
            | grep -q '"valid":true'
        '''
      }
    }

    // Code Quality: SonarQube (Dockerized sonar-scanner)
    stage('Code Quality (SonarQube)') {
  withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
    sh """
      set -eux

      # Bảo đảm thư mục làm việc có thể ghi (phòng hờ)
      mkdir -p .sonar || true
      chmod -R a+rwx .sonar || true

      docker run --rm \
        --user 0:0 \  # IMPORTANT: tránh lỗi AccessDenied khi tạo /usr/src/.sonar
        --network ci-net \
        -v "\$PWD:/usr/src" \
        -e SONAR_HOST_URL=http://sonarqube:9000 \
        sonarsource/sonar-scanner-cli:latest \
        sonar-scanner \
          -Dsonar.host.url=http://sonarqube:9000 \
          -Dsonar.login="${SONAR_TOKEN}" \
          -Dsonar.projectKey=house-price-predictor \
          -Dsonar.sources=/usr/src \
          -Dsonar.working.directory=/usr/src/.sonar \
          -Dsonar.python.version=3.11 \
          -Dsonar.python.coverage.reportPaths=/usr/src/coverage.xml
    """
  }
}

    // Code Quality: Bandit (security linter)
    stage('Code Quality (Bandit)') {
      sh '''
        set -eux
        .venv/bin/bandit -r src -f txt -o bandit.txt || true
      '''
    }

    // Dependency Security (SCA)
    stage('Security (pip-audit)') {
      sh '''
        set -eux
        .venv/bin/pip-audit -f json -o pip-audit.json || true
        echo "[INFO] Review pip-audit.json and document issues (severity, fix)" > security-review.txt
      '''
    }

    // Build Docker artifact
    stage('Build Artifact (Docker)') {
      sh """
        set -eux
        docker build -t house-price-predictor:${BUILD_NUMBER} .
        docker images | head -n 10
      """
    }

    // Deploy to a local staging container
    stage('Deploy (staging)') {
      sh '''
        set -eux
        docker rm -f hp-stg || true
        docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}
      '''
    }

    // Release: push to Docker Hub
    stage('Release (Docker Hub)') {
      withCredentials([usernamePassword(
        credentialsId: 'dockerhub-creds',
        usernameVariable: 'DOCKER_USER',
        passwordVariable: 'DOCKER_PASS'
      )]) {
        sh '''
          set -eux
          REPO="${DOCKER_USER}/house-price-predictor"
          [ -n "'${DOCKER_REPO}'" ] && REPO="'${DOCKER_REPO}'"

          FULL_IMAGE="${REPO}:${BUILD_NUMBER}"
          FULL_LATEST="${REPO}:latest"

          echo "${DOCKER_PASS}" | docker login -u "${DOCKER_USER}" --password-stdin
          docker tag house-price-predictor:${BUILD_NUMBER} "${FULL_IMAGE}"
          docker tag house-price-predictor:${BUILD_NUMBER} "${FULL_LATEST}"
          docker push "${FULL_IMAGE}"
          docker push "${FULL_LATEST}"
          docker logout || true
        '''
      }
    }

    // Monitoring: container health + logs
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

    // Alerting (stub) — replace with real Slack/email later
    stage('Alerting (Stub)') {
      sh 'echo "[Alerting] If hp-stg crashes, notify team via Slack/Email (simulated)" > reports/alert.txt'
    }

    // Publish reports
    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,security-review.txt,junit.xml,reports/**', onlyIfSuccessful: false
    }
  }
}