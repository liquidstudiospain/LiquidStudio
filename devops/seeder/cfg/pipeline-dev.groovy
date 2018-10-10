node {
	stage('Pre Configuration') {
		sh "git config --global http.sslVerify false && " +
		   "git config --global user.email \"jenkins@repsol.com\" && " +
		   "git config --global user.name \"Jenkins\" && " +
		   "git config --global core.quotePath false"

		echo "INFO: Merge request ${env.gitlabMergeRequestTitle} from " +
			 "${env.gitlabSourceBranch} to ${env.gitlabTargetBranch}"

		sh 'git clean -fxd -e "selenium/allure-results" || echo "Nothing to clean"'

		if (! fileExists(".git")){
			repositoryCloned = true;
			git credentialsId: env.SSH_GITLAB, url: "${env.gitlabSourceRepoSshUrl}"
		} else {
			repositoryCloned = false;
		}

		PRIVATE_TOKEN = get_token(env.PRIVATE_TOKEN)
	}
	stage('Configuration') {
		parallel('Download DevOps Artifacts' : {
			get_artifacts()
			generateDescribe(env.SFDC_CREDENTIALS, env.SFDC_SANDBOX)
		}, 'Update Repository' : {
			if (!repositoryCloned) {
				git credentialsId: env.SSH_GITLAB, url: "${env.gitlabSourceRepoSshUrl}"
			}
		})
	}
	stage('Starting Build') {
		updateGitlabStatus('running')
		postToGitlab("### Starting Build [${env.BUILD_DISPLAY_NAME}](${env.RUN_DISPLAY_URL})")
		validateBranchName(env.gitlabSourceBranch, env.SOURCE_TARGET_PATTERN)
	}
	stage('Building Up Delta Package') {
		def statusCode = sh returnStatus: true, script: "dist/merger/merger.exe merge_delta -s ${env.gitlabSourceBranch} -t ${env.gitlabTargetBranch} -nf"
		echo "INFO: Build Delta returned status code: ${statusCode}"
		handleDeltaStatus(statusCode)
	}
	stage('Test') {
		if (delta_built) {
			parallel('Integration Tests' : {
				stage('Running Validation') {
					def testMR = getTestMR()

					def codeValidate = post2sf('validate', env.SFDC_CREDENTIALS, env.SFDC_SANDBOX, 'srcToDeploy', testMR)
					handleValidationErrors('Validation', codeValidate)  // does not return if error
					editLastGitlabComment("+ Validation to **${env.PROJECT_CODE}** Succeded")
				}
			}, 'SonarQube Analysis' : {
				stage('SonarQube Analysis') {
					try {
						echo 'INFO: Running SonarQube Analysis to whole Project'
						def scannerHome = tool name: 'Repsol Sonar Scanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
						def jobName = env.JOB_NAME.replace('/', '_')
						def salesforceUrl = env.SFDC_SANDBOX.toBoolean()? 'https://test.salesforce.com' : 'https://login.salesforce.com'
						withCredentials([usernamePassword(credentialsId: env.SFDC_CREDENTIALS, usernameVariable: 'SFDC_USN', passwordVariable: 'SFDC_PWD')]) {
							withAnt(installation: 'Ant Installation') { withSonarQubeEnv {
								sh "ant -f /var/jenkins_home/salesforce/codescaner/antbuild.xml sonar " +
									"-Dsonar.projectKey=${jobName} "  +
									"-Dsonar.projectName=${jobName} " +
									"-Dsonar.projectVersion=1.0 " +
									"-Dsonar.sources='src' "
							}}
						}
					} catch (error) {
						// editLastGitlabComment("**SonarQube Analysis failed**")
						// updateGitlabStatus('failed')
						// error 'FATAL: SonarQube Analysis failed'
					}
				}
			})
		} else {
			echo 'WARNING: No changes detected in src folder, omitting tests'
		}
	}
	stage('Deploy Delta Package') {
		if (delta_built) {
			def codeDeploy = post2sf('deploy', env.SFDC_CREDENTIALS, env.SFDC_SANDBOX, 'srcToDeploy', '')
			handleValidationErrors('Deployment', codeDeploy)   // does not return if error
			editLastGitlabComment("+ Package Deployed to ${env.PROJECT_CODE}")
		} else {
			echo 'WARNING: No changes detected in src folder, omitting deploy'
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
						echo 'WARNING: Build is unstable'
						editLastGitlabComment('+ Build is unstable')
						updateGitlabStatus('failed')
					} else {
						editLastGitlabComment('+ Navigation Tests passed')
					}
				}
			} catch (error) {
				editLastGitlabComment('+ Exception at Navigation Tests')
			}
		} else {
			echo 'INFO: Directory selenium not exist, the test will not execute'
			editLastGitlabComment('+ Directory selenium does not exist, omitting selenium tests')
		}
	}
	stage('Post Build Steps') {
		if (currentBuild.currentResult == Result.SUCCESS.toString()) {
			updateGitlabStatus('success')
		} else {
			updateGitlabStatus('failed')
		}
		def result_string = "**Jenkins Build ${env.BUILD_DISPLAY_NAME} finished ${currentBuild.currentResult}**"
		editLastGitlabCommentMultiComment(get_ending_comment_part(result_string))
	}
}

def get_artifacts() {
	// def server = Artifactory.server('Arti')
	// def downloadSpec = """{
	//  "files": [
	//   {
	// 	  "pattern": "salesforce/devops_dist/dist_${DEVOPS_TAG}.zip",
	// 	  "target": "build"
	// 	}
	//  ]
	// }"""
	// server.download(downloadSpec)
	// sh 'unzip -q build/devops_dist && mv dist_* dist'
    sh(script: "wget -q https://gitlab.com/api/v4/projects/4358969/jobs/artifacts/${env.DEVOPS_TAG}/download?job=build " +
               "--header=Private-Token:${PRIVATE_TOKEN} -O build.zip > /dev/null")
    sh(script: 'unzip build.zip > /dev/null && mv dist_* dist')
}

def handleDeltaStatus(statusCode) {
	def message
    delta_built = false
	switch(statusCode) {
		case 0:
			echo 'INFO: Delta package build correclty'
			delta_built = true
			file = createDeltaArtifacts()
			message = "+ Delta Package Built Successfully [Delta Package](${env.BUILD_URL}" +
					  "artifact/${file}.html)"
			editLastGitlabComment(message)
			break
		case 11:
			echo 'WARNING: Delta package build with warnings'
			delta_built = true
			file = createDeltaArtifacts()
			message = "+ Delta Package Built With Warnings (Unknown Folders), please notify " +
					  "the RM [Delta Package](${env.BUILD_URL}artifact/artifacts_folder/${file}.html)"
			editLastGitlabComment(message)
			break
		case 123:
			updateGitlabStatus('failed')
			editLastGitlabComment('**ERROR! Could not find remote/source branch, ABORTING**')
			error 'ERROR: Could not find remote/source branch, exiting...' // aka raise exception
			break
		case 2:
			updateGitlabStatus('failed')
			currentBuild.result = 'ABORTED'
			echo 'WARNING: Branches up to date, could not build delta package'
			editLastGitlabComment('+ Delta Package was not built, not validating')
			addGitLabMRComment comment: 'WARNING! Delta Package not built'
			break
		case 3:
			updateGitlabStatus('failed')
			currentBuild.result = 'ABORTED'
			editLastGitlabComment('**ERROR! Merge Conflicts found, ABORTING**')
			error 'FATAL: Merge Conflicts found'
			break
		case 4:
			echo 'WARNING: No changes detected in src folder'
			editLastGitlabComment('+ Delta Package was not built, not validating')
			break
		default:
			updateGitlabStatus('failed')
			editLastGitlabComment('**ERROR! Unhandled Error, ABORTING**')
			error 'FATAL: Unhandled Errors...'
	}
}

