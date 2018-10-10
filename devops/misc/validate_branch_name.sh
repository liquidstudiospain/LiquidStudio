#!/bin/bash

if [ $# -ne 1 ]; then
	echo -e "\033[31m[ERROR] Must provide unless and only one branch name\033[39m"
	# echo -e "\033[31m[ERROR] Must provide unless one branch name\033[39m"
	exit 1
fi

function validate_branch {
	for regex in $ALLOWED_FORMATS ; do
		if [[ $branch =~ $regex ]] ; then
			echo -e "\t\033[32m- Branch '$branch' has a valid format\033[39m"
			return 0
			# exit 0
		fi
	done
	echo -e "\033[31m\t- Branch name '$branch' did not match any valid format\033[39m"
	return 1
	# exit 1
}

branch="$1"

ALLOWED_FORMATS="^feature/.*$ ^fix/.*$ ^selenium$ ^seleniumDev/feature/.* ^seleniumDev/fix/.*"


validate_branch $branch
exit $?

