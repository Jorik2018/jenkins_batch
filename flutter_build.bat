SET PATH=%PATH%;C:\Program Files\flutter_3.3.2\flutter\bin;C:\Windows\SysWOW64;C:\Users\Administrador.WIN-5UFR8AED4T8\AppData\Local\Programs\Python\Python39\Scripts\;C:\Users\Administrador.WIN-5UFR8AED4T8\AppData\Local\Programs\Python\Python39\
python "D:\wildfly\bin\flutter.py"  %1  %2

SET proyect=%1
SET proyect=%proyect:"=%
SET directory=%2
SET directory=%directory:"=%
SET directory=D:\wildfly\bin\apps%directory:/=\%

IF exist %directory% ( echo %directory% exists ) ELSE ( md %directory%)

(robocopy C:\ProgramData\Jenkins\.jenkins\workspace\%proyect%\build\web %directory% /COPYALL /E) ^& IF %ERRORLEVEL% LEQ 4 exit /B 0