#!/usr/bin/env python3
"""
Example: submit a Python script to NBI (SLURM) or IceCube NPX (HTCondor).

Usage:
  python3 submit_script.py <python_script> [args...]

Edit the CONFIGURATION section below for your cluster and resources.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURATION — edit these
# ---------------------------------------------------------------------------

# "nbi"          → Copenhagen HPC (SLURM), run this on hep*/fend*
# "icecube_npx"  → IceCube NPX (HTCondor), run this on npx-submitter
CLUSTER = "nbi"

MEMORY_MB = 4000
DISK_SPACE_MB = 10000
WALL_TIME_HOURS = 4.0   # whole hours only (fractions truncate to 0 on SLURM)
NUM_CPUS = 1

# NBI only
PARTITION = "icecube"
VENV_PATH = None  # e.g. "/groups/icecube/$USER/myproject/.venv"

# IceCube only
ACCOUNTING_GROUP = "quicktest"  # change for production work
CVMFS_SETUP = "/cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/setup.sh"

# Path to this repo if it is not installed in the active environment
REPO_PATH = None  # e.g. "/groups/icecube/$USER/icecube_cluster" or "/data/user/$USER/icecube_cluster"

# ---------------------------------------------------------------------------


def _add_repo_to_path():
    if REPO_PATH:
        sys.path.insert(0, str(Path(REPO_PATH).expanduser()))
    else:
        # Allow running from a clone: examples/ -> repo root
        repo_root = Path(__file__).resolve().parents[1]
        if (repo_root / "icecube_cluster").is_dir():
            sys.path.insert(0, str(repo_root))


_add_repo_to_path()
from icecube_cluster.cluster import ClusterSubmitter  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        print("\nExample: python3 submit_script.py my_analysis.py --input data.txt")
        sys.exit(1)

    script_path = Path(sys.argv[1]).resolve()
    script_args = " ".join(sys.argv[2:])
    if not script_path.is_file():
        print(f"Error: script not found: {script_path}")
        sys.exit(1)

    script_name = script_path.stem
    submit_dir = script_path.parent / f"submit_{script_name}"
    log_dir = script_path.parent / "cluster_logs"

    startup = []
    kwargs = dict(
        job_name=script_name[:20],
        memory=MEMORY_MB,
        disk_space=DISK_SPACE_MB,
        wall_time=WALL_TIME_HOURS,
        num_cpus=NUM_CPUS,
        submit_dir=str(submit_dir),
        output_dir=str(log_dir),
        run_locally=False,
        cluster_name=CLUSTER,
    )

    if CLUSTER == "nbi":
        kwargs["partition"] = PARTITION
        if VENV_PATH:
            startup.append(f"source {Path(VENV_PATH).expanduser()}/bin/activate")
        command = f"python3 {script_path} {script_args}".strip()

    elif CLUSTER == "icecube_npx":
        # Workers need a Python with CVMFS; keep outputs on shared /data/user
        kwargs["accounting_group"] = ACCOUNTING_GROUP
        kwargs["job_mode"] = "lite_wrapper"
        startup.append(f"eval `{CVMFS_SETUP}`")
        if not str(script_path).startswith("/data/user/"):
            print(
                "Warning: script is not under /data/user/$USER. "
                "Worker nodes cannot see submitter /scratch; prefer /data/user."
            )
        command = f"python {script_path} {script_args}".strip()

    else:
        print(f"Error: unknown CLUSTER={CLUSTER!r}. Use 'nbi' or 'icecube_npx'.")
        sys.exit(1)

    if startup:
        kwargs["start_up_commands"] = startup

    print(f"Cluster : {CLUSTER}")
    print(f"Command : {command}")
    print(f"Resources: {MEMORY_MB} MB RAM, {WALL_TIME_HOURS} h, {NUM_CPUS} CPU(s)")
    print(f"Logs    : {log_dir}")

    with ClusterSubmitter(**kwargs) as submitter:
        submitter.add(command=command, description=f"Running {script_path.name}")

    print("Submitted.")
    if CLUSTER == "nbi":
        print("Check status: squeue -u $USER")
    else:
        print("Check status: condor_q")


if __name__ == "__main__":
    main()
