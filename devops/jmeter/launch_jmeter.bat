@echo off

set file=%~1

IF "%file%"=="" set file=SeleniumTests.jmx

IF EXIST results RMDIR "results" /S /Q

md results

jmeter -n -t SeleniumTests.jmx -l results\results.txt -e -o results\result