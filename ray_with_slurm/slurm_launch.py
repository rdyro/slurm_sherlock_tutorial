description = "Launch a job on slurm using ray."
example_usage = (
    "Example usage: python3 slurm-launch.py --script job.py --script-args "
    + "'rllib train --run PPO --env CartPole-v0'"
)

import argparse, subprocess, sys, time, os
from pathlib import Path

template_file = Path(__file__).absolute().parent / "templates" / "template_job.sh"
JOB_NAME = "${JOB_NAME}"
EXP_NAME = "${EXP_NAME}"
OUTPUT_NAME = "${OUTPUT_NAME}"
NUM_NODES = "${NUM_NODES}"
NUM_CPU = "${NUM_CPU}"
NUM_GPUS_PER_NODE = "${NUM_GPUS_PER_NODE}"
NUM_GPUS_TOTAL = "${NUM_GPUS_TOTAL}"
PARTITION_OPTION = "${PARTITION_OPTION}"
SCRIPT_PLACEHOLDER = "${SCRIPT_PLACEHOLDER}"
SCRIPT_ARGS_PLACEHOLDER = "${SCRIPT_ARGS_PLACEHOLDER}"
LOAD_ENV = "${LOAD_ENV}"
SRUN_GPU_HEADER = "${SRUN_GPU_HEADER}"

if __name__ == "__main__":
    # parse arguments #########################################
    parser = argparse.ArgumentParser(description=description, epilog=example_usage)
    parser.add_argument(
        "--exp-name",
        "--name",
        type=str,
        default="my_experiment",
        help="The job name and path to logging file (exp_name.log).",
    )
    parser.add_argument("--num-nodes", "-n", type=int, default=1, help="Number of nodes to use.")
    parser.add_argument(
        "--num-gpus",
        type=int,
        default=0,
        help="Number of GPUs to use for each node. (Default: 0)",
    )
    parser.add_argument(
        "--num-cpus",
        type=int,
        default=2,
        help="Number of CPUs to use for each node. (Default: 2)",
    )
    parser.add_argument(
        "--load-env",
        "-e",
        type=str,
        default=(Path(__file__).absolute().parent / "env_load.sh"),
        help="The script to load your environment (e.g., 'module load cuda/10.1')",
    )
    parser.add_argument(
        "--script",
        "-s",
        type=str,
        required=True,
        help="The script you wish to execute. For example: "
        " --script 'test.py'. "
        "Note that the script must be a path/file.",
    )
    parser.add_argument(
        "--script-args",
        "-a",
        type=str,
        default="",
        help="The script arguments you wish to add. For example: "
        " --script-args '--lr 1e-3 --logdir runs'. "
        "Note the quotes.",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Whether to only generate the job file (in `./jobs`), without running it. Dry run."
    )
    args = parser.parse_args()

    # parse arguments #########################################
    job_name = f"{args.exp_name}_{time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime())}"
    partition_option = "#SBATCH --partition=gpu" if args.num_gpus > 0 else "#"
    if args.num_gpus > 0:
        gpus_per_node = "#SBATCH --gpus-per-node=%d" % args.num_gpus
        gpus_total = "#SBATCH --gpus=%d" % (args.num_gpus * args.num_nodes)
        srun_gpu_header = "-p gpu -G %d" % args.num_gpus
    else:
        gpus_per_node = "#"
        gpus_total = "#"
        srun_gpu_header = ""
    load_env = ("source %s" % args.load_env) if args.load_env else ""

    # ===== Modified the template script =====
    with open(template_file, "r") as f:
        text = f.read()
    text = text.replace(JOB_NAME, job_name)
    text = text.replace(
        OUTPUT_NAME,
        str((Path(__file__).parent / "logs" / (job_name + ".log")).absolute()),
    )
    text = text.replace(NUM_NODES, str(args.num_nodes))
    text = text.replace(NUM_GPUS_PER_NODE, str(gpus_per_node))
    text = text.replace(NUM_GPUS_TOTAL, str(gpus_total))
    text = text.replace(SRUN_GPU_HEADER, str(srun_gpu_header))
    text = text.replace(EXP_NAME, str(args.exp_name))
    text = text.replace(NUM_CPU, str(args.num_cpus))
    text = text.replace(PARTITION_OPTION, partition_option)
    text = text.replace(SCRIPT_PLACEHOLDER, str(Path(args.script).absolute()))
    text = text.replace(SCRIPT_ARGS_PLACEHOLDER, str(args.script_args))
    text = text.replace(LOAD_ENV, load_env)
    text = text.replace(
        "# THIS FILE IS A TEMPLATE AND IT SHOULD NOT BE DEPLOYED TO " "PRODUCTION!",
        "# THIS FILE IS MODIFIED AUTOMATICALLY FROM TEMPLATE AND SHOULD BE " "RUNNABLE!",
    )

    # ===== Save the script =====
    script_file = Path(__file__).parent / "jobs" / f"{job_name}.sh"
    script_file.parent.mkdir(exist_ok=True, parents=True)
    script_file.write_text(text)

    # ===== Submit the job =====
    if not args.dry:
        print("Starting to submit job!")
        subprocess.Popen(["sbatch", script_file])
        print(f"Job submitted! Script file is at: <{script_file}>. Log file is at: <{job_name}.log>.")
    sys.exit(0)