# A simple forecast rerunner for scalability tests (and other fun stuff)

The following tool can be used to run a number of runs varying the number of processors in a simple way. It relies on an existing working directory from a forecast model run. The tool has been tested with both available examples for the VHR exercises.

If you need any help please feel free to conatct the author.

## Environment

Make sure you have python3 loaded by

`module load python3/3.8.8-01`

## Configuration options

### Global settings

A yaml file is used to configure the settings for the runs. First a few general settings are done:

- `vhrdir` - defines the working directory for your runs
- `indir` - defines the reference directory from a run with the forecast model
- `binary` - full path and name of the binary to be used
- `use_environment` - environment setings suitable for the run, content defined further down

The keys recognized are defined in rules. New keys can be defined according to needs
```
rules:
  NAMDIM : ['NPROMA']
  NAMPAR0 : ['NPROC']
  NAMPAR1 : ['NPRGPEW','NPRTRV',
             'NPRGPNS','NPRTRW','NSTRIN']
  NAMIO_SERV: ['NPROC_IO']
```

### Settings per run

Now we can proceed and define number of runs to be done. The first one uses the default settings from your reference namelist:

```
settings:
    default: 
       active : True
       NPROMA:
       NPROC:
       NPROCX:
       NPROCY:
       NSTRIN:
       NPROC_IO:
       OMP_NUM_THREADS: 1
       TASKS-PER-NODE: 128

```

where `active` tells if the run should be executed or not and NPROCX and NPROCY are mapped to NPRGPEW/NPRTRV and NPRGPNS/NPRTRW respectively. We can specify some more details for like in the following:

```
    4nodes_ioserv: 
       active : False
       NPROC: 496
       NPROCX: 16
       NPROCY: 31
       NSTRIN: 1
       NPROC_IO: 16
       OMP_NUM_THREADS: 1
       TASKS-PER-NODE: 128
```
Here we have defined both the number of nodes, the 2D decomposition and activated the IO-server. More configuration examples can be found in the to yaml files in this repo. The creative user can add own namelist variables to change, e.g. for dynamics. A possible dynamics orienented test could look like:

```
rules:
  NAMDYNA : ['LSETTLS','LPC_FULL']
  NAMPAR0 : ['NPROC']
  NAMIO_SERV: ['NPROC_IO']

settings:
  great_fun_tests: 
       LSETTLS : 'F'
       LPC_FULL : 'T'
       NPROC:
       NPROC_IO:
```


### Specifying an arbitrary namelist

The upper air namelist used for each run can be specified in three ways

- The default is to use the fort.4 file available in `vhrdir`
- Specify `ref_ua_namelist` on top level to override the default, i.e `/some_path/fort.4`
- Speficy `ref_ua_namelist` for a single run to use this namelist for this specific run, i.e

```
settings:
    myrun:
     ref_ua_namelist: '/some_other_path/fort.4
     ...
```

### The runtime environment

Finally we define which modules to load and environment variables to specify for the binary used

```
environment:
 gnu: | 
   module load prgenv/gnu
   module load openmpi/4.1.1.1
   module load openblas/0.3.9
   module load netcdf4/4.7.4
   module load hdf5/1.10.6
   module load ecmwf-toolbox/2021.08.3.0

```

## Usage

To start your runs simply 

```
./vhr_scal.py -c your_config.yaml
```

which will submit jobs for the active runs you've defined. The result will end up under the specified vhrdir. The script takes the following arguments:

```
usage: vhr_scal.py [-h] -c CONFIG_FILE [-v] [-s] [-d]

Wrapper for VHR scalability exercise

optional arguments:
  -h, --help      show this help message and exit
  -c CONFIG_FILE  Config file
  -v              Increase verbosity
  -s              Decrease verbosity
  -d              Dry run, do all preparations without submitting the job
```

## Plotting the result

The cost of the runs can be plotted using `plot_cost.py`. The script scans your logfiles and takes the following arguments



```
usage: plot_cost.py [-h] [-e EXPERIMENTS] [-i VHRDIR] [-l] [-p OUTFILE]

Plot cost as function of NODES

optional arguments:
  -h, --help      show this help message and exit
  -e EXPERIMENTS  List of experiments as exp1:exp2:...:expN
  -i VHRDIR       Experiment directory
  -l              List experiments
  -p OUTFILE      Stor plot to filename given

```
![](https://github.com/uandrae/vhr_ws_scalability_exercise/blob/main/example.png)
