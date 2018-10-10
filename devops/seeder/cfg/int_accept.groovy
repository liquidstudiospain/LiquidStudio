pipelineJob("${PROJECT_FOLDER_PATH}/${PROJECT_CODE}_int_accept") {
	parameters {
		credentialsParam("PRIVATE_TOKEN") {
			description()
			defaultValue(PRIVATE_TOKEN)
			type("com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl")
			required(true)
		}
		stringParam("DEVOPS_TAG", DEVOPS_TAG, "")

		stringParam("PROJECT_CODE", PROJECT_CODE, "Donnot edit this values")
		stringParam("SOURCE_BRANCH", WORKING_BRANCH, "Donnot edit this values")
	}
    triggers {
        gitlabPush {
			buildOnMergeRequestEvents(false)
            buildOnPushEvents(false)
			enableCiSkip(true)
			setBuildDescription(true)
			rebuildOpenMergeRequest('source')
			includeBranches(MASTER_BRANCH)
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
			scriptPath("seeder/cfg/pipeline-int_accept.groovy")
		}
	}
}
