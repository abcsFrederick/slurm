import time
import os, sys
import argparse

def main(output):
  path = os.path.join(output, 'out.log')
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
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-o', '--output', help='output.', required=True)
  kwargs = vars(parser.parse_args())
  main(**kwargs)
