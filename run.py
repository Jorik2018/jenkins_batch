import glob
import time
import re
from config import config
import sys,os
from subprocess import run, PIPE,check_output,STDOUT
import shutil

WORKSPACE=os.environ['WORKSPACE']
JOB_NAME=os.environ['JOB_NAME']

if JOB_NAME in config:
    custom=config[JOB_NAME]
    del config[JOB_NAME]
    config={**config,**custom}

SERVICE_ID=config['SERVICE_ID']
PORT=config['PORT']
if 'quarkus' in JOB_NAME or 'spring' in JOB_NAME:
    template='.java'
elif 'laravel' in JOB_NAME:
    template='.laravel'
elif 'rust_' in JOB_NAME or 'axum_' in JOB_NAME or 'axum-' in JOB_NAME:
    template='.rust'
elif 'flask' in JOB_NAME:
    template='.python'
elif 'express' in JOB_NAME:
    template='.node'
else:
    template=''

service=config
DESTINY_PATH = 'D:\\microservicios\\'+JOB_NAME
if 'SERVICE_ID' in service:
    config=service
    with open(r'D:\wildfly\bin\service.xml'+template+'.template', 'r') as file:
        data = file.read()
        if 'JRE' in config:
            data = data.replace('%JRE%',r'D:\java\jdk-17.0.5+8\bin\java')
        elif '-zk-' in JOB_NAME:
            data = data.replace('%JRE%',r'D:\microservicios\zk\zk_web-0.0.1-SNAPSHOT.bat')
        else:
            data = data.replace('%JRE%',r'D:\jdk-11.0.11\bin\java')

        for key in config:
            if key=='SERVICE_ID':
                file = open(key, 'w')
                file.write(config[key])
                file.close()
            if key=='PORT':
                port=config[key]
            data = data.replace('%'+key.strip()+'%',str(config[key]).strip())
        if template=='.rust':
            for path in os.listdir(WORKSPACE+'\\target\\release'):
                    if os.path.isfile(os.path.join(WORKSPACE+'\\target\\release', path)):
                        if path.endswith(".exe"):
                            data = data.replace('%EXECUTABLE%',os.path.join((r'D:\microservicios\ ').strip(),JOB_NAME,path))
        if template=='.java':
            if 'spring' in JOB_NAME:
                if '-zk-' in JOB_NAME:
                    data = data.replace('%JAR%',(r'D:\microservicios\ ').strip()+'zk\\zk_web-0.0.1-SNAPSHOT.jar\" -Djava.library.path=\"D:\\microservicios\\zk\" --spring.config.name=\"zk_web')
                else:
                    if os.path.exists(WORKSPACE+'\\build\\libs'):
                        for path in os.listdir(WORKSPACE+'\\build\\libs'):
                            if os.path.isfile(os.path.join(WORKSPACE+'\\build\\libs', path)):
                                if path.endswith("SNAPSHOT.jar"):
                                    data = data.replace('%JAR%',(r'D:\microservicios\ ').strip()+JOB_NAME+'\\'+path)
            else:
                data = data.replace('%JAR%',DESTINY_PATH+'\\quarkus-run.jar')
        os.makedirs(DESTINY_PATH, exist_ok=True)
        with open(os.path.join(DESTINY_PATH, 'service.xml'), 'w+') as file:
            print(data)
            file.write(data)
            print(DESTINY_PATH+'\service.xml was created!')


def f(p):
	print( 'exit status code:', p.returncode )
	print( 'stdout:', p.stdout.decode() )
	print( 'stderr:', p.stderr.decode() )
	if p.returncode!=0:
		print('error! :(')
		sys.exit(p.returncode)

charset="cp1252"
p=run(["sc","query",SERVICE_ID], stdout=PIPE, stderr=PIPE)
print('p.returncode='+str(p.returncode))
if p.returncode==1060:
    print('El servicio "'+SERVICE_ID+'" no existe se instalara!')
returncode=p.returncode

print('El PORT "'+str(PORT)+'" se liberara!')
p=run(["netstat","-ano"], stdout=PIPE, stderr=PIPE)
if p.returncode==0:
    output=p.stdout.decode(charset)
    for line in output.splitlines():
        if 'TCP' in line and (':'+str(PORT)+' ') in line:
            match = re.search(r'\s(\d+)$', line)
            print("match="+line)
            if match:
                pid = match.group(1)
                print("============>pid="+pid)
                run(["taskkill", "/F", "/PID", pid], stdout=PIPE, stderr=PIPE)
    print( 'stderr:', p.stderr.decode("cp1252"))

