from pathlib import Path
import numpy as np
from collections import defaultdict
from py_markdown_table.markdown_table import markdown_table
import csv
from decimal import Decimal
import random
from itertools import product
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager

plt.rcdefaults()
# Use the newly integrated Roboto font family for all text.
plt.rc("font", family="sans-serif")
plt.rcParams["figure.figsize"] = (8, 4)


def auto_gen_non_me_volumes():

    result_path = Path("./results/combo_latte_all_params")
    num_of_elements = 6
    possible_combos = [p for p in product([0, 1], repeat=num_of_elements)]
    combos = {}
    combo_volume_store = {}  # Non me volumes
    combo_me_volume_store = {}  # ME volumes

    for file in result_path.iterdir():
        if not file.name.startswith("pb_"):
            continue
        combo = tuple([int(c[0:1]) for c in file.name[3:-14].split("_")])
        with open(file, "r") as f:
            combo_volume_store[combo] = float(f.read().split("|")[0])
        # combo_sum = sum(combo)
        # if combo_sum in combos:
        #     combos[combo_sum].append((file, combo))
        # else:
        #     combos[combo_sum] = [(file, combo)]

        # combos.append(combo.reshape(1, 6))

    # print((0, 1, 0, 1, 1, 1), combo_volume_store[(0, 1, 0, 1, 1, 1)])
    subvolume_combos = []
    for level in range(6, 0, -1):
        level_combos = [p for p in possible_combos if sum(p) == level]
        for level_combo in level_combos:
            if not level_combo in combo_volume_store:
                continue
            # if level_combo == (1, 1, 0, 1, 1, 1):
            #     continue
            me_exclude_combos = [
                c
                for c in product([0, 1], repeat=num_of_elements)
                if np.array(level_combo).dot(c) == level and level_combo != c
            ]

            combo_me_volume_store[level_combo] = combo_volume_store[level_combo]
            for me_exclued_combo in me_exclude_combos:
                if me_exclued_combo in combo_me_volume_store:
                    combo_me_volume_store[level_combo] -= combo_me_volume_store[
                        me_exclued_combo
                    ]
                else:
                    del combo_me_volume_store[level_combo]
                    break

            if (0, 0, 1, 0, 1, 1) == level_combo:
                print("u:", combo_volume_store[level_combo])

                print(level, level_combo)
                print(me_exclude_combos)

            if (0, 1, 0, 0, 1, 1) == level_combo:
                print("uu:", combo_volume_store[level_combo])
                print(me_exclude_combos)
            # print("---")
        # if level < 5:
        #     break

    cl = []
    for cc, val in combo_volume_store.items():
        print(cc, val, combo_me_volume_store.get(cc))
        cl.append(cc)
    print(cl)

    print(len(combo_me_volume_store), sum(combo_me_volume_store.values()))
    print(len(combo_volume_store))

    # for pc in possible_combos:
    #     sub_variations = product([0, 1], repeat=num_of_elements - sum(pc))
    #     for variation in sub_variations:
    #         variation = iter(variation)
    #         subvolume_combos.append(
    #             tuple(
    #                 [
    #                     val if val == 1 else next(variation)
    #                     for ii, val in enumerate(pc)
    #                 ]
    #             )
    #         )
    #     print(pc)
    #     print(subvolume_combos)
    # combos = np.concatenate(combos, axis=0)

    # combo_me_volume_store = {}  # ME volumes
    # for combo_sum in range(6, 0, -1):
    #     for combo, vol in combo_volume_store.items():#combos[combo_sum]:
    #         with open(file, "r") as f:
    #             volume = float(f.read().split("|")[0])
    #         me_volume = volume
    #         for k, v in combo_me_volume_store.items():
    #             if np.array(k).dot(combo) == np.sum(combo):
    #                 me_volume -= v
    #         # print(
    #         #     combo_sum,
    #         #     file.name,
    #         #     combo,
    #         #     volume,
    #         #     " me_volume:",
    #         #     me_volume,
    #         # )
    #         combo_me_volume_store[tuple(combo)] = me_volume

    ###########################################
    # print(len(combo_me_volume_store))
    # print(len(combo_volume_store))

    # for pc in possible_combos:
    #     if not pc in combo_volume_store:
    #         print("Missing combo: ", pc)
    #     if not pc in combo_me_volume_store:
    #         print("Missing me combo: ", pc)

    # # Missing 2 indices derivable volumes

    # for pc in possible_combos:
    #     if sum(pc) != 3:
    #         continue

    #     subvolume_combos = []
    #     sub_variations = product([0, 1], repeat=3)
    #     for variation in sub_variations:
    #         variation = iter(variation)
    #         subvolume_combos.append(
    #             tuple(
    #                 [val if val == 1 else next(variation) for ii, val in enumerate(pc)]
    #             )
    #         )
    #     subvolume_combos.append(pc)
    #     print("Checking: ", pc)
    #     if pc in combo_volume_store:
    #         available_me_values = sum(
    #             [svc in combo_me_volume_store for svc in subvolume_combos]
    #         )
    #         available_values = sum(
    #             [svc in combo_volume_store for svc in subvolume_combos]
    #         )
    #         print(
    #             f"Found ME columes: {available_me_values}/{len(subvolume_combos)}  ",
    #             (1, 1, 0, 1, 1, 1) in subvolume_combos,
    #         )
    #########################################

    # print(subvolume_combos)

    # hrep_path = Path("./hrep/combo_latte_gt")
    # for file in hrep_path.iterdir():
    #     if not file.name.startswith("pb_"):
    #         continue

    #     combo = tuple([int(c[0:1]) for c in file.name[3:-11].split("_")])
    #     if sum(combo) != 4:
    #         continue
    #     volume = 0
    #     if combo in combo_me_volume_store:
    #         volume = combo_me_volume_store[combo]
    #     else:
    #         continue
    #     if combo == (0, 1, 1, 0, 0, 1):
    #         print(combo, volume)
    #     quit = False
    #     potential_combos = []
    #     for idx, val in enumerate(combo):
    #         if val == 0:
    #             potential_combos.append(
    #                 tuple([c if ii != idx else 1 for ii, c in enumerate(combo)])
    #             )
    #     if combo_volume_store.get(potential_combos[0]) and combo_me_volume_store.get(
    #         potential_combos[1]
    #     ):
    #         volume += combo_volume_store.get(
    #             potential_combos[0]
    #         ) + combo_me_volume_store.get(potential_combos[1])
    #     elif combo_volume_store.get(potential_combos[1]) and combo_me_volume_store.get(
    #         potential_combos[0]
    #     ):
    #         volume += combo_volume_store.get(
    #             potential_combos[0]
    #         ) + combo_me_volume_store.get(potential_combos[1])
    #     else:
    #         print(combo, " not derivable.")
    #         continue

    #     # if quit == True:
    #     #     continue
    #     # else:
    #     str_combo = "_".join([str(cc) for cc in combo])
    #     try:
    #         with open(result_path / f"pb_{str_combo}.hrep.latte.txt", "r") as f:
    #             stored_non_me_vol = f.read().split("|")[0]
    #     except Exception as e:
    #         stored_non_me_vol = -1
    #         print(e)

    #     print(
    #         combo,
    #         " found with derived volume = ",
    #         volume,
    #         " , Computed non ME volume: ",
    #         stored_non_me_vol,
    #     )


