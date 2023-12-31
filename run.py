import time
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
elif 'flask' in JOB_NAME:
    template='.python'
elif 'express' in JOB_NAME:
    template='.node'
else:
    template=''

service=config

if 'SERVICE_ID' in service:
    config=service
    with open(r'D:\wildfly\bin\service.xml'+template+'.template', 'r') as file:
        data = file.read()
        if 'JRE' in config:
            data = data.replace('%JRE%',r'D:\java\jdk-17.0.5+8\bin\java')
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
        if template=='.java':
            if 'spring' in JOB_NAME:
                for path in os.listdir(WORKSPACE+'\\build\\libs'):
                    if os.path.isfile(os.path.join(WORKSPACE+'\\build\\libs', path)):
                        if path.endswith("SNAPSHOT.jar"):
                            data = data.replace('%JAR%',(r'D:\microservicios\ ').strip()+JOB_NAME+'\\'+path)
            else:
                data = data.replace('%JAR%',r'D:\microservicios\\'+JOB_NAME+'\\quarkus-run.jar')
        with open(WORKSPACE+'\service.xml', 'w+') as file:
            file.write(data)
            print(WORKSPACE+'\service.xml was created!')


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
if p.returncode==0:
    print('El servicio "'+SERVICE_ID+'" existe se desinstalara!')
    p=run(["netstat","-ano"], stdout=PIPE, stderr=PIPE)
    if p.returncode==0:
        output=p.stdout.decode(charset)
        for line in output.splitlines():
            if 'TCP' in line and (':'+str(PORT)+' ') in line:
                print(line)
        print( 'stderr:', p.stderr.decode("cp1252"))
    p=run(["sc","stop",SERVICE_ID], stdout=PIPE, stderr=PIPE)
    print('sc stop -> status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    if 'quarkus' in JOB_NAME or 'spring' in JOB_NAME:
        os.chdir('D:\\microservicios\\'+JOB_NAME)
    #se asume que existe service.exe 
    p=run(["service","uninstall"], stdout=PIPE, stderr=PIPE)
    print('service uninstall -> status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))

if 'spring' in JOB_NAME:
    p=run(["robocopy",WORKSPACE+'\\build\\libs','D:\\microservicios\\'+JOB_NAME,"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
    print('robocopy -> exit status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    shutil.copy(r'D:\wildfly\bin\service.exe', 'D:\\microservicios\\'+JOB_NAME+'\service.exe')
elif 'quarkus' in JOB_NAME:
    p=run(["robocopy",WORKSPACE+'\\build\\quarkus-app','D:\\microservicios\\'+JOB_NAME,"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)
    print('robocopy -> exit status code:', p.returncode )
    print('stdout:', p.stdout.decode(charset))
    print('stderr:', p.stderr.decode(charset))
    shutil.copy(r'D:\wildfly\bin\service.exe', 'D:\\microservicios\\'+JOB_NAME+'\service.exe')
else:
    shutil.copy(r'D:\wildfly\bin\service.exe', WORKSPACE+'\service.exe')
#    p=run(["robocopy",WORKSPACE+'\\dist','D:\\microservicios\\'+JOB_NAME,"/COPYALL","/E"], stdout=PIPE, stderr=PIPE)


with open(WORKSPACE+'\\run.bat', 'w+') as the_file:
    if template=='.node':
        the_file.write('nodist global 15.14.0 && node dist/index.js')
    elif template=='.python':
        port=port and (' --port='+str(port)) or ''
        the_file.write('waitress-serve'+port+' wsqi:app')
    print(WORKSPACE+'\\run.bat was created!')
    
if 'quarkus' in JOB_NAME or 'spring' in JOB_NAME:

    if 'spring' in JOB_NAME:
        for path in os.listdir('D:\\microservicios\\'+JOB_NAME):
            if os.path.isfile(os.path.join('D:\\microservicios\\'+JOB_NAME, path)):
                print(path)
    
    shutil.copy(WORKSPACE+'\service.xml', 'D:\\microservicios\\'+JOB_NAME+'\service.xml')
    os.chdir('D:\\microservicios\\'+JOB_NAME)
elif 'flask' in JOB_NAME:
    if os.path.exists(WORKSPACE+'\\run.bat'):
        shutil.copy(WORKSPACE+'\\run.bat', 'D:\\microservicios\\'+JOB_NAME+'\\run.bat')
    os.chdir('D:\\microservicios\\'+JOB_NAME)

print('installing service "'+SERVICE_ID+'"!')
p=run(["service","install"], stdout=PIPE, stderr=PIPE)
print('service install -> exit status code:', p.returncode )
print('stdout:', p.stdout.decode() )
print('stderr:', p.stderr.decode() )
p=run(["sc","start",SERVICE_ID], stdout=PIPE, stderr=PIPE)
print( 'sc start -> exit status code:', p.returncode )
print( 'stdout:', p.stdout.decode(charset))
print( 'stderr:', p.stderr.decode(charset))
