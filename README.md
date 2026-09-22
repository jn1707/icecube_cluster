# icecube_cluster

Tools for submitting and managing jobs on scientific computing clusters (HTCondor, SLURM, GridEngine, PBS).

## Features
- Submit jobs to IceCube (HTCondor) and UCPH (SLURM) clusters
- Create job submission scripts for Condor, SLURM, GridEngine, PBS
- Manage job arrays and resources
- Utilities for file system and Unix operations

## Installation

From the `icecube_cluster` directory:
```bash
pip install .
```
For development:
```bash
pip install -e .
```

## Quick start

See [`examples/submit_script.py`](examples/submit_script.py). Minimal usage:

```python
from icecube_cluster.cluster import ClusterSubmitter

with ClusterSubmitter(
    job_name="my_job",
    memory=4000,          # MB
    disk_space=10000,     # MB
    wall_time=4.0,        # hours (use whole hours)
    num_cpus=1,
    num_gpus=0,
    submit_dir="submit_my_job",
    output_dir="logs",
    cluster_name="nbi",   # or "icecube_npx"
    # ... cluster-specific options ...
) as submitter:
    submitter.add(command="python3 my_analysis.py --input data.txt")
```

## Submitting Jobs to IceCube (HTCondor)

- Use the `condor.py` and `cluster.py` modules.
- Create a Condor submit file:
  ```python
  from icecube_cluster.condor import create_condor_submit_file
  ```
- Use `accounting_group="quicktest"` for debugging and small tests; will run almost immediately
- For advanced management, use `ClusterSubmitter` in `cluster.py`.

## Submitting Jobs to UCPH (SLURM)

- Use the `slurm.py` and `cluster.py` modules.
- Create a SLURM submit file:
  ```python
  from icecube_cluster.slurm import create_slurm_submit_file
  ```
- Use the `partition=` option to specify the partition (e.g. `icecube` for CPU jobs, `icecube_gpu` for GPU jobs) 
- Use the `start_up_commands=["source /path/to/.venv/bin/activate"]` to activate a specific virtual environment
- Submit from `npx-submitter`. `cobalt` has no Condor client tools. The library can remote-submit via SSH to `npx-submitter`, but sometimes it helps to keep things simple
- Load CMFVS and your virtual environmentss throug the option `start_up_commands=["eval `/cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/setup.sh`"]`
- For advanced management, use `ClusterSubmitter` in `cluster.py`.

## Cluster names reference

| `cluster_name` | System | Notes |
|----------------|--------|--------|
| `nbi` | SLURM | Copenhagen / NBI |
| `icecube_npx` | Condor | Madison NPX |
| `icecube_grid` / `icecube_osg` | Condor | grid; stricter scratch rules, user proxy |
| `desy_*` | Condor | DESY HTC submit nodes |
| `hpcc` / `psu` | SLURM | MSU / PSU |

If you omit `cluster_name`, the library tries to guess from the hostname (and may prompt interactively on IceCube).

## Important practices
- The `memory_MB`, `num_cpus`, and other options are not cosmetic. Please eestimate your resource requirements before submitting. 
- If you request all available `memory_MB` allocated to a partition, but only one gpu, the other gpus remain idle and unavailable to other users because all the memory has been allocated to your job.
- If you have large cpu/gpu jobs write intermediary checkpoints to the disk, so that your progress does not get lost e.g. when your job hits the wall time. 