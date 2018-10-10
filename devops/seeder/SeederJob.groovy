import groovy.json.JsonSlurper
import jenkins.model.*

def DEV_JOB = 'seeder/cfg/dev.groovy'
def INT_JOB = 'seeder/cfg/int.groovy'
def INT_ACCEPT_JOB = 'seeder/cfg/int_accept.groovy'
def DEPLOYER_JOB = 'seeder/cfg/deployer.groovy'
def BUILDER_JOB = 'seeder/cfg/builder.groovy'

def CONFIG_FILES = [DEV_JOB, INT_JOB, INT_ACCEPT_JOB, DEPLOYER_JOB, BUILDER_JOB] as String[]

REPOSITORY_FOLDER_PATH =  "SALESFORCE/${PROJECT_REPOSITORY_REF}"
PROJECT_FOLDER_PATH =  "${REPOSITORY_FOLDER_PATH}/${APPLICATION_ID}_${PROJECT_CODE}"
WORKING_BRANCH = "W/AP_${APPLICATION_ID}_${PROJECT_CODE}"

def systemCredentialsProvider = Jenkins.instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0]
def credentials = systemCredentialsProvider.credentials
def PRIVATE_TOKEN_TEXT = (credentials.find{ it.id == "${PRIVATE_TOKEN}" }).apiToken

println "INFO: Starting process with: ${REPOSITORY_OPTIONS}"
// *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* Checking REPOSITORY *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
def repositoryInfo
if (REPOSITORY_OPTIONS.equals('Nuevo repositorio')) {
	println "INFO: Creating Respository: "
	requestUrl = "${GITLAB_URL}/api/v4/projects/?private_token=${PRIVATE_TOKEN_TEXT}"
	repository = new Repository().setName(PROJECT_REPOSITORY_REF)
								 .setIssuesEnabled(true)
								 .setMergeRequestsEnabled(true)
								 .setJobsEnabled(true)
								 .setResolveOutdatedDiffDiscussions(true)
								 .setVisibility('private')
								 .setPrintingMergeRequestLinkEnabled(true)

	def responseNewRepo = doHttpRequestWithJson(repository.toJsonString(), requestUrl, "POST", true)

	if (responseNewRepo.statusCode != 201) {
		throw new javaposse.jobdsl.dsl.DslException("A project named '${PROJECT_REPOSITORY_REF}' already exists, aborting")
	}

	repositoryInfo = responseNewRepo.json()

	println "DEBUG: Web to new Repo: ${repositoryInfo.web_url}"
	println "DEBUG: Project Id: ${repositoryInfo.id}"
} else if (REPOSITORY_OPTIONS.equals('Repositorio existente')) {
	// *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* Getting ProjectId *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	repositoryInfo = getProjectByName("${PROJECT_REPOSITORY_REF}", "${PRIVATE_TOKEN_TEXT}", "${GITLAB_URL}")
	requestUrl = "${GITLAB_URL}/api/v4/projects/${repositoryInfo.id}?private_token=${PRIVATE_TOKEN_TEXT}"
	def responseGetRepo = doGetHttpRequest(requestUrl, false)
	if (responseGetRepo.statusCode != 200) {
		throw new javaposse.jobdsl.dsl.DslException("Could not find project with id '${repositoryInfo.id}', aborting")
	}
} else {
	throw new javaposse.jobdsl.dsl.DslException("Invalid option ${REPOSITORY_OPTIONS}, aborting")
}

println "DEBUG: Web to new Repo: ${repositoryInfo.web_url}"
println "DEBUG: Project Id: ${repositoryInfo.id}"

REPOSITORY_URL = repositoryInfo.ssh_url_to_repo
PROJECTID = repositoryInfo.id

// *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* Checking if MASTER_BRANCH EXISTS *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
println "INFO: Checking if master branch \'${PROJECT_MASTER_BRANCH}\' exists"
def validateBranchUrl = "${GITLAB_URL}/api/v4/projects/${PROJECTID}/repository/branches/${PROJECT_MASTER_BRANCH}" +
						"?private_token=${PRIVATE_TOKEN_TEXT}"
def validateBranchResponse = doGetHttpRequest(validateBranchUrl, false)

if (validateBranchResponse.statusCode != 200) {
	// *-*-*-*-*-*-*-*-*-*-*-*-*-* Intializing REPOSITORY *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	println "INFO: Master Branch \'${PROJECT_MASTER_BRANCH}\' does not exits, creating stale branch"
	Action[] actions = [new Action().setAction('create')
									.setContent("# ${PROJECT_REPOSITORY_REF}\n")
									.setFilePath('README.md')] as Action[]
	Commit initializingCommit = new Commit().setCommitMessage('Initialize Repository')
											.setBranch(PROJECT_MASTER_BRANCH)
											.setActions(actions)
	requestUrl = "${GITLAB_URL}/api/v4/projects/${PROJECTID}/repository/commits?private_token=${PRIVATE_TOKEN_TEXT}"
	def responseNewBranch = doHttpRequestWithJson(initializingCommit.toJsonString(), requestUrl, "POST", true)
    if (responseNewBranch.statusCode != 201) {
        throw new javaposse.jobdsl.dsl.DslException("Could not create master branch '${PROJECT_MASTER_BRANCH}'")
    }
} else {
	println "INFO: Branch ${PROJECT_MASTER_BRANCH} exists"
}

