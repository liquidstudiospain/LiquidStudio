pipelineJob("${REPOSITORY_FOLDER_PATH}/builder") {
	description()
	keepDependencies(false)
	parameters {
		choiceParam("DELTA_STRATEGY", ["Build Delta", "Merge Delta"], "")
		stringParam("SOURCE_REFERENCE", "", "")
		stringParam("TARGET_REFERENCE", "", "")
		stringParam("SOURCE_BRANCH", "", "")
		credentialsParam("SFDC_CREDENTIALS") {
			description("For generating describe.log only")
			defaultValue()
			type("com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl")
			required(true)
		}
		booleanParam("SFDC_SANDBOX", false, "For generating describe.log only")
		stringParam("REPOSITORY_URL", REPOSITORY_URL, "Do not edit this value")
		credentialsParam("PRIVATE_TOKEN") {
			description("Do not touch")
			defaultValue(PRIVATE_TOKEN)
			type("com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl")
			required(true)
		}
		credentialsParam("SSH_GITLAB") {
			description("Do not edit this value")
			defaultValue(SSH_GITLAB)
			type("com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey")
			required(true)
		}
		stringParam("DEVOPS_TAG", DEVOPS_TAG, "Do not edit this value")
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
			scriptPath("seeder/cfg/pipeline-builder.groovy")
            }
        }
    }
}
