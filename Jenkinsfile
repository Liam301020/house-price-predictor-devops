options { skipDefaultCheckout(true); timestamps() }  // để Jenkins không tự checkout

stage('Checkout') {
  steps {
    deleteDir()  // dọn sạch workspace cũ (xóa .git nếu còn)
    sh '''
      set -eux
      git --version
      git clone --depth 1 https://github.com/Liam301020/house-price-predictor-devops.git .
      git log -1 --oneline
    '''
  }
}