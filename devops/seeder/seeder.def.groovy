freeStyleJob("${NAME}") {
    parameters {
        stringParam("JOB_PREFIX_NAME", "SALESFORCE" , "SALESFORCE")
        stringParam("MODULE", "", "")
        stringParam("AP_ID", "", "")
        stringParam("JOB_NAME", "", "")
        stringParam("WEBHOOK_USR", "", "")
        nonStoredPasswordParam("WEBHOOK_TOKEN", "")
        choiceParam('REPOSITORY_OPTIONS', ['Nuevo repositorio', 'Repositorio existente'])

        stringParam("WORKING_BRANCH", "" , "")
        stringParam("PROJECT_REF", "", "")
        stringParam("SEED_PROJECTID", "", "${SEED_PROJECTID}")

		credentialsParam("PRIVATE_TOKEN") {
			description()
			type("com.cloudbees.plugins.credentials.common.StandardCredentials")
			required(true)
		}
		credentialsParam("SFDC_CREDENTIALS") {
			description()
			type("com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl")
			required(true)
		}
		booleanParam("SFDC_SANDBOX")
		stringParam("PROJECT_CODE", "", "")
		stringParam("DEVOPS_TAG", "", "")
	}

    scm {
        git {
            remote {
                url("${REPO}")
                credentials("${SSH_GITLAB}")
            }
        }
    }

    steps {
        dsl {
            external('SF_seed_job/SeederJob.groovy')  
        }
    }
}