// *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* Creating WORKING_BRANCH *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
println "INFO: Creating Working Branch ${WORKING_BRANCH}"

requestUrl = "${GITLAB_URL}/api/v4/projects/${PROJECTID}/repository/branches?private_token=${PRIVATE_TOKEN_TEXT}"
workingBranch = new Branch().setBranch(WORKING_BRANCH)
						    .setRef("master")
def responseNewWorking = doHttpRequestWithJson(workingBranch.toJsonString(), requestUrl, "POST", true)

if (responseNewWorking.statusCode != 201) {
	println "WARNING: Working Branch ${WORKING_BRANCH} could not be created, check status message"
}

// *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* Creating Folders *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

folders = []
println "INFO: Creating folders '${REPOSITORY_FOLDER_PATH}' and '${PROJECT_FOLDER_PATH}'"

REPOSITORY_FOLDER_PATH.split('/').each {
	folders.add(it)
	REPOSITORY_FOLDER_PATH = folders.join('/')
	folder(REPOSITORY_FOLDER_PATH)
}

folders = []
PROJECT_FOLDER_PATH.split('/').each {
	folders.add(it)
	PROJECT_FOLDER_PATH = folders.join('/')
	folder(PROJECT_FOLDER_PATH)
}

// *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* Creating JOBS *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
println "INFO: Creating jobs from: ${CONFIG_FILES}"

def seedRepo = getProjectByName("${SEED_REPOSITORY_REF}", "${PRIVATE_TOKEN_TEXT}","${GITLAB_URL}")

for (configFile in CONFIG_FILES) {
	println "INFO: Creating job ${configFile}"
	//def configFileEncoded = java.net.URLEncoder.encode(configFile, "UTF-8")

    configFileName = extractFileName(configFile)

    println "INFO: Retrieving '${configFileName}' from seed repository"
    def jobCode = getFileContent('V4', seedRepo.id, configFile)

    def binding = new Binding()
    binding.setVariable("SEED_REPOSITORY",  seedRepo.ssh_url_to_repo)
    binding.setVariable("CONFIG_FILE_NAME", configFile)
    binding.setVariable("PRIVATE_TOKEN", PRIVATE_TOKEN)
    binding.setVariable("JOB_NAME", JOB_NAME)
    binding.setVariable("MASTER_BRANCH", PROJECT_MASTER_BRANCH)
    binding.setVariable("BRANCH_NAME", WORKING_BRANCH)
    if (configFileName == 'dev') {
        binding.setVariable("SFDC_CREDENTIALS", SFDC_CREDENTIALS_DEV)
        binding.setVariable("SFDC_SANDBOX", SFDC_SANDBOX_DEV)
    } else if (configFileName == 'int') {
        binding.setVariable("SFDC_CREDENTIALS", SFDC_CREDENTIALS_INT)
        binding.setVariable("SFDC_SANDBOX", SFDC_SANDBOX_INT)
    }
    def shell = new GroovyShell(binding)

    println "INFO: Building job for '${configFileName}'"

    def closure = shell.evaluate("{->${jobCode}}")
    closure.delegate = this
    closure()

    println "INFO: ${configFile} built correctly"
}

// *-*-*-*-*-*-*-*-*-*-*-*-*-* Creating WEBHOOK *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*--*--*

println "INFO: Retrieving Project WebHooks"
hooksUrl = "${GITLAB_URL}/api/v4/projects/${PROJECTID}/hooks?" +
		   "private_token=${PRIVATE_TOKEN_TEXT}"