if returncode==0:
    print('El servicio "'+SERVICE_ID+'" existe se desinstalara!')
    p=run(["sc","stop",SERVICE_ID], stdout=PIPE, stderr=PIPE)
    print('sc stop -> status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    #uninstall service
    if 'quarkus' in JOB_NAME or 'spring' in JOB_NAME:
        if '-zk-' in JOB_NAME:
            os.chdir('D:\\microservicios\\zk')
        else:
            os.chdir(DESTINY_PATH)
    #se asume que existe service.exe 
    p=run(["service","uninstall"], stdout=PIPE, stderr=PIPE)
    print('service uninstall -> status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))

archivos_log = glob.glob(os.path.join(DESTINY_PATH, '*.log'))
for archivo in archivos_log:
    try:
        os.remove(archivo)
        print(f'Eliminado: {archivo}')
    except Exception as e:
        print(f'Error al eliminar {archivo}: {e}')
if '-zk-' in JOB_NAME:
    archivos_log = glob.glob(os.path.join('D:\\microservicios\\zk', '*.log'))
    for archivo in archivos_log:
        try:
            os.remove(archivo)
            print(f'Eliminado: {archivo}')
        except Exception as e:
            print(f'Error al eliminar {archivo}: {e}')


if 'axum' in JOB_NAME:
    p=run(["robocopy",WORKSPACE+'\\target\\release',DESTINY_PATH,"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
    print('robocopy -> exit status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    shutil.copy(WORKSPACE+'\\.env', DESTINY_PATH+'\.env')
elif 'spring' in JOB_NAME:
    if '-zk-' not in JOB_NAME:
        p=run(["robocopy",WORKSPACE+'\\build\\libs',DESTINY_PATH,"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
        print('robocopy -> exit status code:', p.returncode )
        print('stdout:', p.stdout.decode(charset))
        print('stderr:', p.stderr.decode(charset))
elif 'quarkus' in JOB_NAME:
    p=run(["robocopy",WORKSPACE+'\\build\\quarkus-app',DESTINY_PATH,"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
    print('robocopy -> exit status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
elif 'express' in JOB_NAME:
    p=run(["robocopy",os.path.join(WORKSPACE,'dist'),os.path.join(DESTINY_PATH,'dist'),"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
    print('robocopy -> exit status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    p=run(["robocopy",os.path.join(WORKSPACE,'node_modules'),os.path.join(DESTINY_PATH,'node_modules'),"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
    print('robocopy -> exit status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    shutil.copy(os.path.join(WORKSPACE,'.env'), os.path.join(DESTINY_PATH,'.env'))


if '-zk-' in JOB_NAME:
    JOB_NAME = 'zk'
    os.chdir(DESTINY_PATH)
    print('chdir '+DESTINY_PATH)



shutil.copy(r'D:\wildfly\bin\service.exe', DESTINY_PATH+'\service.exe')
with open(DESTINY_PATH+'\\run.bat', 'w+') as the_file:
    if template=='.node':
        the_file.write('SET PATH=C:\\wildfly-18.0.1.Final\\bin\\.data\\node-v22.13.0-win-x64;C:\\wildfly-18.0.1.Final\\bin\\.data\\node-v22.13.0-win-x64\\globals  && npm config set prefix C:\\wildfly-18.0.1.Final\\bin\\.data\\node-v22.13.0-win-x64\\globals && node dist/index.js')
    elif template=='.python':
        port=port and (' --port='+str(port)) or ''
        the_file.write('waitress-serve'+port+' wsqi:app')
    print(DESTINY_PATH+'\\run.bat was created!')
    
print('installing service "'+SERVICE_ID+'"!')
os.chdir(DESTINY_PATH)
print('os.getcwd()="'+os.getcwd()+'"!')

p=run(["cmd", "/c", "dir",DESTINY_PATH], stdout=PIPE, stderr=PIPE)
print('dir=', p.returncode )
print('stdout:', p.stdout.decode(charset))
print('stderr:', p.stderr.decode() )


cmd=["service","install"]
print(cmd)
p=run(cmd, stdout=PIPE, stderr=PIPE)
print('service install -> exit status code:', p.returncode )
print('stdout:', p.stdout.decode(charset))
print('stderr:', p.stderr.decode() )
p=run(["sc","start",SERVICE_ID], stdout=PIPE, stderr=PIPE)
print( 'sc start -> exit status code:', p.returncode )
print( 'stdout:', p.stdout.decode(charset))
print( 'stderr:', p.stderr.decode(charset))
