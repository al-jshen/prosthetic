import toml
import munch
import argparse
import numpy as np
import os
from subprocess import Popen, PIPE, DEVNULL
from tqdm.auto import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, default="config.toml", help="path to config file"
    )
    parser.add_argument(
        "--sweep_dir", type=str, default="./", help="path to save sweep results"
    )
    parser.add_argument(
        "--n_jobs", type=int, default=4, help="number of jobs to run in parallel"
    )
    args = parser.parse_args()
    config = munch.munchify(toml.load(args.config))
    total_variations = 1
    grid_indices = []
    for k in config.hyperparameters:
        total_variations *= len(config[k])
        grid_indices.append(np.arange(len(config[k])))
    grid_indices = np.meshgrid(*grid_indices, indexing="ij")
    grid_indices = np.stack(grid_indices, axis=-1).reshape(
        -1, len(config.hyperparameters)
    )

    # create directory for results
    if not os.path.exists(args.sweep_dir + "hypersweep/"):
        os.makedirs(args.sweep_dir + "hypersweep/")

    commands = []

    for i in range(total_variations):
        config_copy = config.copy()
        variation = grid_indices[i]
        for j, k in enumerate(config.hyperparameters):
            config_copy[k] = config[k][variation[j]]

        # save config
        with open(args.sweep_dir + "hypersweep/config_" + str(i) + ".toml", "w") as f:
            toml.dump(config_copy, f)

        # run experiment
        command = (
            "python3 "
            + "solve.py --config "
            + args.sweep_dir
            + "hypersweep/config_"
            + str(i)
            + ".toml"
        )

        commands.append(command)

    # if output file exists, delete it
    if os.path.exists(args.sweep_dir + "hypersweep/outputs.txt"):
        os.remove(args.sweep_dir + "hypersweep/outputs.txt")

    # run experiments in parallel, n_jobs at a time
    for i in tqdm(range(0, len(commands), args.n_jobs)):
        processes = [
            Popen(cmd, shell=True, stdout=PIPE, stderr=DEVNULL)
            for cmd in commands[i : i + args.n_jobs]
        ]
        for p in processes:
            p.wait()

        outputs = [p.stdout.read().decode("utf-8") for p in processes]
        # prepend output with variation number
        outputs = [
            f"Variation {i+j+1}/{total_variations}\n" + outputs[j]
            for j in range(len(outputs))
        ]
        # save outputs to file
        with open(args.sweep_dir + "hypersweep/outputs.txt", "a") as f:
            f.writelines(outputs)
