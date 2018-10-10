node {
    if (env.DELTA_STRATEGY != 'Build Delta' && env.SOURCE_BRANCH != '') {
        error 'Can only provide SOURCE_BRANCH parameter in \'Build Delta\' stategy'
    }
    stage('Pre Configuration') {
        echo "INFO: ${env.DELTA_STRATEGY} between ${env.SOURCE_REFERENCE} and ${env.TARGET_REFERENCE}"

        sh "git config --global http.sslVerify false && " +
            "git config --global user.email \"jenkins@repsol.com\" && " +
            "git config --global user.name \"Jenkins\" && " +
            "git config --global core.quotePath false"

        sh 'git clean -fxd || echo "Nothing to clean"'

        if (! fileExists(".git")){
            repositoryCloned = true;
            git credentialsId: env.SSH_GITLAB, url: "${env.REPOSITORY_URL}"
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
                git credentialsId: env.SSH_GITLAB, url: "${env.REPOSITORY_URL}"
            }
        })
    }
    stage('Building Up Delta Package') {
        deltaStrategy = env.DELTA_STRATEGY == 'Build Delta' ? 'build_delta' : 'merge_delta'
        branchName = env.SOURCE_BRANCH? " -b ${env.SOURCE_BRANCH} " : ''
        def statusCode = sh (script: "dist/merger/merger.exe ${deltaStrategy} -s ${env.SOURCE_REFERENCE} -t ${env.TARGET_REFERENCE} ${branchName} -nf",
                             returnStatus: true)
        echo "INFO: Build Delta returned status code: ${statusCode}"
        handleDeltaStatus(statusCode)
    }
}

def get_token(privateTokenCredential) {
	try {
		def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
			com.cloudbees.plugins.credentials.Credentials.class, Jenkins.instance, null, null);
		def PRIVATE_TOKEN = creds.find{ it.id == "${privateTokenCredential}" }
		return PRIVATE_TOKEN.apiToken
	} catch (org.jenkinsci.plugins.scriptsecurity.sandbox.RejectedAccessException e1) {
		echo 'ERROR: Exception Launched, returning hardcoded token'
		return 'N7MsnE8Y_kLfaSJ6UTW4'
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


def generateDescribe(targetCredentials, isSandbox){
	def statusCode = -1
	def sandboxString = env.SFDC_SANDBOX.toBoolean()? ' -sa ' : ''
	withCredentials([usernamePassword(credentialsId: targetCredentials, usernameVariable: 'SFDC_USN', passwordVariable: 'SFDC_PWD')]) {
		withAnt(installation: 'Ant Installation') {
	// 		withEnv(["ANT_OPTS=-Dhttps.proxyHost=proxymadrid.rm.gr.repsolypf.com -Dhttp.proxyHost=proxymadrid.rm.gr.repsolypf.com -Dhttp.proxyPort=8080"]) {
				statusCode = sh(script: "dist/migrationtool/post2sf.exe describe -u ${SFDC_USN} -p '${SFDC_PWD}' ${sandboxString}",
							 returnStatus: true)
	// 		}
		}
	}
	if(statusCode != 0){
		error 'FATAL: Cannot create describe log. ABORTING'
	}
	return statusCode
}

def handleDeltaStatus(statusCode) {
	def message
	delta_built = false
	switch(statusCode) {
		case 0:
			echo 'INFO: Delta package build correclty'
			delta_built = true
			file = createDeltaArtifacts()
			break
		case 11:
			echo 'WARNING: Delta package build with warnings'
			delta_built = true
			file = createDeltaArtifacts()
			break
		case 123:
			error 'ERROR: Could not find remote/source branch, exiting...'
			break
		case 2:
			currentBuild.result = 'ABORTED'
			echo 'WARNING: Branches up to date, could not build delta package'
			break
		case 3:
			currentBuild.result = 'ABORTED'
			error 'FATAL: Merge Conflicts found'
			break
		case 4:
			echo 'WARNING: No changes detected in src folder, could not build delta package'
			break
		default:
			error 'FATAL: Unhandled Errors...'
	}
}

def createDeltaArtifacts() {
	def date = sh (script: 'date "+%y%m%d_%H%M"', returnStdout: true).trim()
	def source = sh(script: "echo ${env.BRANCH_NAME} | tr '/' '-'", returnStdout: true).trim()
	def target = sh(script: "echo ${env.TAG} | tr '/' '-'", returnStdout: true).trim()
	def path = "${source}-${target}"
	def file = "${date}__${path}"
	dir('artifacts_folder') {
		sh "zip -r ${file}.zip ../srcToDeploy"
		sh "mv output.txt ${file}.txt && mv mergerReport.html ${file}.html"
		archiveArtifacts allowEmptyArchive: true, artifacts: "${file}.*", fingerprint: true
	}
	return file
}
