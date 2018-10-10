''' Module for creating releases '''
from models.git import Project, Branch, Tag, MergeRequest, Remote


def create_release(host, token, project_id, mr_iid, tag_name, target_branch,
                   message, release_description, release_branch, ssl_verify):
    ''' Creates a release (accepts merge + create tag + create branch) '''
    remote = Remote(host, token)
    project = Project(project_id)

    merge_request = MergeRequest(mr_iid)
    tag = Tag(tag_name, target_branch, message, release_description)
    branch = Branch(release_branch, target_branch)

    merge_request.accept_merge_request(remote, project, ssl_verify)
    tag.create_remote(remote, project, ssl_verify)
    branch.create_remote(remote, project, ssl_verify)
