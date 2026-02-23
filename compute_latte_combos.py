import numpy as np
import time, json
from itertools import product
import warnings, importlib
import subprocess
import io, re
import selectors
import sys

warnings.simplefilter(action="ignore", category=FutureWarning)
import PBcombos as pbc
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
            # match = re.search(r"Left =\s*(\d+),", text)
            # if match:
            # number = int(match.group(1))
            # print(f"LEFT: {number} in -> ")
            # assert number > 347, f"LEFT: {number} in -> " + text
            # num = text.split("Left =")[1].split(",")[0]
            # num = int(num)
            # assert num < 120

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
    boundaries = {
        "Aerosol effect": 1,
        "CO2 effect": 1,
        "Biodiv. incl. climate effect": 1,
        "Biogeochem. effect": 1,
        "Freshwater effect": 1,
        # "Ocean acid. effect": 1,
        "Land-use effect": 1,
    }
    # integrate --valuation=volume --cone-decompose ./hrep/combo_latte_all_params/pb_0_1_0_0_1_1.hrep.latte

    # Create a generator of lists of indicators whether a specific boundary should be activated
    combinations = product([0, 1], repeat=6)

    tech_param_version = "combo_latte_all_params_me"

    results = {}
    hrep_files = []
    results_path = Path() / "results" / tech_param_version
    results_path.mkdir(exist_ok=True)
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
            pbc.gen_hrep_file_new(
                tech_params,
                boundaries,
                dir=file_dir,
                exclude_non_active_boundaries=False,
            )
        
        # gt_results_path = Path() / "results" / "combo_latte_gt"
        # for gtfile in gt_results_path.iterdir():
        #     if f"pb_{file_id}.hrep.latte.txt" == gtfile.name:
        #         with open(gtfile, "r") as gtf:
        #             gtvolres = gtf.read().split("|")
        #         # Feasible: "1_1_0_0_0_0", "0_1_0_1_0_0", "0_1_0_0_1_0", "0_1_0_0_0_1", "0_0_0_1_1_0", "0_0_0_0_1_1"
        #         if (
        #             len(gtvolres) > 1
        #             and float(gtvolres[1]) < 1
        #             and file_id not in ["1_0_0_0_0_1", "1_1_0_0_0_0"]
        #         ):
        #             hrep_files.append(str(file_dir))
        #         elif file_id not in [
        #             "1_1_0_1_1_1",
        #             "1_1_0_1_1_0",
        #             "1_1_0_1_0_1",
        #             "1_0_0_0_0_1",
        #             "1_1_0_1_0_0",
        #             "1_1_0_0_1_1",
        #             "1_1_0_0_1_0",
        #             "1_1_0_0_0_1",
        #             "1_1_0_0_0_0",
        #             "1_0_0_1_1_1",
        #             "1_0_0_1_1_0",
        #             "1_0_0_1_0_1",
        #             "1_0_0_1_0_0",
        #             "1_0_0_0_1_1",
        #             "1_0_0_0_1_0",
        #             "0_1_0_1_1_1",
        #             "0_1_0_1_1_0",
        #             "0_1_0_1_0_1",
        #             "0_1_0_1_0_0",
        #             "0_1_0_0_1_1",
        #             "0_1_0_0_1_0",
        #             "0_1_0_0_0_1",
        #             "0_0_0_1_1_1",
        #             "0_0_0_1_1_0",
        #             "0_0_0_1_0_1",
        #             "0_0_0_1_0_0",
        #             "0_0_0_0_1_1",
        #         ]:
        #             hrep_files.append(str(file_dir))
        # print(tuple([int(ii) for ii in file_id.split("_")]))
        # if tuple([int(ii) for ii in file_id.split("_")]) not in [
        #     (1, 1, 1, 1, 1, 1),
        #     (0, 1, 1, 1, 1, 1),
        #     (1, 0, 1, 1, 1, 1),
        #     (1, 1, 1, 0, 1, 1),
        #     (1, 1, 1, 1, 0, 1),
        #     (1, 1, 1, 1, 1, 0),
        #     (0, 0, 1, 1, 1, 1),
        #     (0, 1, 1, 0, 1, 1),
        #     (0, 1, 1, 1, 0, 1),
        #     (0, 1, 1, 1, 1, 0),
        #     (1, 0, 1, 0, 1, 1),
        #     (1, 0, 1, 1, 0, 1),
        #     (1, 0, 1, 1, 1, 0),
        #     (1, 1, 1, 0, 0, 1),
        #     (1, 1, 1, 0, 1, 0),
        #     (1, 1, 1, 1, 0, 0),
        #     (0, 0, 1, 0, 1, 1),
        #     (0, 0, 1, 1, 0, 1),
        #     (0, 0, 1, 1, 1, 0),
        #     (0, 1, 1, 0, 0, 1),
        #     (0, 1, 1, 0, 1, 0),
        #     (0, 1, 1, 1, 0, 0),
        #     (1, 0, 1, 0, 0, 1),
        #     (1, 0, 1, 0, 1, 0),
        #     (1, 0, 1, 1, 0, 0),
        #     (1, 1, 1, 0, 0, 0),
        #     (0, 0, 1, 0, 0, 1),
        #     (0, 0, 1, 0, 1, 0),
        #     (0, 0, 1, 1, 0, 0),
        #     (0, 1, 1, 0, 0, 0),
        #     (1, 0, 1, 0, 0, 0),
        #     (0, 0, 1, 0, 0, 0),
        # ] and file_id not in [
        #     "1_1_0_1_1_1",
        #     "1_1_0_1_1_0",
        #     "1_1_0_1_0_1",
        #     "1_1_0_1_0_0",
        #     "1_1_0_0_1_1",
        #     "1_1_0_0_1_0",
        #     "1_1_0_0_0_1",
        #     "1_1_0_0_0_0",
        #     "1_0_0_1_1_1",
        #     "1_0_0_1_1_0",
        #     "1_0_0_1_0_1",
        #     "1_0_0_1_0_0",
        #     "1_0_0_0_1_1",
        #     "1_0_0_0_1_0",
        #     "1_0_0_0_0_1",
        #     "1_0_0_0_0_0",
        #     "0_1_0_1_1_1",
        #     "0_1_0_1_1_0",
        #     "0_1_0_1_0_1",
        #     "0_1_0_1_0_0",
        #     "0_1_0_0_1_1",
        #     "0_1_0_0_1_0",
        #     "0_1_0_0_0_1",
        #     "0_1_0_0_0_0",
        #     "0_0_0_1_1_1",
        #     "0_0_0_1_1_0",
        #     "0_0_0_1_0_1",
        #     "0_0_0_1_0_0",
        #     "0_0_0_0_1_1",
        #     "0_0_0_0_1_0",
        #     "0_0_0_0_0_1",
        # ]:
        if f"pb_{file_id}.hrep.latte.txt" not in compute_latte_combos:
            hrep_files.append(str(file_dir))
        else:
            print("Already proceesded: ", file_id)

    # results[str(combo)] = answer
    # with open("./results/compute_latte_combos.py", "w") as f:
    #     f.write(json.dumps(results))

    commands = [
        f"integrate --valuation=volume --cone-decompose ./{hrep}" for hrep in hrep_files
    ]
    for cmd in commands:
        print(cmd)

    # commands = [
    #     f"integrate --valuation=volume --cone-decompose ./hrep/{tech_param_version}/pb_1_1_1_1_0_1.hrep.latte"
    # ]
    # integrate --valuation=volume --cone-decompose ./hrep/combo_latte_all_params/pb_0_0_1_0_1_1.hrep.latte
    integrate --valuation=volume --cone-decompose ./latte/pbtech/pb.hrep.latte
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
                        # f.write(f"Command: {command} || Result: {answer}\n")
                if not answer_found:
                    print(f"Command: {command} || Failed!! \n")
                    # f.write(f"Command: {command} || Failed!! \n")

            except Exception as e:
                print(f" Error: {e}. For {command}")
                f.write(f" Error: {e}. For {command}")
                # f.write(f" Error: {e}\n")

