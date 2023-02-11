#!/usr/bin/env python3

import os
import sys
import re
import shutil
import yaml
import argparse



def find_files(path,check_file=True):
  result = []
#  print ("Search in:",path)
  with os.scandir(path) as it:
    for entry in it:
      if check_file:
       if not entry.name.startswith('.') and entry.is_file(follow_symlinks=False):
          result.append(entry.name)
      else:
       if not entry.name.startswith('.') and entry.is_symlink():
          result.append(entry.name)
      if not entry.name.startswith('.') and entry.is_dir():
          subresult = find_files(os.path.join(path,entry.name),check_file)
          subresult = [entry.name + "/" + e for e in subresult]
          result.extend(subresult)
  return result


def read_namelist(filename):
  list = []
  with open(filename, "r") as a_file:
   for line in a_file:
    list.append(line)

  a_file.close()
  return list

def write_namelist(filename,list):
  f = open(filename,'w')
  f.writelines(list)
  f.close()

def update_namelist(list,new_settings):

  search = False
  update = []
  nfld=0
  nchg=0
  done=[]
  for l in list:
    update.append(l)
    if '&' in l:
      if nfld != nchg:
        for k,v in new_settings[key].items():
         if k not in done:
          update.insert(-2,'  {}={},\n'.format(k,v))
        done=[]
        nfld=0
        nchg=0
      
      key = l[1:].strip()
      search = key in new_settings
      if search :
        nfld= len(new_settings[key])
        nchg=0
        done=[]
      continue
    if search:
     for k,v in new_settings[key].items():
      if k in l:
        done.append(k)
        n= l.split('=')
        n[1]=str(v)+',\n'
        update[-1] = '='.join(n)

  return update

def update_settings(s):

 new_settings= { 'NAMPAR0': { 'NPROC': s['NPROC'] , 
                              'NPRGPEW': s['NPROCX'],
                              'NPRGPNS': s['NPROCY'],
                              'NPRTRV' : s['NPROCX'],
                              'NPRTRW' : s['NPROCY'],
                            },
                 'NAMIO_SERV': { 'NPROC_IO' : s['NPROC_IO'] },
               }

 new_settings['NAMPAR1'] = {}
 new_settings['NAMPAR1']['NSTRIN'] = s['NSTRIN']  if 'NSTRIN' in s else 1
 new_settings['NAMPAR1']['NSTROUT'] = s['NSTRIN'] if 'NSTRIN' in s else 1

 return new_settings

def skipme(d):
      return re.match(r'(fort.4|ICMSH(.*)+\d{4}|io_serv(.*))',d)

def setup_files(indir,files,links):

    for link in links:
      if os.path.islink(link):
          os.unlink(link)
      fullpath = os.path.realpath(os.path.join(indir,link))
      os.symlink(fullpath,link)

    for fname in files:
        shutil.copy(os.path.join(indir,fname),'.')


def create_job(wrkdir,i,val,binary,environment):


  jobfile = 'test.job'

  logfile = os.path.join(wrkdir,'job.log')
  tpn=val['TASK-PER-NODE'] if 'TASK-PER-NODE' in val else 128
  nodes = int((val['NPROC']+val['NPROC_IO'])/tpn)
  ompt = 'export OMP_NUM_THREADS={}'.format(val['OMP_NUM_THREADS'])


  line = '''#!/bin/bash
#SBATCH --qos=np
#SBATCH --time=1:00:00
#SBATCH --error={0}
#SBATCH --output={0}
#SBATCH --job-name=vhr:run_{1}
#SBATCH --nodes={2}
#SBATCH --ntasks-per-node={3}
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread

{6}

{7}

cd {5}

srun {4}

'''.format(logfile,i,nodes,tpn,binary,wrkdir,environment,ompt)

  print("Creating job as",os.path.join(wrkdir,jobfile))
  print("  settings:",val)

  f=open(jobfile,'w')
  f.write(line)
  f.close()

  #os.system('sbatch {}'.format(jobfile))


def main(argv) :

  parser = argparse.ArgumentParser(description='Fetch ARPEGE data from Meteo France over ftp')
  parser.add_argument('-c',dest="config_file",help='Config file',required=True,default='vhr.yaml')

  if len(argv) == 1 :
     parser.print_help()
     sys.exit(1)

  args = parser.parse_args()

  # Read config file
  if not os.path.isfile(args.config_file) :
     print("Could not find config file:",args.config)
     sys.exit(1)

  config = yaml.safe_load(open(args.config_file))
  environment = config['environment'][config['use_environment']]



  indir=config['indir']
  vhrdir='{}/vhr_exercise'.format(os.environ['SCRATCH'])
  binary=config['binary']

  print("Reference setup:",indir)
  files = find_files(indir)
  links = find_files(indir,False)

  files = [x for x in files if not skipme(x)]
  links = [x for x in links if not skipme(x)]

  settings = config['settings']

  namelist = read_namelist(os.path.join(indir,'fort.4'))

  if not os.path.exists(vhrdir):
      os.makedirs(vhrdir)

  for tag,val in settings.items():
    os.chdir(vhrdir)
    wrkdir=os.path.join(vhrdir,'test_{}'.format(tag))
    if not os.path.exists(wrkdir):
        os.makedirs(wrkdir)

    os.chdir(wrkdir)
    setup_files(indir,files,links)

    modif = update_namelist(namelist,update_settings(val))
    write_namelist('fort.4',modif)

    create_job(wrkdir,tag,val,binary,environment)

if __name__ == "__main__":
    sys.exit(main(sys.argv))


