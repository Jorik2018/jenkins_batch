REM SET PATH=%PATH%;C:\Users\Administrador.WIN-5UFR8AED4T8\.pyenv\pyenv-win\bin;C:\Users\Administrador.WIN-5UFR8AED4T8\.pyenv\pyenv-win\shims
REM SET PYENV=C:\Users\Administrador.WIN-5UFR8AED4T8\.pyenv\pyenv-win\
REM SET PYENV_HOME=C:\Users\Administrador.WIN-5UFR8AED4T8\.pyenv\pyenv-win\
SET PATH=%PATH%;C:\Users\Administrador.WIN-5UFR8AED4T8\AppData\Local\Programs\Python\Python310\Scripts\;C:\Users\Administrador.WIN-5UFR8AED4T8\AppData\Local\Programs\Python\Python310\

REM SET VERSION=3.10

REM IF (%3)==() (
REM     SET VERSION=3.10.0
REM )

pipenv --rm

REM DEL C:\ProgramData\Jenkins\.jenkins\workspace\%1\Pipfile.lock

if not exist "D:\microservicios\%1\app" mkdir D:\microservicios\%1\app

robocopy C:\ProgramData\Jenkins\.jenkins\workspace\%1\app D:\microservicios\%1\app /COPYALL /E

copy D:\wildfly\bin\service.exe D:\microservicios\%1

copy D:\wildfly\bin\wsqi.py D:\microservicios\%1

move Pipfile D:\microservicios\%1

python "D:\wildfly\bin\flask.py" "%1" "D:\microservicios\%1"

ECHO "================="
ECHO SERVICE_ID
ECHO %SERVICE_ID%

D:
cd D:\microservicios\%1

rem pyenv local %VERSION%

sc query %2 > NUL
IF ERRORLEVEL 1060 GOTO MISSING
ECHO EXISTS
GOTO SERVICEOK
:MISSING

service install
:SERVICEOK

sc query %2
sc stop %2
pipenv --rm
DEL Pipfile.lock
pipenv install
pipenv install waitress mysql-connector-python
pipenv install
sc start %2