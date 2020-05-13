# AGS logs with SQLITE -- Setup

## Create the environment

1. Install Anaconda.
2. Clone this repo.
3. `cd legendary-octo-happiness`
4. Create the proper environment using

```
conda env create -f environment.yml
```

5. Activate the environment with `conda activate agslogs`
6. Install the packages with `python setup.py install`

## Initialize the SQLITE database

So, for example, to setup for idpgis, use

```
ags-initialize idpgis
```

# Let 'er rip!

```
./process_daily_logs.sh idpgis
```

This first time, it will take a while for this to run, as it has to get thru
several days of logs.  Subsequent runs over the next few days will be quicker.
