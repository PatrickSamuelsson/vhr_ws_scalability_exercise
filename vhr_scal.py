#!/usr/bin/env python3

import os
import sys
import re
import shutil
import yaml
import argparse


#####################################################################################3
def set_verbosity(a) :
  p = 1
  if a.v != None :
   p += len(a.v)

  if a.s != None :
   p -= len(a.s)
  return p

#####################################################################################3
def find_files(path,check_file=True):
  result = []
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
  print('Read namelist:',filename)
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
         if k not in done and v > -1:
          update.insert(-2,'  {}={},\n'.format(k,v))
        done=[]
        nfld=0
        nchg=0
      
      key = l.replace('&','').strip()
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
        if v is not None :
          n[1]=str(v)+',\n'
          update[-1] = '='.join(n)
        else:
          new_settings[key][k]=int(n[1].replace(',','').strip())

  return update

def update_settings(s):

 new_settings= { 'NAMDIM' : {},
                 'NAMPAR0' : {},
                 'NAMPAR1' : {},
                 'NAMIO_SERV': {} }

 if 'NPROMA' in s :
     new_settings['NAMDIM']['NPROMA'] = s['NPROMA']
 if 'NPROC' in s :
     new_settings['NAMPAR0']['NPROC'] = s['NPROC']

 if 'NPROCX' in s and 'NPROCY' in s:
     new_settings['NAMPAR0']['NPRGPEW']= s['NPROCX']
     new_settings['NAMPAR0']['NPRTRV']= s['NPROCX']
     new_settings['NAMPAR0']['NPRGPNS']= s['NPROCY']
     new_settings['NAMPAR0']['NPRTRW']= s['NPROCY']
               
 if 'NPROC_IO' in s :
     new_settings['NAMIO_SERV']['NPROC_IO']= s['NPROC_IO']

 if 'NSTRIN' in s :
     new_settings['NAMPAR1']['NSTRIN'] = s['NSTRIN']
     new_settings['NAMPAR1']['NSTROUT'] = s['NSTRIN']

 return new_settings

def skipme(d):
      return re.match(r'((core|log|PF|drhook|io_serv)(.*)|MASTERODB|fort.4|ICMSH(.*)+\d{4})',d)

def setup_files(indir,files,links):

    for link in links:
      if os.path.islink(link):
          os.unlink(link)
      fullpath = os.path.realpath(os.path.join(indir,link))
      os.symlink(fullpath,link)

    for fname in files:
        shutil.copy(os.path.join(indir,fname),'.')


def create_job(wrkdir,i,ns,val,binary,environment,dry):

  jobfile = 'test.job'

  logfile = os.path.join(wrkdir,'job.log')
  tpn=val['TASK-PER-NODE'] if 'TASK-PER-NODE' in val else 128
  nodes = int((ns['NAMPAR0']['NPROC']+max(0,ns['NAMIO_SERV']['NPROC_IO']))/tpn)
  ompt = 'export OMP_NUM_THREADS={}'.format(val['OMP_NUM_THREADS']) if 'OMP_NUM_THREADS' in val else 1


  line = '''#!/bin/bash
#SBATCH --qos=np
#SBATCH --time=2:00:00
#SBATCH --error={0}
#SBATCH --output={0}
#SBATCH --job-name=vhr:{1}
#SBATCH --nodes={2}
#SBATCH --ntasks-per-node={3}
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread

{6}

{7}

cd {5}

srun {4}

'''.format(logfile,i,nodes,tpn,binary,wrkdir,environment,ompt)

  print()
  print("Creating job as",os.path.join(wrkdir,jobfile))
  print("  logfile:",logfile)
  print("  settings:",ns)
  print("  task-per-node:",tpn)
  print("  OMP_NUM_THREADS:",ompt)

  f=open(jobfile,'w')
  f.write(line)
  f.close()

  if dry :
      print("Dry run, job not submitted")
  else:
      os.system('sbatch {}'.format(jobfile))


def main(argv) :

  parser = argparse.ArgumentParser(description='Wrapper for VHR scalability exercise')
  parser.add_argument('-c',dest="config_file",help='Config file',required=True,default='vhr.yaml')
  parser.add_argument('-v', action='append_const', const=int, help='Increase verbosity')
  parser.add_argument('-s', action='append_const', const=int, help='Decrease verbosity')
  parser.add_argument('-d',action="store_true",dest="dry",
                      help="Dry run, do all preparations without submitting the job",required=False,default=False)


  if len(argv) == 1 :
     parser.print_help()
     sys.exit(1)

  args = parser.parse_args()
  printlev = set_verbosity(args)


  # Read config file
  if not os.path.isfile(args.config_file) :
     print("Could not find config file:",args.config)
     sys.exit(1)

  config = yaml.safe_load(open(args.config_file))
  environment = config['environment'][config['use_environment']]


  indir=config['indir']
  if 'vhrdir' not in config:
    config['vhrdir']='{}/vhr_exercise'.format(os.environ['SCRATCH'])
  binary=config['binary']

  print("Reference setup:",indir)
  files = find_files(indir)
  links = find_files(indir,False)

  files = [x for x in files if not skipme(x)]
  links = [x for x in links if not skipme(x)]
  if printlev > 1:
      print('\nCopying:')
      [print('   ',f) for f in sorted(files)]
      print('\nLinking:')
      [print('   ',l) for l in sorted(links)]

  settings = config['settings']


  if not os.path.exists(config['vhrdir']):
      os.makedirs(config['vhrdir'])

  for tag,val in settings.items():
    if 'active' in val:
        if not val['active']:
            continue
    os.chdir(config['vhrdir'])
    wrkdir=os.path.join(config['vhrdir'],'{}'.format(tag))
    if not os.path.exists(wrkdir):
        os.makedirs(wrkdir)

    os.chdir(wrkdir)
    setup_files(indir,files,links)

    new_settings = update_settings(val)
    namelistfile = None
    if 'ref_ua_namelist' in val:
        if val['ref_ua_namelist'] is not None:
          namelistfile= val['ref_ua_namelist']
    if 'ref_ua_namelist' in config and namelistfile is None:
        if config['ref_ua_namelist'] is not None:
           namelistfile= config['ref_ua_namelist']
    if namelistfile is None:
        namelistfile= os.path.join(indir,'fort.4')

    namelist = read_namelist(namelistfile)
    modif = update_namelist(namelist,new_settings)
    write_namelist('fort.4',modif)

    create_job(wrkdir,tag,new_settings,val,binary,environment,args.dry)

if __name__ == "__main__":
    sys.exit(main(sys.argv))


