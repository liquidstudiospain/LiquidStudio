node {
    if(env.SOURCE_BRANCH != env.gitlabSourceBranch) {
        println "WARNING: Source branch triggered by Merge Request (${env.gitlabSourceBranch})  " +
                "did not match with set up one (${env.SOURCE_BRANCH})"
        currentBuild.result = 'NOT_BUILT'
        return
    } else {
	stage('Pre Configuration') {
		echo "INFO: Accepting Merge Request ${env.gitlabMergeRequestTitle}"
		PRIVATE_TOKEN = get_token(env.PRIVATE_TOKEN)
		sh ('rm -fr *')
	}
	stage('Configuration') {
		get_artifacts()
	}
	stage('Starting Build') {
		updateGitlabStatus('running')
        postToGitlab("### Starting Build [${env.BUILD_DISPLAY_NAME}](${env.RUN_DISPLAY_URL})")
	}
	stage('Accept Merge Request') {
	    def tagName = env.gitlabSourceBranch.substring(2) + '_' + new Date().format('yyyyMMdd-hhmmss').toString()
		editLastGitlabComment("+ Creating Release Branch and Tag, with name ${tagName}")
        createRelease(tagName)
        def result_string = "**Jenkins Build ${env.BUILD_DISPLAY_NAME} finished " +
                            "${currentBuild.currentResult}**"
		editLastGitlabCommentMultiComment(get_ending_comment_part(result_string))
		if (currentBuild.currentResult == Result.SUCCESS.toString()) {
			updateGitlabStatus('success')
		} else {
			updateGitlabStatus('failed')
        }
	}
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

def get_ending_comment_part(result_comment) {
    def build_link = "+ **[Build Status](${env.RUN_DISPLAY_URL})**"
    return [result_comment, build_link]
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

def updateGitlabStatus(status) {
    sh(script: "dist/callgitlab/call_gitlab.exe status --no-ssl --force-https -t ${PRIVATE_TOKEN} -s ${status}", returnStatus: true)
}

def createRelease(tagName) {
	sh(script: "dist/callgitlab/call_gitlab.exe release --no-ssl --force-https -to ${PRIVATE_TOKEN} -tn ${tagName}", returnStatus: true)
}

def get_token(privateTokenCredential) {
    try {
        def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
            com.cloudbees.plugins.credentials.Credentials.class, Jenkins.instance, null, null);
        def PRIVATE_TOKEN = creds.find{ it.id == "${privateTokenCredential}" }
        return PRIVATE_TOKEN.apiToken
    } catch (org.jenkinsci.plugins.scriptsecurity.sandbox.RejectedAccessException e1) {
        echo 'Exception Launched, returning hardcoded token'
        return 'N7MsnE8Y_kLfaSJ6UTW4'
    }
}