def handleValidationErrors(postType, postStatusCode){
	echo "INFO: ${postType} returned status code: ${postStatusCode}"
	switch(postStatusCode) {
		case 0:
			break;
		case 4:
			echo 'ERROR: Could not find ant migration tool library'
			editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** Please contact your Release Manager")
			updateGitlabStatus('failed')
			error 'ERROR: Could not find ant migration tool library'
		case 5:
			archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts_folder/validate_log.txt', fingerprint: true
			editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** [${postType} Log](${env.BUILD_URL}artifact/artifacts_folder/validate_log.txt)")
			updateGitlabStatus('failed')
			error "ERROR: ${postType} Failed"
		case 6:
			archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts_folder/validate_log.txt', fingerprint: true
			editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed due to Code Coverage"+
								  "** [${postType} Log](${env.BUILD_URL}artifact/artifacts_folder/validate_log.txt)")
			updateGitlabStatus('failed')
			error "ERROR: ${postType} Failed due to not enough Code Coverage"
		case 7:
			archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts_folder/validate_log.txt', fingerprint: true
			editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed due to Test Failures** [${postType} Log]" +
								  "(${env.BUILD_URL}artifact/artifacts_folder/validate_log.txt)")
			updateGitlabStatus('failed')
			error "ERROR: ${postType} Failed due to Test Failures"
		case 8:
			echo "ERROR: Could not find credentials for ${env.PROJECT_CODE}"
			editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** Please contact your Release Manager")
			updateGitlabStatus('failed')
			error 'ERROR: Credentials not found'
		default:
			echo 'ERROR: Unhandled Error'
			editLastGitlabComment("**${postType} to ${env.PROJECT_CODE} Failed** Please contact your Release Manager")
			updateGitlabStatus('failed')
			error 'ERROR: Unhandled Error'
	}
}

def getTestMR(){
	def statusCode = sh (script: "dist/callgitlab/call_gitlab.exe description --no-ssl --force-https -t ${PRIVATE_TOKEN}", returnStatus: true)
	if (statusCode != 0){
		error 'ERROR: Could not retrieve tests from from Merge Request Description'
	}
	return sh(returnStdout: true, script: "cat ${env.BUILD_ID}-description.txt").trim()
}

def get_ending_comment_part(result_comment) {
	def build_link = "+ **[Build Status](${env.RUN_DISPLAY_URL})**"
	def sonar_link = "+ **[Sonarqube Results](https://ccq.rg.repsol.com/dashboard?id=" + env.JOB_NAME.replace('/', '_') + ")**"
	return [result_comment, build_link, sonar_link]
}

def createDeltaArtifacts() {
	def date = sh (script: 'date "+%y%m%d_%H%M"', returnStdout: true).trim()
	def source = sh(script: "echo ${env.gitlabSourceBranch} | tr '/' '-'", returnStdout: true).trim()
	def target = sh(script: "echo ${env.gitlabTargetBranch} | tr '/' '-'", returnStdout: true).trim()
	def path = "${source}-${target}"
	def file = "${date}__${path}"
	dir('artifacts_folder') {
		sh "zip -r ${file}.zip ../srcToDeploy"
		sh "mv output.txt ${file}.txt && mv mergerReport.html ${file}.html"
		archiveArtifacts allowEmptyArchive: true, artifacts: "${file}.*", fingerprint: true
	}
	return file
}