def webhooksResponse = doGetHttpRequest(hooksUrl, false)
if (webhooksResponse.statusCode == 200) {
	webhooks = webhooksResponse.json()
	requestUrl = "${GITLAB_URL}/api/v4/projects/${PROJECTID}/hooks?private_token=${PRIVATE_TOKEN_TEXT}"

	for (configFile in CONFIG_FILES) {
		configFileName = extractFileName(configFile)

        if (configFileName != 'dev' && configFileName != 'int' && configFileName != 'int_accept'){
            println "INFO: ${configFileName} does not requiere webhook"
            continue
        }

		println "INFO: Checking if WebHook for '${configFileName}' is created"
		jobPath = "${PROJECT_FOLDER_PATH}/${PROJECT_CODE}_${configFileName}"

		webhookUrl = convertToWebHookFormat(JENKINS_URL, jobPath, WEBHOOK_USR, WEBHOOK_TOKEN)
		println "DEBUG: ${webhookUrl}"
		def found = false
		for (webhook in webhooks) {
			if (webhookUrl == webhook.url) {
				found = true
			}
		}
        if (! found) {
            println "INFO: Creating WebHook for ${configFile}"
            webhook = new Webhook().setId(PROJECTID)
                                   .setUrl(webhookUrl)
            switch(configFileName) {
                case 'dev':
                    webhook.setPushEvents(true)
                           .setMergeRequestsEvents(true)
                           .setNoteEvents(true)
                    break
                case 'int':
                    webhook.setPushEvents(true)
                           .setMergeRequestsEvents(true)
                           .setNoteEvents(true)
                    break
                case 'int_accept':
                    webhook.setPushEvents(false)
                           .setMergeRequestsEvents(true)
                           .setNoteEvents(false)
                    break
            }
            def responseHook = doHttpRequestWithJson(webhook.toJsonString(),
                                                     requestUrl, "POST", true)
		} else {
			println "INFO: Webhook already created for ${configFile}"
		}
	}
}

// -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*
// UTILS
private getProjectByName(String pName, String privateToken, String GITLAB_URL) {

	String requestUrl = "${GITLAB_URL}/api/v4/projects/?private_token=${privateToken}&search=${pName}&membership=true"
	def responseGetProject = doGetHttpRequest(requestUrl, false)
	String result = null

	if (responseGetProject.statusCode != 200) {
		println("ERROR")
		throw new javaposse.jobdsl.dsl.DslException("Could not find project with id '${pName}', aborting")
	}

	return responseGetProject.json()[0]
}

HttpResponse doGetHttpRequest(String requestUrl, Boolean printBody) {
	URL url = new URL(requestUrl)
	HttpURLConnection connection = url.openConnection()

	connection.setRequestMethod("GET")

	println "DEBUG: Request (GET):\n\tURL: ${requestUrl}"

	connection.connect()

	HttpResponse resp = new HttpResponse(connection)

	println "DEBUG: Response:\n\tHTTP Status: ${resp.statusCode}\n\tMessage: ${resp.message}"

	if (printBody) {
		println "\tResponse Body: ${resp.body}"
	}

	return resp
}

HttpResponse doHttpRequestWithJson(String json, String requestUrl, String verb, Boolean printBody) {
	URL url = new URL(requestUrl)
	HttpURLConnection connection = url.openConnection()

	connection.setRequestMethod(verb)
	connection.setRequestProperty("Content-Type", "application/json")
	connection.doOutput = true

	def writer = new OutputStreamWriter(connection.outputStream)
	writer.write(json)
	writer.flush()
	writer.close()

	connection.connect()

	HttpResponse resp = new HttpResponse(connection)

	println "DEBUG: Request (${verb}):\n\tURL: ${requestUrl}\n\tJSON: ${json}"
	println "DEBUG: Response:\n\tHTTP Status: ${resp.statusCode}\n\tMessage: ${resp.message}"
	if (printBody) {
		println "\tResponse Body: ${resp.body}"
	}

	return resp
}

String extractFileName(filePath){
	def regex = '.+\\/(.+)\\..+'
	def matcher = filePath =~ regex
	return matcher[0][1]
}

String getFileContent(String apiVersion, Integer seedRepoId, String configFile) {
    def encodedFilePath = java.net.URLEncoder.encode(configFile, "UTF-8")
    def encodeSeedBranch = java.net.URLEncoder.encode(SEED_BRANCH, "UTF-8")

    if (apiVersion == 'V4') {
        println "INFO: Retrieving file using Gitlab API V4"

        def getFileUrlV4 = "${GITLAB_URL}/api/v4/projects/${seedRepoId}/repository/files/${encodedFilePath}/raw?private_token=${PRIVATE_TOKEN_TEXT}&ref=${encodeSeedBranch}"
        def fileResponse = doGetHttpRequest(getFileUrlV4, false)

        if (fileResponse.statusCode != 200) {
            throw new javaposse.jobdsl.dsl.DslException("Could not get file from blob id")
        }

        return fileResponse.body
    }
    if (apiVersion == 'V3') {
        println "INFO: Retrieving file using Gitlab API V4"

        def getBlobUrlV3 = "${GITLAB_URL}/api/v3/projects/${seedRepoId}/repository/files?private_token=${PRIVATE_TOKEN_TEXT}&file_path=${encodedFilePath}&ref=${encodeSeedBranch}"
        def blobResponse = doGetHttpRequest(getBlobUrlV3, true)

        if (blobResponse.statusCode == 410) {
            throw new javaposse.jobdsl.dsl.DslException("${blobResponse.json().error}")
        }
        if (blobResponse.statusCode != 200) {
            throw new javaposse.jobdsl.dsl.DslException("Could not get Blob Id for '${configFile}'")
        }

        def getFileUrlV3 = "${GITLAB_URL}/api/v3/projects/${seedRepoId}/repository/raw_blobs/${blobResponse.json().id}?private_token=${PRIVATE_TOKEN_TEXT}"
        def fileResponse = doGetHttpRequest(getFileUrlV3, false)
        if (fileResponse.statusCode != 200) {
            throw new javaposse.jobdsl.dsl.DslException("Could not get file from blob id")
        }
        return fileResponse.body
    }
    throw new javaposse.jobdsl.dsl.DslException("API version not allowed")
}