def vrep_analys():
    """Computes feasible parameter space from Vrep files"""
    result_path = Path(
        "./results/combo_latte_gt"
    )  # Note: when  results path is combo_latte_gt we need to comment out other inputs in tech_params below
    with open(result_path / "pb.vrep.latte", "r") as f:
        prev_vals, max_vals = None, None
        for idx, line in enumerate(f.readlines()):
            if idx > 0:
                vals = [
                    (
                        float(v.split("/")[0]) / float(v.split("/")[1])
                        if "/" in v
                        else int(v)
                    )
                    for v in line.split(" ")
                ]

                if prev_vals:
                    max_vals = [
                        max(val_pair) for val_pair in zip(max_vals or vals, prev_vals)
                    ]
                prev_vals = vals
    print("feasible parameter space: ", np.prod(np.array(max_vals[1:])))

    fig, ax = plt.subplots()
    tech_params = {
        ("A_LA", "Land use efficiency in agriculture"): 1,
        ("A_EpsA", "Energy efficiency agriculture"): 1,
        ("A_P", "Fertilizer efficiency in agriculture"): 1,
        ("A_W", "Water efficiency in agriculture"): 1,
        # ("A_MA", "Other inputs efficiency in agriculture"): 1,
        ("P_EP", "Fossil fuel efficiency in fertilizer prod."): 1,
        ("P_Pho", "Phosphor efficiency in fertilizer prod."): 1,
        # ("P_MP", "Other inputs efficiency in fertilizer prod."): 1,
        ("Eps_AB", "Biofuel efficiency in energy service prod."): 1,
        ("Eps_EEps", "Fossil fuel efficiency in energy service prod."): 1,
        ("Eps_R", "Renewable efficiency in energy service prod."): 1,
        ("Y_EpsY", "Energy services efficiency in manufacturing"): 1,
        # ("Y_MY", "Other inputs efficiency in manufacturing"): 1,
        ("Fi_EFi", "Fossil fuels efficiency in fisheries"): 1,
        # ("Fi_MFi", "Other inputs efficiency in fisheries"): 1,
        ("T_LT", "Land use efficiency in timber prod."): 1,
        # ("T_MT", "Other inputs efficiency in timber prod."): 1,
    }
    tech_params = {k: max_vals[ii] for ii, k in enumerate(tech_params.keys(), start=1)}
    df = pd.DataFrame.from_dict(
        {k[1]: v for k, v in tech_params.items() if v}, orient="index"
    ).sort_index(ascending=False)
    df.columns = ["space"]

    # Save the chart so we can loop through the bars below.
    bars = ax.barh(
        df.index,
        df["space"],
        height=0.4,
        align="center",
    )

    # Axis formatting.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.tick_params(bottom=False, left=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#EEEEEE")
    ax.xaxis.grid(False)

    # Add text annotations to the top of the bars.
    bar_color = bars[0].get_facecolor()
    vol = 1
    for bar in bars:
        vol = vol * bar.get_width()
        # print(bar.get_y(), bar.get_x(), bar.get_width())
        ax.text(
            bar.get_width() + 0.04,
            bar.get_y(),
            round(bar.get_width(), 2),
            horizontalalignment="center",
            color=bar_color,
            weight="normal",
        )

    # Add labels and a title.
    ax.set_xlabel(
        "",
        labelpad=15,
        color="#333333",
    )
    ax.set_ylabel(" ", labelpad=15, color="#333333")
    # ax.set_title("Share of 1 Percent change", pad=15, color="#333333", weight="bold")
    print(vol)
    fig.tight_layout()
    fig.savefig(result_path / "percent_change.png")
    # print("ddd")


