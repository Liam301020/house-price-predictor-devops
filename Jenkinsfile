// Jenkinsfile (Scripted Pipeline)

node {
  // ---- Cấu hình (sửa repo Docker Hub nếu cần) ----
  def DOCKER_REPO = 'liamnguyen/house-price-predictor' 
  // -------------------------------------------------

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

    stage('Code Quality (Bandit)') {
      sh '.venv/bin/bandit -r src -f txt -o bandit.txt || true'
    }

    stage('Security (pip-audit)') {
      sh '.venv/bin/pip-audit -f json -o pip-audit.json || true'
    }

    stage('Build Artefact (Docker))') {
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
          # Nếu bạn không set sẵn DOCKER_REPO ở trên, mặc định dùng namespace theo username
          REPO="${DOCKER_REPO}"
          if [ -z "\${REPO}" ]; then REPO="\${DOCKER_USER}/house-price-predictor"; fi

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
      // In macOS + Docker Desktop: host.docker.internal
      def url = 'http://host.docker.internal:8081'
      retry(5) {
        sleep 6
        sh "curl -fsSL --max-time 5 ${url} >/dev/null"
      }
      sh '''
        set -eux
        mkdir -p reports
        docker logs hp-stg --since 2m > reports/app-logs.txt || true
      '''
    }

    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,junit.xml,reports/**', onlyIfSuccessful: false
    }
  }
}