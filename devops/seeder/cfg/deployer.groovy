pipelineJob("${REPOSITORY_FOLDER_PATH}/deployer") {
	parameters {
		stringParam("BRANCH_NAME", "", "")
		stringParam("TAG", "", "")
		stringParam("REPOSITORY_URL", REPOSITORY_URL, "")
		stringParam("TEST_TO_RUN", "", "")

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
			defaultValue()
			type("com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl")
			required(true)
		}
        booleanParam("SFDC_SANDBOX", false, "")

		stringParam("DEVOPS_TAG", DEVOPS_TAG, "")
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
			scriptPath("seeder/cfg/pipeline-deployer.groovy")
            }
        }
    }
}