String convertToWebHookFormat(jenkinsUrl, jobPath, jenkinsUser, jenkinsKey) {
	def regex = '(http[s]:\\/\\/)(.+)\\/'
	def matcher = jenkinsUrl =~ regex
	def webhookUrl = "${matcher[0][1]}${jenkinsUser}:${jenkinsKey}@${matcher[0][2]}/project/${jobPath}"
	return webhookUrl
}

// -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*
// MODELS
class HttpResponse {
	String body
	String message
	Integer statusCode
	boolean failure = false

	public HttpResponse(HttpURLConnection connection){
		this.statusCode = connection.responseCode
		this.message = connection.responseMessage

		if(statusCode == 200 || statusCode == 201){
			this.body = connection.content.text//this would fail the pipeline if there was a 400
		}else{
			this.failure = true
			this.body = connection.getErrorStream().text
		}

		connection = null //set connection to null for good measure, since we are done with it
	}

	public json(){
		if (this.body != null) {
			return new JsonSlurper().parseText(this.body)
		}
	}
}

class GitlabObject {
	public String toJsonString(){
		return groovy.json.JsonOutput.toJson(this).toString()
	}
}

class Webhook extends GitlabObject {
	Integer id
	String url
	Boolean push_events
	Boolean merge_requests_events
	Boolean note_events

	public Webhook setId(Integer id) {
		this.id = id
		return this
	}

	public Webhook setUrl(String url) {
		this.url = url
		return this
	}

	public Webhook setPushEvents(Boolean pushEvents) {
		this.push_events = pushEvents
		return this
	}

	public Webhook setMergeRequestsEvents(Boolean mergeRequestsEvents) {
		this.merge_requests_events = mergeRequestsEvents
		return this
	}

	public Webhook setNoteEvents(Boolean noteEvents) {
		this.note_events = noteEvents
		return this
	}
}

class Repository extends GitlabObject {
	String name
	Boolean issues_enabled
	Boolean merge_requests_enabled
	Boolean jobs_enabled
	Boolean resolve_outdated_diff_discussions
	String visibility
	Boolean printing_merge_request_link_enabled

	public Repository setName(String name) {
		this.name = name
		return this
	}
	public Repository setIssuesEnabled(Boolean issuesEnabled) {
		this.issues_enabled = issuesEnabled
		return this
	}
	public Repository setMergeRequestsEnabled(Boolean mergeRequestsEnabled) {
		this.merge_requests_enabled = mergeRequestsEnabled
		return this
	}
	public Repository setJobsEnabled(Boolean jobsEnabled) {
		this.jobs_enabled = jobsEnabled
		return this
	}
	public Repository setResolveOutdatedDiffDiscussions(Boolean resolveOutdatedDiffDiscussions) {
		this.resolve_outdated_diff_discussions = resolveOutdatedDiffDiscussions
		return this
	}
	public Repository setVisibility(String visibility) {
		this.visibility = visibility
		return this
	}
	public Repository setPrintingMergeRequestLinkEnabled(Boolean printingMergeRequestLinkEnabled) {
		this.printing_merge_request_link_enabled = printingMergeRequestLinkEnabled
		return this
	}
}

class Branch extends GitlabObject {
	String branch
	String ref

	public Branch setBranch(String branch) {
		this.branch = branch
		return this
	}

	public Branch setRef(String ref) {
		this.ref = ref
		return this
	}

}

class Commit extends GitlabObject {
	String commit_message
	String branch
	Action[] actions

	public Commit setCommitMessage(String commitMessage) {
		this.commit_message = commitMessage
		return this
	}

	public Commit setBranch(String branch) {
		this.branch = branch
		return this
	}

	public Commit setActions(Action[] actions) {
		this.actions = actions
		return this
	}

}

class Action extends GitlabObject {
	String action
	String content
	String file_path

	public Action setAction(String action) {
		this.action = action
		return this
	}

	public Action setContent(String content) {
		this.content = content
		return this
	}

	public Action setFilePath(String filePath) {
		this.file_path = filePath
		return this
	}
}
