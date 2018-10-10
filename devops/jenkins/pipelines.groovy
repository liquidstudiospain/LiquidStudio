node {
	stage('Pre Configuration') {
		echo "Merge request ${env.gitlabMergeRequestTitle} from ${env.gitlabSourceBranch} to ${env.gitlabTargetBranch}"

		sh 'git clean -fxd -e "selenium/allure-results" || echo "Nothing to clean"'

	    if (! fileExists(".git")){
		    repositoryCloned = true;
		    git credentialsId: SSH_GITLAB, url: "${env.gitlabSourceRepoSshUrl}"
		} else {
		    repositoryCloned = false;
		}

		sh 'printenv'
	}
	stage('Configuration') {
		parallel('Download DevOps Artifacts' : {
            withCredentials([string(credentialsId: env.SEED_PRIVATE_TOKEN, variable: 'SEED_PRIVATE_TOKEN')]) {
			    sh(script: "wget -q https://gitlab.com/api/v4/projects/4358969/jobs/artifacts/${env.DEVOPS_TAG}/download?job=build " +
                           "--header=Private-Token:${SEED_PRIVATE_TOKEN} -O build.zip > /dev/null")
		    }
			sh(script: 'unzip build.zip > /dev/null && mv dist_* dist')
            generateDescribe(env.SFDC_CREDENTIALS, env.SFDC_SANDBOX)
		}, 'Download PMD' : {
			sh "wget -q https://github.com/pmd/pmd/releases/download/pmd_releases%2F${env.PMD_VERSION}/pmd-bin-${env.PMD_VERSION}.zip > /dev/null"
			sh(script: "unzip pmd-bin-${env.PMD_VERSION}.zip > /dev/null && mv pmd-bin-${env.PMD_VERSION} pmd")
		},  'Update Repository' : {
            if (!repositoryCloned) {
			    git credentialsId: SSH_GITLAB, url: "${env.gitlabSourceRepoSshUrl}"
            }
		})
	}
	stage('Starting Build') {
	    updateGitlabStatus('running')
		postToGitlab("### Starting Build ${env.BUILD_DISPLAY_NAME}")
		validateBranchName()
	}
	stage('Building Up Delta Package') {
		def statusCode = sh returnStatus: true, script: "dist/merger/merger.exe merge_delta -s ${env.gitlabSourceBranch} -t ${env.gitlabTargetBranch} -nf"
		echo "STATUS CODE: ${statusCode}"
        handleDeltaErrors(statusCode)
	}
	stage('Test') {
		if (delta_built) {
			parallel('Integration Tests' : {
				stage('Running Validation') {
					def codeValidate = post2sf('validate', env.SFDC_CREDENTIALS, env.SFDC_SANDBOX, 'srcToDeploy', 'NoTestRun')
					handleValidationErrors('Validation', codeValidate)  // does not return if error
					editLastGitlabComment("+ Validation to ${env.PROJECT_CODE} Succeded")
				}
			}, 'Code Quality Tests' : {
				stage('Running Code Quality Tests') {
					echo 'Running Code Quality Tests to whole Project'
					def cache_path = "${env.JENKINS_HOME}/${env.JOB_NAME}/pmd-cache"
					sh (script: 'pmd/bin/run.sh pmd -d src -R "dist/pmd/rules.xml" -f xml -r pmd.xml -failOnViolation false -cache \"${cache_path}\"')
					pmd canComputeNew: false, defaultEncoding: '', healthy: '', pattern: '', unHealthy: ''
					echo 'Running Code Quality Tests to Delta Package'
					sh (script: 'pmd/bin/run.sh pmd -d srcToDeploy -R "dist/pmd/rules.xml" -f xml -r pmddelta.xml -failOnViolation false')
				}
			})
		}
	}
	stage('Deploy Delta Package') {
        if (delta_built) {
            echo 'ALERT! DEPLOYING!!'
            def codeDeploy = post2sf('deploy', env.SFDC_CREDENTIALS, env.SFDC_SANDBOX, 'srcToDeploy', 'NoTestRun')
            handleValidationErrors('Deployment', codeDeploy)   // does not return if error
            editLastGitlabComment("+ Package Deployed to ${env.PROJECT_CODE}")
            sendEmailValidate('success', env.RECIPIENTS, env.RECIPIENTS_CC, "${file}.txt")
        } else {
			echo 'ALERT! Target Branch is not develop NOT DEPLOYING!!'
		}
	}
	stage('Navigation Tests') {
		if (fileExists("selenium/src")){
			try {
				dir('selenium') {
					editLastGitlabComment('+ Starting Navigation Tests')
					sh 'bash test_launcher.sh'
					allure includeProperties: false, jdk: '', results: [[path: 'selenium/src/allure-results']]
					//junit 'src/allure-results/test_result.xml' TODO check this
					if (currentBuild.currentResult == Result.UNSTABLE.toString()) {
					    echo '[WARNING] Build is unstable'
						editLastGitlabComment('+ Build is unstable')
					    updateGitlabStatus('failed')
                		sendEmail('selenium', env.RECIPIENTS_SELENIUM, env.RECIPIENTS_RELEASE_MANAGERS)
					} else {
						editLastGitlabComment('+ Navigation Tests passed')
					}
				}
			} catch (error) {
				sendEmail('selenium', env.RECIPIENTS_SELENIUM, env.RECIPIENTS_RELEASE_MANAGERS)
				editLastGitlabComment('+ Exception at Navigation Tests')
			}
		}else{
			echo '[JENKINS] Directory Selenium_Tests not exist, the test will not execute'
			editLastGitlabComment('+ Directory Selenium_Tests not exist, the test will not execute')
		}
	}
	stage('Accept Merge Request') {
	    if (currentBuild.currentResult == Result.SUCCESS.toString()) {
		    updateGitlabStatus('success')
		}
		def result_string = "**Jenkins Build ${env.BUILD_DISPLAY_NAME} finished ${currentBuild.currentResult}**"
		editLastGitlabCommentMultiComment(get_ending_comment_part(result_string))
		echo 'ALERT! NOT ACCEPTING MR'
		//acceptGitLabMR()
	}
}

