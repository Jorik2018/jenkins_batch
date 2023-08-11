import time
import sys,os
from subprocess import run, PIPE

print(sys.argv[1])

def f(p):
	print( 'exit status code:', p.returncode )
	print( 'stdout:', p.stdout.decode() )
	print( 'stderr:', p.stderr.decode() )
	if p.returncode!=0:
		print('error! :(')
		sys.exit(p.returncode)

print("flutter clean")
p=run(["C:\\Program Files\\flutter_3.3.2\\flutter\\bin\\flutter.bat","clean"], stdout=PIPE, stderr=PIPE)

f(p)
print("flutter create .")
p=run(["C:\\Program Files\\flutter_3.3.2\\flutter\\bin\\flutter.bat","create","."], stdout=PIPE, stderr=PIPE)
f(p)

print("flutter build")
p=run(["C:\\Program Files\\flutter_3.3.2\\flutter\\bin\\flutter.bat","build","web","--base-href",sys.argv[2]], stdout=PIPE, stderr=PIPE)

f(p)