# PARALLELIZE CODE
# if 1 == 2:
#     with ProcessPoolExecutor(max_workers=4) as executor:
#         commands = [
#             f"integrate --valuation=volume --cone-decompose ./{hrep}"
#             for hrep in hrep_files
#         ]
#         futures = [executor.submit(run_subprocess, command) for command in commands]
#         # with open("./results/compute_latte_combos.json", "w") as f:
#         for future in as_completed(futures):
#             try:
#                 command, output = future.result()
#                 answer_found = False
#                 for row in output.split("\n"):
#                     if "Decimal: " in row:
#                         answer = row.split("Decimal: ")[-1]
#                         answer = float(answer)
#                         answer_found = True
#                         print(f"Command: {command} || Result: {answer}\n")
#                         filename = command.split("/hrep/")[-1]
#                         with open(
#                             f"./results/combo_latte_combos/{filename}.txt", "w"
#                         ) as f:
#                             f.write(f"{answer}")
#                         # f.write(f"Command: {command} || Result: {answer}\n")
#                 if not answer_found:
#                     print(f"Command: {command} || Failed!! \n")
#                     # f.write(f"Command: {command} || Failed!! \n")

#             except Exception as e:
#                 print(f" Error: {e}\n")
#                 # f.write(f" Error: {e}\n")
# else:
