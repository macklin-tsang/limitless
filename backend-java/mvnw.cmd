@REM Maven wrapper script for Windows
@REM Downloads and runs Maven automatically

@echo off
setlocal

set WRAPPER_JAR=.mvn\wrapper\maven-wrapper.jar
set WRAPPER_PROPERTIES=.mvn\wrapper\maven-wrapper.properties

@REM Check for Java
where java >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Java is not installed or not in PATH
    echo Please install Java 17 or later: https://adoptium.net/
    exit /b 1
)

@REM Run using Maven wrapper jar
java -jar "%WRAPPER_JAR%" %*

endlocal
