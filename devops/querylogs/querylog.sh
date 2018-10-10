#!/usr/local/bin/bash

# TODO prompt login
# TODO filter by time
# TODO implement loop in same file...

declare -A arrayMap
arrayMap['ERNESTO']='00558000002L5O3AAK'
arrayMap['TAMARA']='00558000002L5O5AAK'
arrayMap['SONIA']='00558000002L5NsAAK'
arrayMap['DEBORA']='00558000002L5NkAAK'
arrayMap['INTEGRATION']='00558000002KumdAAC'
arrayMap['PATRICIA']='00558000002L5NoAAK'
arrayMap['ALBERTO']='00558000002L5NzAAK'
arrayMap['MARIA']='00558000002L5NtAAK'
arrayMap['EDUARDO']='00558000002L5NrAAK'

USERNAME="$1"
USERNAME_ID="${arrayMap[$USERNAME]}"

if [[ -z $USERNAME_ID ]]; then
    echo "Error could not find username '$USERNAME'"
    exit 1
fi

mkdir -p log/$USERNAME

QUERY="SELECT Id, StartTime, Operation FROM ApexLog WHERE LogUserId='$USERNAME_ID'"
echo $QUERY
for each in $(force query "$QUERY" 2>&1); do
    if [[ $each = *Id* ]]; then
        continue
    elif [[ $each = *ERROR* ]]; then
        echo -e "\033[31m[ERROR]\033[0m Please login using 'force login'"
        exit 1
    fi

    log_line=$(echo $each | sed -e 's/"//g')

    IFS=','; read -r -a array <<< "$log_line"; unset IFS;

    log_id=${array[0]}
    log_operation=${array[1]}
    log_date=${array[2]}
    log_date_formated=$(gdate -d "$log_date" +%y%m%d_%H%M%S)

    # echo "id=$log_id"
    # echo "date=$log_date"
    # echo "log_operation=$log_operation"
    # echo "formated=$log_date_formated"
    # echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

    file="$log_date_formated-$log_id.debug"

    file_folder=log/$USERNAME/$log_operation

    mkdir -p $file_folder
    
    file_path=$file_folder/$file

    if [[ ! -f $file_path ]]; then
        echo -e "\033[33m[INFO]\033[0m Downloading log $file"
        force log $log_id > $file_path
    fi
done

echo -e "\033[32m[SUCCESS]\033[0m Downloaded all $USERNAME logs"
