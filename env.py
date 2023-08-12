import time
from config import config
import sys,os
from subprocess import run, PIPE
import shutil

WORKSPACE=os.environ['WORKSPACE']
JOB_NAME=os.environ['JOB_NAME']
if 'spring_' in JOB_NAME:
    template='.java'
    gradle=WORKSPACE+'\\build.gradle'
    fin = open(gradle, "rt")
    data = fin.read()
    data = data.replace('D:/projects/java/spring/isobit/build', 'D:/java')
    fin.close()
    fin = open(gradle, "wt")
    fin.write(data)
    fin.close()
elif 'quarkus' in JOB_NAME:
    template='.java'
    gradle=WORKSPACE+'\\build.gradle'
    fin = open(gradle, "rt")
    data = fin.read()
    data = data.replace('C:/projects/java/spring/java_isobit/build', 'D:/java')
    data = data.replace('D:/projects/java/spring/isobit/build', 'D:/java')
    #close the input file
    fin.close()
    #open the input file in write mode
    fin = open(gradle, "wt")
    #overrite the input file with the resulting data
    fin.write(data)
    #close the file
    fin.close()
elif 'flask' in JOB_NAME:
    template='.python'
elif 'express' in JOB_NAME:
    template='.node'
elif 'laravel' in JOB_NAME:
    template='.laravel'
else:
    template=''


env_file=None
try:
    env_filename=WORKSPACE+'\\.env.example'
    env_file = open(env_filename, 'r')
except FileNotFoundError:
    try:
        env_filename=WORKSPACE+'\\src\\main\\resources\\application.properties.example'
        env_file = open(env_filename, 'r')
    except FileNotFoundError:
        env_file=None

if env_file!=None:
    Lines = env_file.readlines()
else:
    Lines=[]

if JOB_NAME in config:
    custom=config[JOB_NAME]
    del config[JOB_NAME]
    config={**config,**custom}

print(config)
if 'PORT' in config:
    if 'spring_' in JOB_NAME:
        config['server.port']=config['PORT']
    else:
        config['quarkus.http.port']=config['PORT']
    
for key in ['VUE_APP_PUBLIC_PATH','DESTINY_DIR']:
    if key in config:
        file = open(key, 'w')
        file.write(config[key].replace('/','\\'))
        file.close()

service={};
for key in ['SERVICE_ID','SERVICE_NAME','SERVICE_DESCRIPTION']:
    if key in config:
        service[key]=config[key]
        del config[key]
if 'PORT' in config:
    service['PORT']=config['PORT']


with open(env_filename.replace('.example',''), 'w+') as file_out:
    for line in Lines:
        words=line.split('=')
        if len(words)==2 and words[0]!='VUE_APP_PUBLIC_PATH':
            if words[0].strip() in config:
                words[1]=config[words[0].strip()]
            file_out.write(str(words[0]).strip()+'='+str(words[1]).strip()+'\n')
    key='VUE_APP_PUBLIC_PATH'
    if key in config:
        print(config)
        print('====================================')
        file_out.write('VUE_APP_PUBLIC_PATH='+config[key]+'\n')
        file_out.write('PUBLIC_URL='+config[key])
        


    





