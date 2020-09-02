import time
import os, sys
import argparse

def main(directory):
  path = os.path.join(output, 'out.log')
  if os.path.exists(path):
    os.remove(path)
  for a in range(0,10):
    f = open(path, 'a')
    time.sleep(1)
    print a
    f.write(str(a) + '\n')
    f.close()
  f = open(path, 'a')
  f.write('finished \n')
  f.close()
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-d', '--directory', help='tmp directory for current slurm job data input/ouput.', required=True)
  kwargs = vars(parser.parse_args())
  main(**kwargs)
