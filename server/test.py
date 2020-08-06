import time
import os, sys

path = sys.argv[1]
path = os.path.join(path, 'out.log')
if os.path.exists(path):
  os.remove(path)
for a in range(0,5):
  f = open(path, 'a')
  time.sleep(1)
  f.write(str(a) + '\n')
  f.close()
f = open(path, 'a')
f.write('finished \n')
f.close()