def post2sf(postType, targetCredentials, isSandbox, folder, testToRun){
	def statusCode = -1
	withCredentials([usernamePassword(credentialsId: targetCredentials, usernameVariable: 'SFDC_USN', passwordVariable: 'SFDC_PWD')]) {
		withAnt(installation: 'Ant Installation') {
			// withEnv(["ANT_OPTS=-Dhttps.proxyHost=proxymadrid.rm.gr.repsolypf.com -Dhttp.proxyHost=proxymadrid.rm.gr.repsolypf.com -Dhttp.proxyPort=8080"]) {
				def sandboxString = env.SFDC_SANDBOX.toBoolean()? '-sa' : ''
				def testString = !testToRun? '--test-level NoTestRun' : "-tl RunSpecifiedTests -tr ${testToRun}"
				statusCode = sh(script: "dist/migrationtool/post2sf.exe ${postType} -u ${SFDC_USN} -p '${SFDC_PWD}' ${sandboxString} " +
										"-f ${folder} ${testString}", returnStatus: true)
			// }
		}
	}
	return statusCode
}

def generateDescribe(targetCredentials, isSandbox){
	def statusCode = -1
	def sandboxString = env.SFDC_SANDBOX.toBoolean()? ' -sa ' : ''
	withCredentials([usernamePassword(credentialsId: targetCredentials, usernameVariable: 'SFDC_USN', passwordVariable: 'SFDC_PWD')]) {
		withAnt(installation: 'Ant Installation') {
			// withEnv(["ANT_OPTS=-Dhttps.proxyHost=proxymadrid.rm.gr.repsolypf.com -Dhttp.proxyHost=proxymadrid.rm.gr.repsolypf.com -Dhttp.proxyPort=8080"]) {
				statusCode = sh(script: "dist/migrationtool/post2sf.exe describe -u ${SFDC_USN} -p '${SFDC_PWD}' ${sandboxString}",
							 returnStatus: true)
			// }
		}
	}
	if(statusCode != 0){
		error 'FATAL: Cannot create describe log. ABORTING'
	}
	return statusCode
}

def postToGitlab(message) {
	sh (script: "dist/callgitlab/call_gitlab.exe comment --no-ssl --force-https -t ${PRIVATE_TOKEN} -m \"${message}\"", returnStatus: true)
}

def editLastGitlabComment(message) {
	sh (script: "dist/callgitlab/call_gitlab.exe comment --no-ssl --force-https -t ${PRIVATE_TOKEN} -m \"${message}\" -e", returnStatus: true)
}

def editLastGitlabCommentMultiComment(messages) {
	def messagesString = ''
	for (message in messages) {
		messagesString += "\"${message}\" "
	}
	sh (script: "dist/callgitlab/call_gitlab.exe comment --no-ssl --force-https -t ${PRIVATE_TOKEN} -m ${messagesString} -e", returnStatus: true)
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

def validateBranchName(branchName, targetPattern) {
	echo "INFO: Validating Branch ${branchName}"
    if (targetPattern != null) {
        if (!(branchName ==~ targetPattern)) {
            //sendEmail('branch_name', env.gitlabUserEmail, env.RECIPIENTS_RELEASE_MANAGERS)
            updateGitlabStatus('failed')
            editLastGitlabComment("**ERROR! Source branch does not follow the naming convention, ABORTING**")
			error 'FATAL: Branch name not supported'
		}
    }
}


def updateGitlabStatus(status) {
	sh(script: "dist/callgitlab/call_gitlab.exe status --no-ssl --force-https -t ${PRIVATE_TOKEN} -s ${status}", returnStatus: true)
}

def get_token(privateTokenCredential) {
	try {
		def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
			com.cloudbees.plugins.credentials.Credentials.class, Jenkins.instance, null, null);
		def PRIVATE_TOKEN = creds.find{ it.id == "${privateTokenCredential}" }
		return PRIVATE_TOKEN.apiToken
	} catch (org.jenkinsci.plugins.scriptsecurity.sandbox.RejectedAccessException e1) {
		echo 'WARNING: Exception Launched, returning hardcoded token'
		return 'N7MsnE8Y_kLfaSJ6UTW4'
	}
}