def handleDeltaErrors(statusCode) {
    def message
    switch(statusCode) {
        case 0:
            echo '[INFO] Delta package build correclty'
            delta_built = true
            file = createDeltaArtifacts()
            message = "+ Delta Package Built Successfully [Delta Package](${env.BUILD_URL}" +
                      "artifact/artifacts_folder/${file}.html)"
            editLastGitlabComment(message)
            break
        case 11:
            echo '[WARNING] Delta package build with warnings'
            delta_built = true
            file = createDeltaArtifacts()
            message = "+ Delta Package Built With Warnings (Unknown Folders), please notify " +
                      "the RM [Delta Package](${env.BUILD_URL}artifact/artifacts_folder/${file}.html)"
            editLastGitlabComment(message)
            break
        case 123:
            updateGitlabStatus('failed')
            editLastGitlabComment('**ERROR! Could not find remote/source branch, ABORTING**')
            error 'ERROR! Could not find remote/source branch, exiting...' // aka raise exception
            break
        case 2:
            updateGitlabStatus('failed')
            currentBuild.result = 'ABORTED'
            echo '[WARNING] Branches up to date, could not build delta package'
            editLastGitlabComment('+ Delta Package was not built, not validating')
            addGitLabMRComment comment: 'WARNING! Delta Package not built'
            break
        case 3:
            updateGitlabStatus('failed')
            currentBuild.result = 'ABORTED'
            editLastGitlabComment('**ERROR! Merge Conflicts found, ABORTING**')
            error '[FATAL] Merge Conflicts found'
            break
        case 4:
            echo 'No changes detected in src folder'
            editLastGitlabComment('+ Delta Package was not built, not validating')
            delta_built = false
            break
        default:
            updateGitlabStatus('failed')
            editLastGitlabComment('**ERROR! Unhandled Error, ABORTING**')
            error '[FATAL] Unhandled Errors...'
    }
}

def handleValidationErrors(postType, postStatusCode){
    echo "STATUS CODE: ${postStatusCode}"
    switch(postStatusCode) {
        case 0:
            break;
        case 4:
            echo 'Could not find ant migration tool library'
            editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** Please contact your Release Manager")
            updateGitlabStatus('failed')
            error '[ERROR] Could not find ant migration tool library'
        case 5:
            sendEmailValidate('error', env.gitlabUserEmail, "${env.RECIPIENTS_CC} ${env.RECIPIENTS_RELEASE_MANAGERS}", 'errors.txt')
            archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts_folder/validate_log.txt', fingerprint: true
            editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** [${postType} Log](${env.BUILD_URL}artifact/artifacts_folder/validate_log.txt)")
            updateGitlabStatus('failed')
            error "[ERROR] ${postType} Failed"
        case 8:
            echo "Could not find credentials for ${env.PROJECT_CODE}"
            editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** Please contact your Release Manager")
            updateGitlabStatus('failed')
            error '[ERROR] Credentials not found'
        default:
            echo 'Unhandled Error'
            editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** Please contact your Release Manager")
            updateGitlabStatus('failed')
            error '[ERROR] Unhandled Error'
    }
}

def get_ending_comment_part(result_comment) {
    def build_link = "+ **[Build Status](${env.RUN_DISPLAY_URL})**"
    def pmd_link = "+ **[PMD Results](${env.BUILD_URL}pmdResult)**"
    def allure_link = "+ **[Allure Results](${env.BUILD_URL}'allure)**"
    return [result_comment, build_link, pmd_link, allure_link]
}

