# A simple forecast run rerunner for scalability tests

## Enivironment

'''module load python3/3.8.8-01'''

## Usage

Specify your reference setup, binary and settings in vhr.yaml. In this file you also specify the software environment required. The config files allows you to change the number of processors and the decomposition layout. Run with

'''./vhr_scal.py -c vhr.yaml'''

The result will end up under '''$SCRATCH/vhr_exercise'''



