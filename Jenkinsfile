// Jenkins Pipeline - Linux Agent
// 需安装插件: Allure Jenkins Plugin, HTML Publisher, Pipeline, Git Plugin,
//            Email Extension, Credentials Binding, Build Timeout

pipeline {
    agent { label 'linux-ui' }

    parameters {
        choice(
            name: 'ENV',
            choices: ['test', 'staging', 'production'],
            description: '目标测试环境'
        )
        string(
            name: 'PYTEST_MARKS',
            defaultValue: '',
            description: '运行指定标记的用例，如 smoke（为空则运行全部）'
        )
        string(
            name: 'PYTEST_KEYWORD',
            defaultValue: '',
            description: '运行名称包含关键字的用例，如 login（为空则运行全部）'
        )
        booleanParam(
            name: 'NOTIFY',
            defaultValue: true,
            description: '是否发送通知'
        )
    }

    environment {
        ENV           = "${params.ENV}"
        TEST_USERNAME = credentials('ui-test-username')
        TEST_PASSWORD = credentials('ui-test-password')
        ALLURE_CMD    = 'allure'
        DINGTALK_URL  = credentials('dingtalk-webhook-url')
        FEISHU_URL    = credentials('feishu-webhook-url')
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {

        stage('环境准备') {
            steps {
                echo "=== 环境: ${params.ENV} | 构建号: ${BUILD_NUMBER} ==="

                sh '''
                    python3 -m pip install --upgrade pip --quiet
                    pip install -r requirements-ci.txt --quiet
                '''

                sh 'playwright install chromium'
                sh 'playwright install-deps chromium'

                sh 'allure --version'
            }
        }

        stage('执行测试') {
            steps {
                script {
                    def extraArgs = ''
                    if (params.PYTEST_MARKS?.trim()) {
                        extraArgs += " -m ${params.PYTEST_MARKS}"
                    }
                    if (params.PYTEST_KEYWORD?.trim()) {
                        extraArgs += " -k ${params.PYTEST_KEYWORD}"
                    }
                    sh "python3 ci_run.py ${extraArgs}"
                }
            }
            post {
                always {
                    echo '测试执行完毕，进入归档阶段'
                }
            }
        }

        stage('归档报告') {
            steps {
                // Allure 报告（需安装 Allure Jenkins Plugin）
                allure([
                    includeProperties: false,
                    jdk              : '',
                    properties       : [],
                    reportBuildPolicy: 'ALWAYS',
                    results          : [[path: 'report/allure_results']]
                ])

                // pytest-HTML 报告
                publishHTML(target: [
                    allowMissing         : true,
                    alwaysLinkToLastBuild: true,
                    keepAll              : true,
                    reportDir            : 'report/html',
                    reportFiles          : 'report.html',
                    reportName           : 'pytest-HTML报告',
                    reportTitles         : ''
                ])

                // 失败截图 + 日志
                archiveArtifacts(
                    artifacts        : 'screenshots/**/*.png, logs/**/*.log',
                    allowEmptyArchive: true,
                    fingerprint      : false
                )
            }
        }
    }

    post {
        always {
            script {
                if (params.NOTIFY) {
                    def status   = currentBuild.currentResult
                    def emoji    = status == 'SUCCESS' ? '✅' : '❌'
                    def duration = currentBuild.durationString

                    // 钉钉通知
                    def dingMsg = """{
                      "msgtype": "markdown",
                      "markdown": {
                        "title": "UI自动化测试报告",
                        "text": "## ${emoji} UI自动化测试完成\\n\\n- **环境**: ${params.ENV}\\n- **状态**: ${status}\\n- **耗时**: ${duration}\\n- **构建号**: #${BUILD_NUMBER}\\n- **报告**: [查看Allure报告](${BUILD_URL}allure)\\n- **详情**: [构建日志](${BUILD_URL}console)"
                      }
                    }"""
                    sh "curl -s -X POST '${DINGTALK_URL}' -H 'Content-Type: application/json' -d '${dingMsg}' || true"

                    // 飞书通知
                    def feishuMsg = """{
                      "msg_type": "interactive",
                      "card": {
                        "header": {
                          "title": {"tag": "plain_text", "content": "${emoji} UI自动化测试 - ${status}"},
                          "template": "${status == 'SUCCESS' ? 'green' : 'red'}"
                        },
                        "elements": [{
                          "tag": "div",
                          "text": {
                            "tag": "lark_md",
                            "content": "**环境**: ${params.ENV}\\n**状态**: ${status}\\n**耗时**: ${duration}\\n**构建**: #${BUILD_NUMBER}\\n[查看报告](${BUILD_URL}allure)"
                          }
                        }]
                      }
                    }"""
                    sh "curl -s -X POST '${FEISHU_URL}' -H 'Content-Type: application/json' -d '${feishuMsg}' || true"
                }
            }
        }
        failure {
            emailext(
                subject : "[FAILED] UI自动化测试失败 - ${params.ENV} #${BUILD_NUMBER}",
                body    : """
                    <h3>UI自动化测试失败</h3>
                    <p><b>环境:</b> ${params.ENV}</p>
                    <p><b>构建号:</b> #${BUILD_NUMBER}</p>
                    <p><b>耗时:</b> ${currentBuild.durationString}</p>
                    <p><a href="${BUILD_URL}allure">查看 Allure 报告</a></p>
                    <p><a href="${BUILD_URL}console">查看构建日志</a></p>
                """,
                to      : '${DEFAULT_RECIPIENTS}',
                mimeType: 'text/html'
            )
        }
    }
}
