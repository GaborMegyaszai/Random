pipeline {
  agent {
    docker {
      image 'python:3'
      args '-u root --privileged'
    }
  }
  parameters {
    string(name: 'VNF_NAMES', description: 'Names of VNFs to be terminated separated by commas, e.g. vnf-1, vnf-2, vnf-3', defaultValue: "NTAS2-HELPALAB3")
  }
  environment {
    NTAS_BOT = credentials('ntasbot')
    CBIS_BOT = credentials('cbis-bot')
    CBAM_BOT = credentials('cbam-bot')
    DEPADMIN = credentials('depadmin')
    ARC_USER = credentials('nokia-arc')
    DEPADMIN_DEFAULT_PASSWORD = credentials('depadmin-default-pw')
    OS_USERNAME = "${CBIS_BOT_USR}"
    OS_PASSWORD = "${CBIS_BOT_PSW}"
    ARTIFACTORY_URL = "https://artifactory.elisa.eficode.io"
    ARTIFACTORY_PATH = "Nokia/NTAS"
    // TODO: Can these be read from VNFD?
    NTAS_IP = "10.64.160.148"
    NTAS_CONF_IP = "10.64.160.149"
  }
  stages {
    stage('Check prerequisites') {
      steps {
        dir('telco') {
          git url: 'https://github.com/eficode/telco.git'
          dir('nokia/cbamlibrary') {
            sh 'pip install -r requirements.txt'
          }
          dir('openstack_foundation/openstacklibrary') {
            sh 'pip install -r requirements.txt'
          }
        }
        git credentialsId: 'ntasbot', url: 'https://git.elisa.eficode.io/scm/entas/pipelines.git'
        sh 'pip install -r requirements.txt'
        script {
          VERSION_PATH = getPathOfLastModifiedVersion()
        }
        sh "apt-get update"
        sh "apt-get install -y sshpass expect"
      }
    }
    stage('Add files to version control') {
      when { triggeredBy 'ArtifactoryCause' }
      steps {
        script {
          artifactoryDownload("INSTALL_MEDIA/*.json")
          def diffCode = sh script: 'git diff artifactory-download --exit-code', returnStatus: true
          if (diffCode != 0) {
            sh 'git add artifactory-download'
            sh 'git -c user.name="Elisa Bot" -c user.email="test@example.com" commit -m "Add files from artifactory - ${VERSION_PATH}"'
            sh "git push https://${NTAS_BOT_USR}:${NTAS_BOT_PSW}@git.elisa.eficode.io/scm/entas/pipelines.git"
          } else {
            echo "No changes, skipping commit."
          }
        }
      }
    }

    stage('Redeploy') {
      steps {
        script {
          artifactoryDownload("INSTALL_MEDIA/*.zip")
          //artifactoryDownload("INSTALL_MEDIA/Nokia-NokiaTAS_mcs_5.11.14-20.2.zip")
        }
        sh "python redeployment.py '${params.VNF_NAMES}'"
        sh "mkdir /root/.ssh && chmod 0700 /root/.ssh"
        sh "ssh-keyscan -p 23 ${NTAS_IP} >> ~/.ssh/known_hosts"
        sh "./set_password.sh ${NTAS_IP} ${DEPADMIN_USR} ${DEPADMIN_DEFAULT_PASSWORD} '${DEPADMIN_PSW}'"
        sh "python add_permissions.py"
        rtDownload (
          serverId: 'elisa-artifactory',
          spec: """{
            "files": [
              {
                "pattern": "Nokia/utils/AvamarClient-linux-sles11-x86_64-7.4.101-58.rpm",
                "target": "./",
                "flat": "true"
              }
            ]
          }
          """
        )
        sh "sh avamar_upload.sh"
        sh "python configure_br.py"
        sh "python arc_restore.py"
      }
    }
  }
  post {
    always {
      restApiPublisher(customPrefix: '', customProjectName: 'NTAS-redeployment', jenkinsEnvParameterField: '', jenkinsEnvParameterTag: '')
    }
  }
}

def getPathOfLastModifiedVersion() {
  def response = httpRequest httpMode: 'GET',
    authentication: 'ntasbot',
    url: "${ARTIFACTORY_URL}/api/storage/${ARTIFACTORY_PATH}?lastModified",
    validResponseCodes: '200'
  def json = readJSON text: response.content
  return (json.uri =~ /${ARTIFACTORY_PATH}\/[^\/]*\/[^\/]*/)[0]
}

def artifactoryDownload(String... patterns) {
  def files = []
  patterns.each{ pattern ->
    files << """
    {
      "pattern": "${VERSION_PATH}/${pattern}",
      "target": "artifactory-download/",
      "flat": "true"
    }"""
  }
  rtDownload (
    serverId: 'elisa-artifactory',
    spec: """{
      "files": [
        ${files.join(",\n")}
      ]
    }
    """
  )
}
