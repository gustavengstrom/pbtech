# import necessary packages
import multiprocessing as mp
import numpy as np
import math, time
import pandas as pd
import csv
import re, importlib
import subprocess
from tqdm import tqdm
import os, sys, json
import JuPyMake
from pathlib import Path
from itertools import product
from itertools import batched
from model_code import params, model  # Load parameters and model implementation.

param_list = list(params.df_typing_formatting.T.to_dict().values())
model_params = {row["keys"]: row["values"] for row in param_list}
sm = model.SolveModel(model_params)

df_carbontax_quantities, df_carbontax_prices = sm.gen_results(
    robust_check=False, biofuel_tax=0
)

general_tech_params = {
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
green_tech_params = {
    ("A_LA", "Land use efficiency in agriculture"): 1,
    ("A_EpsA", "Energy efficiency agriculture"): 1,
    ("A_P", "Fertilizer efficiency in agriculture"): 1,
    ("A_W", "Water efficiency in agriculture"): 1,
    ("A_MA", "Other inputs efficiency in agriculture"): 0,
    ("P_EP", "Fossil fuel efficiency in fertilizer prod."): 1,
    ("P_Pho", "Phosphor efficiency in fertilizer prod."): 1,
    ("P_MP", "Other inputs efficiency in fertilizer prod."): 0,
    ("Eps_AB", "Biofuel efficiency in energy service prod."): 1,
    ("Eps_EEps", "Fossil fuel efficiency in energy service prod."): 1,
    ("Eps_R", "Renewable efficiency in energy service prod."): 1,
    ("Y_EpsY", "Energy services efficiency in manufacturing"): 1,
    ("Y_MY", "Other inputs efficiency in manufacturing"): 0,
    ("Fi_EFi", "Fossil fuels efficiency in fisheries"): 1,
    ("Fi_MFi", "Other inputs efficiency in fisheries"): 0,
    ("T_LT", "Land use efficiency in timber prod."): 1,
    ("T_MT", "Other inputs efficiency in timber prod."): 0,
}


# Dictionary mapping row labels to LaTeX and descriptions
row_labels_map = {'A_LA': ("$A_{L_A}$", "(land use efficiency in agriculture)"),
 'A_EpsA': ("$A_{\\mathcal{E}_A}$", "(energy efficiency agriculture)"),
 'A_P': ("$A_P$", "(fertilizer efficiency in agriculture)"),
 'A_W': ("$A_W$", "(water efficiency in agriculture)"),
 'A_MA': ("$A_{M_A}$", "(other inputs efficiency in agriculture)"),
 'P_EP': ("$P_{E_P}$", "(fossil fuel efficiency in fertilizer prod.)"),
 'P_Pho': ("$P_{\\mathcal{P}}$", "(phosphor efficiency in fertilizer prod.)"),
 'P_MP': ("$P_{M_P}$", "(other inputs efficiency in fertilizer prod.)"),
 'Eps_AB': ("$\\mathcal{E}_{A_B}$", "(biofuel efficiency in energy service prod.)"),  
 'Eps_EEps': ("$\\mathcal{E}_{E_{\\mathcal{E}}}$", "(fossil fuel efficiency in energy service prod.)"),
 'Eps_R': ("$\\mathcal{E}_R$", "(renewable efficiency in energy service prod.)"),
 'Y_EpsY': ("$Y_{\\mathcal{E}_Y}$", "(energy services efficiency in manufacturing)"),
 'Y_MY': ("$Y_{M_Y}$", "(other inputs efficiency in manufacturing)"),
 'Fi_EFi': ("$F_{E_F}$", "(fossil fuels efficiency in fisheries)"),
 'Fi_MFi': ("$F_{M_F}$", "(other inputs efficiency in fisheries)"),
 'T_LT': ("$T_{L_T}$", "(land use efficiency in timber prod.)"),
 'T_MT': ("$T_{M_T}$", "(other inputs efficiency in timber prod.)")
}
col_labels_map = {'Aerosol effect': "Aerosols",
 'CO2 effect': "CO2",
 'Biodiv. incl. climate effect': "Biodiversity loss",
 'Biogeochem. effect': "Biogeochemicals",
 'Freshwater effect': "Freshwater use",
 'Ocean acid. effect': "Ocean acidification",
 'Land-use effect': "Cultivated land"}


def compute_pb_tech_individual(return_as_dataframe=False, include_food_effects=False):
    """Method for calculating how each resp tech change efffects PB´s
    Applies one tech param change at a time and stores the results in a Matrix form with Tech params on the rows and PB effects as columns.
    """
    prod_change = {}
    for k, v in sm.prod_change_dict.items():
        sm.prod_change_dict[k] = 1
        df_carbontax_quantities, df_carbontax_prices = sm.gen_results(
            robust_check=False, biofuel_tax=0
        )
        pb = sm.pb_effects(df_carbontax_quantities)
        sm.prod_change_dict[k] = 0
        pb_sum = pb[pb.columns[4:]].sum()

        if include_food_effects:
            pb_sum["Food price effect"] = sm.pb_food_price_effect(df_carbontax_prices)
            pb_sum["Food quantity effect"] = sm.pb_food_quantity_effect(df_carbontax_quantities)
            pb_sum["Food value effect"] = pb_sum["Food price effect"] + pb_sum["Food quantity effect"] 

        prod_change[k] = pb_sum
    df = pd.DataFrame(prod_change).T

    if return_as_dataframe:
        return df
    return df.to_numpy()


def gen_hrep_file_new(
    tech_params, boundaries, dir=None, exclude_non_active_boundaries=True
):
    """
    Docstring for gen_hrep_file_new
    
    :param tech_params: Technology params
    :param boundaries: Boundaries
    :param dir: Description
    :param exclude_non_active_boundaries: If this is True then we only check whether these boundary constraints hold else if False we require that the boundary constrains with a 0 do not hold. 
    
    """
    dft = compute_pb_tech_individual(return_as_dataframe=True, include_food_effects=True)

    included_boundaries = list(boundaries.keys())
    print("included_boundaries: ", included_boundaries)
    dft = dft.loc[:, included_boundaries]

    scale_factors = {'Aerosol effect': -1e5, 'CO2 effect': -1e5, 'Biodiv. incl. climate effect': -1e4,
                    'Biogeochem. effect': -1e4, 'Freshwater effect': -1e5,
                    'Land-use effect': 1e4, 'Food price effect': -1e5,
                    'Food quantity effect': 1e4, 'Food value effect': -1e5}
    for k, v in scale_factors.items():
        if k in included_boundaries:
            dft.loc[:, k] = dft.loc[:, k]*v

    dft = dft.to_numpy().T

    tech_values = list(tech_params.values())
    boundary_values = list(boundaries.values())

    ncols = sum(boundary_values)
    cnt_tech_vals = sum([1 for t in tech_values if t > 0])
    if exclude_non_active_boundaries:
        nrows = cnt_tech_vals * 2 + ncols
    else:
        nrows = cnt_tech_vals * 2 + len(boundary_values)

    bcs = ""

    for idx, dt in enumerate(dft):

        rescale_factor = 1
        if boundary_values[idx] == 0:
            if exclude_non_active_boundaries:
                continue
            else:
                # This case changes signs pof the quality constraint in order for to make the solution interpretation: active constrains hold and other not => mutually exclusive solutions.
                rescale_factor = -1 * rescale_factor

        bc = "0 " + " ".join(
            [
                "{0:.0f}".format(tc * rescale_factor)
                for ii, tc in enumerate(dt)
                if tech_values[ii] > 0
            ]
        )
        bcs += bc + "\n"
        # print(bc)

    tcs = ""
    for idx, tv in enumerate(tech_values):
        if tv == 0:
            continue

        tc = (
            f"{tv} "
            + " ".join(
                [
                    "-1" if ii == idx else "0"
                    for ii, t in enumerate(dt)
                    if tech_values[ii] > 0
                ]
            )
            + "\n"
        )  #  Cube outer constraint
        tc += "0 " + " ".join(
            [
                "1" if ii == idx else "0"
                for ii, t in enumerate(dt)
                if tech_values[ii] > 0
            ]
        )  #  greater than zero constraint
        tcs += tc + "\n"

    latte = f"{nrows} {cnt_tech_vals+1}\n" + bcs + tcs
    if dir:
        dir = Path(dir) / "pb.hrep.latte"
    else:
        dir = Path() / "hrep/temp/pb.hrep.latte"
    with open(dir, "w") as f:
        f.write(latte)
    return dir


def gen_latte(boundaries, tech_params=general_tech_params, constraints=[0, 1], compute_vertices=True, compute_polyhedra_volume=True, compute_vertex_barycenter=True, exclude_non_active_boundaries=True):
    """Generate a hrep file for volume computation and vertex enumeration in latte and compute the volume and vertices if specified."""

    print("###### Running latte ##########")

    hrep_dir = gen_hrep_file_new(
        tech_params, boundaries, exclude_non_active_boundaries=exclude_non_active_boundaries
    )

    # gen_hrep_file(tech_params, boundaries)
    print("Hrep file generated")
    tech_param_range = {}
    if compute_vertices:

        print("Convert to Vertic representation")
        JuPyMake.InitializePolymake()
        ## POLYMAKE Convert to Vertic representation ##
        with open(hrep_dir, "r") as f:
            hrep_content = f.readlines()
        ineqs = ",".join(
            [
                "[{}]".format(row.replace("\n", "").replace(" ", ","))
                for row in hrep_content[1:]
            ]
        )
        # print(ineqs)
        p = f"$p = new Polytope(INEQUALITIES=>[{ineqs}]);"
        JuPyMake.ExecuteCommand(p)
        vrep_content = JuPyMake.ExecuteCommand("print $p->VERTICES;")
        param_coords = {}
        vrep_rows = vrep_content[1].split("\n")
        for row in vrep_rows:
            if len(row) == 0:
                continue
            for ii, val in enumerate(row.split(" ")[1:]):
                if ii in param_coords:
                    param_coords[ii].append(eval(val))
                else:
                    param_coords[ii] = [eval(val)]

        print("hrep_content", hrep_content[1:])
        ## Compute polytopes ##
        # Convert hrep to numeric
        hrep = []
        for constraint in hrep_content[1:]:  # bcs.split("\n") + tcs.split("\n"):
            constraint = constraint.replace("\n", "")
            if len(constraint) == 0:
                continue
            hrep.append([int(val) for val in constraint.split(" ") if len(val) > 0])
        hrep = np.array(hrep)
        print("hrep:", hrep.shape)

        # Convert vrep to numeric and write to file
        vrep = []
        vrep_rows = vrep_content[1].split("\n")
        vrep_dir = hrep_dir.parent / "pb.vrep.latte"
        with open(vrep_dir, "w") as f:
            col_cnt = len(vrep_rows[0].split(" "))
            f.write(f"{len(vrep_rows)-1} {col_cnt}\n")
            for row in vrep_rows:
                if len(row) == 0:
                    continue
                coords = []
                numerator = 1
                numerator_idx = None
                for idx, col in enumerate(row.split(" ")):
                    if len(col.split("/")) == 1:
                        coords.append(int(col))
                    else:
                        coords.append(int(col.split("/")[0]))
                        numerator = int(col.split("/")[1])
                        numerator_idx = idx
                coords = [
                    cc * numerator if numerator_idx != idx else cc
                    for idx, cc in enumerate(coords)
                ]
                coords_str = " ".join([str(cc) for cc in coords])
                # f.write(coords_str + "\n")
                f.write(row + "\n")
                vrep.append(coords)
        vrep = np.array(vrep)
        print("vrep:", vrep.shape)
        d = hrep.shape[1] - 1
        print("dimension (d):", d)

        M = 0
        mfactor = math.factorial(M) / math.factorial(M + d)
        print("mfactor: ", mfactor)
        print(" ")

        idx = 0
        for k, v in tech_params.items():
            if v == 0:
                tech_param_range[k] = None
                continue
            tech_param_range[k] = [max(param_coords[idx]), min(param_coords[idx])]
            idx += 1


    # Compute polyhedra
    answer = None
    if compute_polyhedra_volume:
        print("Compute polyhedra")
        integrate = subprocess.run(
            [
                "integrate",
                "--valuation=volume",
                "--cone-decompose",
                hrep_dir,
            ],
            capture_output=True,
            text=True,
        )

        #
        answer = "No answer found"

        # print(integrate.stdout.split("\n"))
        for row in integrate.stdout.split("\n"):
            if "Decimal: " in row:
                # for part in row.split(" "):
                # if "Decimal:" in part:
                answer = row.split("Decimal: ")[-1]
                answer = float(answer)

        if answer == "No answer found":
            print(integrate.stderr)
        

    barycenter_params = {}
    if compute_vertex_barycenter:
        print("Compute vertex barycenter")
        JuPyMake.InitializePolymake()
        ## POLYMAKE Convert to Vertic representation ##
        with open(hrep_dir, "r") as f:
            hrep_content = f.readlines()
        ineqs = ",".join(
            [
                "[{}]".format(row.replace("\n", "").replace(" ", ","))
                for row in hrep_content[1:]
            ]
        )

        p = f"$p = new Polytope(INEQUALITIES=>[{ineqs}]);"
        JuPyMake.ExecuteCommand(p)
        barycenter_content = JuPyMake.ExecuteCommand("print $p->VERTEX_BARYCENTER;")
        tps = [k for k, v in tech_param_range.items() if v is not None]
        #print('barycenter_content', barycenter_content)
        for idx, v in enumerate(barycenter_content[1].split()):
            if idx == 0:
                continue
            tp = tps[idx-1]
            bcenter = eval(v)
            barycenter_params[tp] = bcenter
            if tech_param_range[tp] and len(tech_param_range[tp])==2:
                tech_param_range[tp].append(bcenter)
            

    return answer, tech_param_range, barycenter_params


def compute_boundary_solved_tables(result_path="./results/combo_latte_gt"):
    """Compute tables showing the number of boundaries solved and their probabilities"""
    assert result_path
    result_path = Path(result_path) if isinstance(result_path, str) else result_path
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
    file_num_boundaries_solved_probs_table =  result_path / "num_boundaries_solved_probs_table.csv"
    with open(
        file_num_boundaries_solved_probs_table, "w", newline=""
    ) as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(prob_to_csv)

    file_num_boundaries_solved_probs_share_table =  result_path / "num_boundaries_solved_probs_share_table.csv"
    with open(
        file_num_boundaries_solved_probs_share_table, "w", newline=""
    ) as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(prob_shares_to_csv)
    
    return file_num_boundaries_solved_probs_table, file_num_boundaries_solved_probs_share_table