def createDeltaArtifacts() {
    def date = sh (script: 'date "+%y%m%d_%H%M"', returnStdout: true).trim()
    def source = sh(script: "echo ${env.gitlabSourceBranch} | tr '/' '-'", returnStdout: true).trim()
    def target = sh(script: "echo ${env.gitlabTargetBranch} | tr '/' '-'", returnStdout: true).trim()
    def path = "${source}-${target}"
    def file = "${date}__${path}"
    dir('artifacts_folder') {
        sh "zip -r ${file}.zip ../srcToDeploy"
        sh "tree ../srcToDeploy -o ${file}.txt && tree -H src --nolinks -C -T \"Deploy Delta\" ../srcToDeploy -o ${file}.html"
        archiveArtifacts allowEmptyArchive: true, artifacts: "${file}.*", fingerprint: true
    }
    return file
}

def post2sf(postType, targetCredentials, isSandbox, folder, testLevel){
    def statusCode = -1
    withCredentials([usernamePassword(credentialsId: targetCredentials, usernameVariable: 'SFDC_USN', passwordVariable: 'SFDC_PWD')]) {
        def sandboxString = env.SFDC_SANDBOX.toBoolean()? ' -sa ' : ''
        statusCode = sh(script: "dist/migrationtool/post2sf.exe ${postType} -u ${SFDC_USN} -p ${SFDC_PWD} ${sandboxString} " +
                                     "-f ${folder} -test ${testLevel}", returnStatus: true)
    }
    return statusCode
}

def generateDescribe(targetCredentials, isSandbox){
    def statusCode = -1
    def sandboxString = env.SFDC_SANDBOX.toBoolean()? ' -sa ' : ''
    withCredentials([usernamePassword(credentialsId: targetCredentials, usernameVariable: 'SFDC_USN', passwordVariable: 'SFDC_PWD')]) {
        statusCode = sh(script: "dist/migrationtool/post2sf.exe describe -u ${SFDC_USN} -p ${SFDC_PWD} ${sandboxString}",
                         returnStatus: true)
    }
    return statusCode
}

def postToGitlab(message) {
    withCredentials([string(credentialsId: env.PRIVATE_TOKEN, variable: 'PRIVATE_TOKEN')]) {
        sh (script: "dist/callgitlab/call_gitlab.exe comment -t ${PRIVATE_TOKEN} -m \"${message}\"", returnStatus: true)
    }
}

def editLastGitlabComment(message) {
    withCredentials([string(credentialsId: env.PRIVATE_TOKEN, variable: 'PRIVATE_TOKEN')]) {
        sh (script: "dist/callgitlab/call_gitlab.exe comment -t ${PRIVATE_TOKEN} -m \"${message}\" -e", returnStatus: true)
    }
}

def editLastGitlabCommentMultiComment(messages) {
    def messagesString = ''
    for (message in messages) {
        messagesString += "\"${message}\" "
    }
    withCredentials([string(credentialsId: env.PRIVATE_TOKEN, variable: 'PRIVATE_TOKEN')]) {
        sh (script: "dist/callgitlab/call_gitlab.exe comment -t ${PRIVATE_TOKEN} -m ${messagesString} -e", returnStatus: true)
    }
}

def sendEmail(emailType, recipient, recipientCc) {
    withCredentials([usernamePassword(credentialsId: env.EMAIL_CREDENTIALS, usernameVariable: 'USN', passwordVariable: 'PWD')]) {
        sh (script: "dist/sendemail/send_email.exe -u ${USN} -p ${PWD} -sa ${env.EMAIL_SERVER} ${emailType} -r ${recipient} " +
                    "-rCC ${recipientCc}", returnStatus: true)
    }
}

def sendEmailValidate(status, recipient, recipientCc, file_path) {
    withCredentials([usernamePassword(credentialsId: env.EMAIL_CREDENTIALS, usernameVariable: 'USN', passwordVariable: 'PWD')]) {
        sh (script: "dist/sendemail/send_email.exe -u ${USN} -p ${PWD} -sa ${env.EMAIL_SERVER} validate -r ${recipient} " +
                    "-rCC ${recipientCc} -f ${file_path} -s ${status}", returnStatus: true)
    }
}

def validateBranchName() {
    def statusCode = sh(returnStatus: true, script: "dist/misc/validate_branch_name.sh ${env.gitlabSourceBranch}")
    echo "STATUS CODE: ${statusCode}"
    if(statusCode == 1){
        sendEmail('branch_name', env.gitlabUserEmail, env.RECIPIENTS_RELEASE_MANAGERS)
        updateGitlabStatus('failed')
        editLastGitlabComment("**ERROR! Source branch does not follow the naming convention, ABORTING**")
        error 'FATAL! Branch name not supported'
    }
}

def updateGitlabStatus(status) {
    withCredentials([string(credentialsId: env.PRIVATE_TOKEN, variable: 'PRIVATE_TOKEN')]) {
        sh(script: "dist/callgitlab/call_gitlab.exe status -t ${PRIVATE_TOKEN} -s ${status}", returnStatus: true)
    }
}
