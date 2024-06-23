@ECHO OFF

SET ISQ_HOME=%~dp0isqc

IF EXIST "%ISQ_HOME%" GOTO start_env

:download
REM isq-open seems deprecated, isQ now has official windows build :)
wget -nc https://www.arclightquantum.com/isq-releases/isqc-standalone/0.2.8/isqc-0.2.8-x86_64-pc-windows-gnu.tar.gz
tar xvf isqc-0.2.8-x86_64-pc-windows-gnu.tar.gz

:start_env
SET PATH=%ISQ_HOME%\bin;%ISQ_HOME%\bin\isqc1;%PATH%
DOSKEY isq=isqc1.exe -I "%ISQ_HOME%\lib" $*
CMD /K isqc --version
