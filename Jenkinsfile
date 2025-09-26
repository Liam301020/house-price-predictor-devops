// Jenkinsfile (Scripted Pipeline)

node {
  def DOCKER_REPO = 'liamnguyen301020/house-price-predictor'

  timestamps {
    // ... (Checkout, Build, Test, Bandit, pip-audit)

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

    stage('Archive Reports') {
      junit 'junit.xml'
      archiveArtifacts artifacts: 'bandit.txt,pip-audit.json,junit.xml,reports/**', onlyIfSuccessful: false
    }
  }
}