import numpy as np
import time, json
from itertools import product
import warnings, importlib
import subprocess
import io, re
import selectors
import sys

warnings.simplefilter(action="ignore", category=FutureWarning)
import Results_and_figures as rf
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from subprocess import Popen, PIPE


def capture_subprocess_output(subprocess_args):
    # Start subprocess
    # bufsize = 1 means output is line buffered
    # universal_newlines = True is required for line buffering
    process = subprocess.Popen(
        subprocess_args,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    # Create callback function for process output
    buf = io.StringIO()

    def handle_output(stream, mask):
        # Because the process' output is line buffered, there's only ever one
        # line to read when this function is called
        line = stream.readline()
        buf.write(line)
        sys.stdout.write(line)

    # Register callback for an "available for read" event from subprocess' stdout stream
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, handle_output)

    # Loop until subprocess is terminated
    while process.poll() is None:
        # Wait for events and handle them with their registered callbacks
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    # Get process return code
    return_code = process.wait()
    selector.close()

    success = return_code == 0

    # Store buffered output
    output = buf.getvalue()
    buf.close()

    return subprocess_args, output


def run_subprocess_print(command):
    output = ""

    with Popen(command.split(" "), stdout=PIPE) as p:

        while True:
            text = p.stdout.read1().decode("utf-8")
            output += text + " \n"

            print(text, end="", flush=True)

            if "Total time:" in text:
                break
    return command, output


def run_subprocess(command):
    print("Running: ", command)
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        return command, result.stdout
    except subprocess.CalledProcessError as e:
        return command, f"Error: {e}"


if __name__ == "__main__":
    """
    Computes polyhedra volumes for all possible boundary constraints

    Run using command:
    >>> python compute_latte_combos.py combo_latte_all_params
    which computes the volumes for all combinations of non-mutually exclusive boundary constraints for the case of general tecnological change.
    or 
    >>> python compute_latte_combos.py combo_latte_gt
    which computes the volumes for all combinations of non-mutually exclusive boundary constraints for the case of green tecnological change.
    """
    assert sys.argv[1] in ["combo_latte_all_params", "combo_latte_gt"]
    tech_param_version = sys.argv[1]

    tech_params = {
        ("A_LA", "Land use efficiency in agriculture"): 1,
        ("A_EpsA", "Energy efficiency agriculture"): 1,
        ("A_P", "Fertilizer efficiency in agriculture"): 1,
        ("A_W", "Water efficiency in agriculture"): 1,
        ("A_MA", "Other inputs efficiency in agriculture"): 1,
        ("P_EP", "Fossil fuel efficiency in fertilizer prod."): 1,
        ("P_Pho", "Phosphor efficiency in fertilizer prod."): 1,
        ("P_MP", "Other inputs efficiency in fertilizer prod."): 1,
        ("Eps_AB", "Biofuel efficiency in energy service prod."): 1,
        ("Eps_EEps", "Fossil fuel efficiency in energy service prod."): 1,
        ("Eps_R", "Renewable efficiency in energy service prod."): 1,
        ("Y_EpsY", "Energy services efficiency in manufacturing"): 1,
        ("Y_MY", "Other inputs efficiency in manufacturing"): 1,
        ("Fi_EFi", "Fossil fuels efficiency in fisheries"): 1,
        ("Fi_MFi", "Other inputs efficiency in fisheries"): 1,
        ("T_LT", "Land use efficiency in timber prod."): 1,
        ("T_MT", "Other inputs efficiency in timber prod."): 1,
    }

    if tech_param_version == "combo_latte_gt":
        tech_params[("A_MA", "Other inputs efficiency in agriculture")] = 0
        tech_params[("P_MP", "Other inputs efficiency in fertilizer prod.")] = 0
        tech_params[("Y_MY", "Other inputs efficiency in manufacturing")] = 0
        tech_params[("Fi_MFi", "Other inputs efficiency in fisheries")] = 0
        tech_params[("T_MT", "Other inputs efficiency in timber prod.")] = 0


    boundaries = {
        "Aerosol effect": 1,
        "CO2 effect": 1,
        "Biodiv. incl. climate effect": 1,
        "Biogeochem. effect": 1,
        "Freshwater effect": 1,
        "Land-use effect": 1,
    }


    # Create a generator of lists of indicators whether a specific boundary should be activated
    combinations = product([0, 1], repeat=6)

    results = {}
    hrep_files = []
    results_path = Path() / "results" / tech_param_version
    results_path.mkdir(exist_ok=True, parents=True)
    compute_latte_combos = [
        file.name
        for file in results_path.iterdir()
        if not file.is_dir() or file.suffix != ".txt"
    ]
    print(compute_latte_combos)
    for ii, combo in enumerate(combinations):
        if sum(combo) == 0:
            continue
        boundaries = {k: combo[idx] for idx, k in enumerate(boundaries)}
        file_id = str(combo).replace(", ", "_")[1:-1]
        file_dir = Path(f"./hrep/{tech_param_version}/pb_{file_id}.hrep.latte")
        file_dir.parent.mkdir(exist_ok=True)
        if not file_dir.exists():
            rf.gen_hrep_file_new(
                tech_params,
                boundaries,
                dir=file_dir,
                exclude_non_active_boundaries=False,
            )
        

        if f"pb_{file_id}.hrep.latte.txt" not in compute_latte_combos:
            hrep_files.append(str(file_dir))
        else:
            print("Already proceesed: ", file_id)

    commands = [
        f"integrate --valuation=volume --cone-decompose ./{hrep}" for hrep in hrep_files
    ]
    for cmd in commands:
        print("Preparing to run command: ", cmd)

    for command in sorted(commands, reverse=True):
        with open(results_path / f"failed_commands.txt", "w") as ff:
            try:
                with open(results_path / f"running_command.txt", "w") as f:
                    f.write(f"{command}")
                start_time = time.time()
                command, output = run_subprocess_print(command)
                end_time = time.time()
                answer_found = False
                for row in output.split("\n"):
                    if "Decimal: " in row:
                        answer = row.split("Decimal: ")[-1]
                        answer = float(answer)
                        answer_found = True
                        print(" ")
                        print("--------------------------")
                        print(f"Command: {command} || Result: {answer}\n")
                        filename = command.split(f"/{tech_param_version}/")[-1]
                        with open(results_path / f"{filename}.txt", "w") as f:
                            f.write(f"{answer}|{end_time-start_time}")

                if not answer_found:
                    print(f"Command: {command} || Failed!! \n")

            except Exception as e:
                print(f" Error: {e}. For {command}")
                f.write(f" Error: {e}. For {command}")