def compute_boundary_solved_tables():
    """Compute tables showing the number of boundaries solved and their probabilities"""
    result_path = Path("./results/combo_latte_gt")
    combo_volume_store = {}  # Non me volumes
    combo_me_volume_store = {}  # ME volumes
    num_of_elements = 6
    possible_combos = [p for p in product([0, 1], repeat=num_of_elements)]

    for file in result_path.iterdir():
        if not file.name.startswith("pb_"):
            continue
        combo = tuple([int(c[0:1]) for c in file.name[3:-14].split("_")])
        with open(file, "r") as f:
            combo_volume_store[combo] = float(f.read().split("|")[0])

    print("Number of UNconditional volumes found: ", len(combo_volume_store))
    # print((0, 1, 0, 1, 1, 1), combo_volume_store[(0, 1, 0, 1, 1, 1)])
    subvolume_combos = []
    for level in range(6, 0, -1):
        level_combos = [p for p in possible_combos if sum(p) == level]
        for level_combo in level_combos:
            if not level_combo in combo_volume_store:
                print(level_combo, " not found!")
                continue
            # if level_combo == (1, 1, 0, 1, 1, 1):
            #     continue
            combo_me_volume_store[level_combo] = combo_volume_store[level_combo]
            if level < 6:
                me_exclude_combos = [
                    c
                    for c in product([0, 1], repeat=num_of_elements)
                    if np.array(level_combo).dot(c) == level and level_combo != c
                ]
                for me_exclued_combo in me_exclude_combos:

                    if me_exclued_combo in combo_me_volume_store:
                        combo_me_volume_store[level_combo] -= combo_me_volume_store[
                            me_exclued_combo
                        ]
                    else:
                        del combo_me_volume_store[level_combo]
                        break

    print("Number of conditional volumes found: ", len(combo_me_volume_store))
    # Generate CSV table
    prob = {}
    for combo, me_volume in combo_me_volume_store.items():
        num_solved = sum(combo)

        # for _ in range(combo[1] + 1):
        #    num_solved += combo[1]

        if num_solved in prob:
            prob[num_solved]["all"] += me_volume
            prob[num_solved]["Aerosol effect"] += me_volume if combo[0] == 1 else 0
            prob[num_solved]["CO2 effect"] += me_volume if combo[1] == 1 else 0
            prob[num_solved]["Biodiv. incl. climate effect"] += (
                me_volume if combo[2] == 1 else 0
            )
            prob[num_solved]["Biogeochem. effect"] += me_volume if combo[3] == 1 else 0
            prob[num_solved]["Freshwater effect"] += me_volume if combo[4] == 1 else 0
            prob[num_solved]["Ocean acid. effect"] += me_volume if combo[1] == 1 else 0
            prob[num_solved]["Land-use effect"] += me_volume if combo[5] == 1 else 0

        else:
            prob[num_solved] = {
                "all": me_volume,
                "Aerosol effect": me_volume if combo[0] == 1 else 0,
                "CO2 effect": me_volume if combo[1] == 1 else 0,
                "Biodiv. incl. climate effect": me_volume if combo[2] == 1 else 0,
                "Biogeochem. effect": me_volume if combo[3] == 1 else 0,
                "Freshwater effect": me_volume if combo[4] == 1 else 0,
                "Ocean acid. effect": me_volume if combo[1] == 1 else 0,
                "Land-use effect": me_volume if combo[5] == 1 else 0,
            }

    prob[0] = {k: 0 for k, v in prob[1].items()}
    prob[0]["all"] = 1 - sum([v["all"] for _, v in prob.items()])

    prob_to_csv, prob_shares_to_csv = [], []
    for cnt, vals in prob.items():
        str_vals = {
            "Boundaries improved": cnt,
        }
        str_share_vals = str_vals.copy()
        for k, v in vals.items():
            if k != "all":
                value = 100 * v / vals["all"]
            else:
                value = v
            str_vals[k] = f"{v:.4E}"
            str_share_vals[k] = f"{value:.4E}"

        prob_to_csv.append(str_vals)
        prob_shares_to_csv.append(str_share_vals)

    keys = prob_to_csv[0].keys()
    with open(
        result_path / "num_boundaries_solved_probs_table.csv", "w", newline=""
    ) as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(prob_to_csv)

    with open(
        result_path / "num_boundaries_solved_probs_share_table.csv", "w", newline=""
    ) as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(prob_shares_to_csv)


if __name__ == "__main__":
    # vrep_analys()
    # auto_gen_non_me_volumes()
    compute_boundary_solved_tables()
