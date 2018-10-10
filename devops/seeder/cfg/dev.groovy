pipelineJob("${PROJECT_FOLDER_PATH}/${PROJECT_CODE}_dev") {
	parameters {
		credentialsParam("PRIVATE_TOKEN") {
			description()
			defaultValue(PRIVATE_TOKEN)
			type("com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl")
			required(true)
		}
        credentialsParam("SSH_GITLAB") {
			description()
			defaultValue(SSH_GITLAB)
			type("com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey")
			required(true)
		}
		credentialsParam("SFDC_CREDENTIALS") {
			description()
			defaultValue(SFDC_CREDENTIALS)
			type("com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl")
			required(true)
		}
		booleanParam("SFDC_SANDBOX", SFDC_SANDBOX.toBoolean(), "Check if target environment is a Sandbox")
		stringParam("DEVOPS_TAG", DEVOPS_TAG, "")

		stringParam("PROJECT_CODE", PROJECT_CODE, "Donnot edit this values")
		stringParam("SOURCE_BRANCH_PATTERN", "(fix|feature)\\/.+(\\/.+)*", "Donnot edit this values")
	}
	triggers {
		gitlabPush {
			buildOnMergeRequestEvents(true)
			buildOnPushEvents(false)
			enableCiSkip(true)
			commentTrigger('Jenkins please retry a build')
			setBuildDescription(true)
			rebuildOpenMergeRequest('source')
			includeBranches(WORKING_BRANCH)
		}
	}
	definition {
		cpsScm {
			scm {
				git {
					remote {
						url(SEED_REPOSITORY)
						credentials(SSH_GITLAB)
					}
					branch(SEED_BRANCH)
				}
			}
			scriptPath("seeder/cfg/pipeline-dev.groovy")
		}
	}
}
