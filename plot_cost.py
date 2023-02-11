#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import re
import os
import sys
import argparse

def scan_log(filename):

 n = {}
 with open(filename, "r") as a_file:
  for line in a_file:
    if re.match(r'(.*?)(ElapsedRaw)(.*)\: (\d{1,})',line):
     zz = re.findall(r'(ElapsedRaw)(.*)\: (\d{1,})',line)
     n[zz[0][0]]=int(zz[0][-1])
     continue
    if re.match(r'(.*)(NSTOP)(.*)=(( ){0,})(\d{1,})',line):
     zz = re.findall(r'(.*)(|NSTOP)(.*) =(( ){0,})(\d{1,})',line)
     n[zz[0][0].strip()]=int(zz[0][-1])
     continue
    if re.match(r'(.*)(NFLEVG|NSTRIN|NPROMA|NPRGPNS|NPRGPEW|NDLON|NDGUXG) =(( ){0,})(\d{1,})',line):
     zz = re.findall(r'(.*)(NFLEVG|NSTRIN|NPROMA|NPRGPNS|NPRGPEW|NDLON|NDGUXG) =(( ){0,})(\d{1,})',line)
     n[zz[0][1]]=int(zz[0][-1])
     continue
    if re.match(r'#SBATCH(.*)ntasks-per-node=(.*)',line):
     zz= re.findall(r'(.*)(ntasks-per-node)=(.*)',line)
     n[zz[0][-2]]=int(zz[0][-1])
     continue
    if re.match(r'(.*)(ntasks\-per\-node|NPROC_IO|TSTEP) {0,}=( {0,}\d{1,}),',line):
     zz = re.findall(r'(ntasks\-per\-node|NPROC_IO|TSTEP) {0,}=( {0,}\d{1,}),',line)
     n[zz[0][0]]=int(zz[0][1])
     continue

 a_file.close()

 return n

############################################################################33

def plot_log(scans):

 print('plotting ...')
 size = 13

 fig, ax = plt.subplots(1)

 for exp,v in scans.items():
  x,y = [],[]
  if 'ElapsedRaw' in v:
    x.append(v['NODES'])
    nhour = float(v['NSTOP']*v['TSTEP'])/3600.
    y.append(v['ElapsedRaw']/nhour)

  xx,yy = [],[]
  for i in np.argsort(x):
      xx.append(x[i])
      yy.append(y[i])

  size -= 1
  ax.plot(xx,yy,'*',label=exp,markersize=size)

 ax.legend()
 ax.set(ylabel='Time per forecast hour(s)')
 ax.set(xlabel='Nodes')
 fig.suptitle('Cost for DOMAIN:({}x{}x{})'.format(v['NDLON'],v['NDGUXG'],v['NFLEVG']))

 plt.show()

############################################################################33

def scan_logs(path):
 n = {}
 for f in ['NODE.001_01','fort.4','job.log','test.job']:
  fname = os.path.join(path,f)
  if os.path.isfile(fname):
   x = scan_log(fname)
   for k,v in x.items():
       n[k] = v

 if 'NPROC_IO' not in n :
     n['NPROC_IO'] = 0
 n['NPROC'] = int(n['NPRGPEW'])*int(n['NPRGPNS'])
 n['NODES'] = int((int(n['NPRGPEW'])*int(n['NPRGPNS'])+int(n['NPROC_IO']))/int(n['ntasks-per-node']))

 return n
############################################################################33

def main(argv) :

  parser = argparse.ArgumentParser(description='Plot cost as function of NODES')
  parser.add_argument('-e',dest="experiments",help='List of experiments as exp1:exp2:...:expN',required=True,default=None)
  parser.add_argument('-i',dest="vhrdir",help='List of experiments',required=False,default=os.path.join(os.environ['SCRATCH'],'vhr_exercise'))

  if len(argv) == 1 :
     parser.print_help()
     sys.exit(1)

  args = parser.parse_args()


  d = {}
  for exp in args.experiments.split(':'):
    path = os.path.join(args.vhrdir,exp)
    print("-------- Scan",exp,"under",path)
    d[exp]=scan_logs(path)
    print(d[exp])

  plot_log(d)


if __name__ == "__main__":
    sys.exit(main(sys.argv))


