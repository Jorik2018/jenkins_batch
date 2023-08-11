import time
from config import config
import sys,os
from subprocess import run, PIPE

#read .env.example
env_file = open('C:\\ProgramData\\Jenkins\\.jenkins\\workspace\\'+sys.argv[1]+'\\.env.example', 'r')


Lines = env_file.readlines()

#port where service run
port=False

key=sys.argv[1];
if key in config:
    custom=config[key]
    del config[key]
    config={**config,**custom};
    

with open(r'D:\wildfly\bin\service.xml.template', 'r') as file:
    data = file.read()
    for key in config:
        if key=='SERVICE_ID':
            os.environ[key] = config[key]
        if key=='PORT':
            port=config[key]
        data = data.replace('%'+key.strip()+'%',str(config[key]).strip())
    
    print('==============================================')
    print(data)
    with open(sys.argv[2]+'\service.xml', 'w+') as file:
        file.write(data)
        print(sys.argv[2]+'\service.xml was created!')
        
with open(sys.argv[2]+'\\.env', 'w+') as file_out:
    for line in Lines:
        words=line.split('=')
        if len(words)==2:
            if words[0].strip() in config:
                words[1]=config[words[0].strip()]            
            print(words[0].strip()+'='+words[1].strip())
            file_out.write(words[0].strip()+'='+words[1].strip()+'\n')

with open(sys.argv[2]+'\\run.bat', 'w+') as the_file:
    port=port and (' --port='+str(port)) or ''
    the_file.write('waitress-serve'+port+' wsqi:app')
    print(sys.argv[2]+'\\run.bat was created!')




