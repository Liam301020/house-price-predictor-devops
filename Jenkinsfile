// Jenkinsfile (Scripted Pipeline) — Local Code Quality (pylint + radon + xenon)

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

    stage('Build (venv & deps)') {
      sh '''
        set -eux
        python3 -m venv .venv
        .venv/bin/python -m pip install --upgrade pip
        .venv/bin/pip install --no-cache-dir -r requirements.txt

        # Local code-quality toolchain
        .venv/bin/pip install --no-cache-dir pylint radon xenon
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

    // Local Code Quality
    stage('Code Quality (pylint / radon / xenon)') {
      sh '''
        set -eux
        mkdir -p reports

        # 1) pylint: check code style + smells
        .venv/bin/pylint src --fail-under=8.0 | tee reports/pylint.txt

        # 2) duplication only (report only, không fail pipeline)
        .venv/bin/pylint src --disable=all --enable=R0801 | tee reports/duplication.txt || true

        # 3) complexity reports
        .venv/bin/radon cc src -s -a | tee reports/radon-cc.txt
        .venv/bin/radon mi src -s    | tee reports/radon-mi.txt

        # 4) xenon: enforce complexity (nới ngưỡng để tránh fail quá sớm)
        #    Nếu muốn chỉ báo cáo, thêm "|| true"
        .venv/bin/xenon src --max-absolute C --max-modules B --max-average B || true
      '''
    }

    // Security lint (Bandit)
    stage('Code Quality (Bandit)') {
      sh '''
        set -eux
        .venv/bin/bandit -r src -f txt -o bandit.txt || true
      '''
    }

    // Dependency Security (pip-audit)
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

    // Deploy to staging
    stage('Deploy (staging)') {
      sh '''
        set -eux
        docker rm -f hp-stg || true
        docker run -d --name hp-stg -p 8081:8501 house-price-predictor:${BUILD_NUMBER}
      '''
    }

    // Release to Docker Hub
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

    // Monitoring: health + logs
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

    // Alerting (basic)
    stage('Alerting (basic)') {
      sh '''
        set -eux
        status=$(docker inspect -f "{{.State.Health.Status}}" hp-stg || echo "unknown")
        if [ "$status" != "healthy" ]; then
          echo "ALERT: hp-stg is not healthy (status=$status)" | tee reports/alert.txt
          exit 1
        else
          echo "hp-stg healthy — no alert." | tee reports/alert.txt
        fi
      '''
    }

    // Publish reports
    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,security-review.txt,junit.xml,coverage.xml,reports/**', onlyIfSuccessful: false
    }
  }
}