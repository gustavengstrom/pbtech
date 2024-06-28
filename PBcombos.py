# import necessary packages
import multiprocessing as mp
import numpy as np
import pandas as pd
import re, importlib
import subprocess
from tqdm import tqdm
import os, sys, json
import JuPyMake
from pathlib import Path
from itertools import product
from itertools import batched
from web_model import params, model  # Load parameters and model implementation.
param_list = list(params.df_typing_formatting.T.to_dict().values())
model_params = {row["keys"]: row["values"] for row in param_list}
sm = model.SolveModel(model_params)

df_carbontax_quantities, df_carbontax_prices = sm.gen_results(
    robust_check=False, biofuel_tax=0
)

pb = sm.pb_effects(df_carbontax_quantities)

prod_change_dict = sm.prod_change_dict.copy()


def compute_pb_tech_individual():
    """ Method for calculating how each resp tech change efffects PB´s 
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
        pb_sum["Ozone effect"] = int(pb_sum["Ozone effect"] > 0) + -1 * int(
            pb_sum["Ozone effect"] < 0
        )
        pb_sum["Chem. effect"] = int(pb_sum["Chem. effect"] > 0) + -1 * int(
            pb_sum["Chem. effect"] < 0
        )
        tex_key = sm.prod_change_tex[k]
        prod_change[k] = pb_sum
    df = pd.DataFrame(prod_change).T

    return df.to_numpy()

def gen_latte(tech_params, boundaries, constraints=[0,1], compute_vertices=True):
    """Generate a latte file for volume ccomputation """
    print("Running latte")
    
    dft = compute_pb_tech_individual()[:,0:7].T
    tech_values = list(tech_params.values()) 
    boundary_values = list(boundaries.values())
    ncols = sum(boundary_values)
    cnt_tech_vals =sum([1 for t in tech_values if t>0])
    nrows = cnt_tech_vals*2 + ncols
    bcs = ""
    for idx, dt in enumerate(dft):
        if boundary_values[idx] == 0:
            continue 
        int_factor = 1e12*-1
        if idx==6:
            int_factor = 1e12
        bc = "0 " + " ".join(["{0:.0f}".format(tc*int_factor) for ii, tc in enumerate(dt) if tech_values[ii]>0])
        bcs += bc + "\n"
        print(bc)

    tcs = ""
    for idx, tv in enumerate(tech_values):
        if tv == 0:
            continue 
        
        tc = f"{tv} " + " ".join(["-1" if ii==idx else "0" for ii, t in enumerate(dt) if tech_values[ii]>0]) + "\n"     #  Cube outer constraint
        tc += "0 " + " ".join(["1" if ii==idx else "0" for ii, t in enumerate(dt) if tech_values[ii]>0])                #  greater than zero constraint
        tcs += tc + "\n"
    
    latte = f"{nrows} {cnt_tech_vals+1}\n" + bcs + tcs
    with open("./latte/pbtech/pb.hrep.latte", "w") as f:
        f.write(latte)

    tech_param_range = {}
    if compute_vertices:
        print("Convert to Vertic representation")
        JuPyMake.InitializePolymake()
        ## POLYMAKE Convert to Vertic representation ##
        with open("./latte/pbtech/pb.hrep.latte", "r") as f:
            hrep_content = f.readlines()
        ineqs=",".join(["[{}]".format(row.replace("\n","").replace(" ",",")) for row in hrep_content[1:]])
        #print(ineqs)
        p = f"$p = new Polytope(INEQUALITIES=>[{ineqs}]);"
        JuPyMake.ExecuteCommand(p)
        vrep_content = JuPyMake.ExecuteCommand("print $p->VERTICES;")
        param_coords = {}
        #print(vrep_content[1])
        for row in vrep_content[1].split("\n"):
            if len(row) == 0:
                continue
            for ii, val in enumerate(row.split(" ")[1:]):
                if ii in param_coords:
                    param_coords[ii].append(eval(val))
                else:
                    param_coords[ii]  = [eval(val)]

        idx = 0
        for k, v in tech_params.items():
            if v == 0:
                tech_param_range[k] = None
                continue
            tech_param_range[k] = [max(param_coords[idx]),min(param_coords[idx])]
            idx += 1
        #################################################

    """
    ## POLYMAKE TEST ##
    with open("./latte/test/manual_example/manual.hrep.latte", "r") as f:
        manual = f.readlines()
    ineqs=",".join(["[{}]".format(row.replace("\n","").replace(" ",",")) for row in manual[1:]])
    p = f"$p = new Polytope(INEQUALITIES=>[{ineqs}]);"
    JuPyMake.ExecuteCommand(p)
    res=JuPyMake.ExecuteCommand("print $p->VERTICES;")
    params = {}
    print(res[1])
    for row in res[1].split("\n"):
        if len(row) == 0:
            continue
        for ii, val in enumerate(row.split(" ")[1:]):
            if ii in params:
                params[ii].append(val)
            else:
                params[ii]  = [val]
    #res[1]
    integrate = subprocess.run(["integrate", "--valuation=volume", "--cone-decompose", "./latte/test/manual_example/manual.hrep.latte"], capture_output=True, text=True)
    integrate = subprocess.run(["integrate", "--valuation=volume", "--cone-decompose", "./latte/test/test.hrep.latte"], capture_output=True, text=True)

    #######
    """

    # Compute polyhedra
    print("Compute polyhedra")
    integrate = subprocess.run(["integrate", "--valuation=volume", "--cone-decompose", "./latte/pbtech/pb.hrep.latte"], capture_output=True, text=True)

    # 
    answer = None

    print(integrate.stdout.split("\n"))
    for row in integrate.stdout.split("\n"):
        if "Decimal: " in row:
            #for part in row.split(" "):
                #if "Decimal:" in part:
            answer = row.split("Decimal: ")[-1]
            answer = float(answer)
    


    
    return answer, tech_param_range


def pb_boundary(c, df=None, pack=True):
    """ Method for computing the effect based on a specific policy combination.
    pack: setting this to True reduces storage size on disk
    """
    if not df:
        df = np.array([[0.0010672170921913766, 0.041064083724359594, 0.03606265998995495, -0.09056933011478599, -0.04212802843617142, 0.041064083724359594, -0.009457889673203462, 1.0, 0.0], [0.000280677776028135, 0.008976494788867724, 0.01177139088129886, 0.03526377679207529, 0.01852054800088953, 0.008976494788867724, 0.02102473117337316, 1.0, 0.0], [0.00020340503955239205, 0.006589680358849447, -0.006776759136928323, -0.7402134722784179, 0.022800158842504303, 0.006589680358849447, 0.026026952518861418, 1.0, 0.0], [9.9185328694472e-05, 0.003172095057746263, 0.00415974962560961, 0.012461440095563102, -0.3842849415925758, 0.003172095057746263, 0.0074296757714614955, 1.0, 0.0], [0.003884525919690355, 0.12423294486923242, 0.1629137640898226, 0.48804382346702246, 0.2563207881093982, 0.12423294486923242, 0.290978196967412, 1.0, 0.0], [-0.00024021385317936803, -0.007525790597789012, 0.0038170542693505283, -0.7438123683284646, 0.0015344277486948853, -0.007525790597789012, 0.0020087592144643757, 1.0, -1.0], [0.00014337353262626137, 0.004561989962317463, 0.015669995737233045, -0.47658456002351374, 0.006872888059443555, 0.004561989962317463, 0.007762458447490711, 1.0, 0.0], [0.0003002453601054886, 0.009553480994320743, 0.03281528624420327, 0.48018345607356033, 0.014392843034365638, 0.009553480994320743, 0.01625573485690654, 1.0, 0.0], [-0.0006111707649527577, -0.01246899195121234, -0.002054702421672161, 0.025601994295128286, 0.009820830412398384, -0.01246899195121234, -0.0347027538961542, -1.0, -1.0], [-0.010601937582399506, -0.18222918227136342, 0.006492022805304476, 0.030006844126706043, -0.01827941758527299, -0.18222918227136342, 0.02399593109999751, 0.0, -1.0], [-0.001378795905645309, -0.02429506543859241, 0.001620392870027576, 0.006529822849102153, -0.0011754369121571736, -0.02429506543859241, 0.0016281928468621894, 0.0, -1.0], [-0.011353948105761754, -0.19686385686103025, 0.005973005270065723, 0.05761786114221153, -0.007917923440818157, -0.19686385686103025, -0.011396641580090863, 0.0, -1.0], [0.007955944854472449, 0.2614958180324138, 0.10111898011515574, 0.28702815750204236, 0.16405574909673404, 0.2614958180324138, -0.6538286204894805, 1.0, 0.0], [-4.432538898446151e-05, -0.001712370567540188, 0.007170572698467215, -0.0027423063067561065, -0.0014945870566598976, -0.001712370567540188, 0.0026320395286490873, 0.0, -1.0], [0.00019221806859163147, 0.0017392470741345537, 0.04032729896277232, -0.018034945822891793, -0.00826967604066459, 0.0017392470741345537, 0.014594754586366124, 1.0, -1.0], [1.0008546572808551e-05, -0.0008635002555022078, 0.059912845007070725, -0.0014463897522506383, -0.0005926498932396549, -0.0008635002555022078, 0.013885795678424254, 1.0, 0.0], [0.00013047951009683057, 0.0035842060759157883, 0.15737326705952404, -0.001374217876452746, -0.00039992010625888993, 0.0035842060759157883, -0.01968233909427637, 1.0, -1.0]])
    dc = df * np.array(c).reshape(len(c), 1)
    dc_sum = dc.sum(axis=0)[0:7]<0
    if pack:
        return np.packbits(dc_sum, axis=None)
    else:
        return dc_sum

def compute_tech_combos(output_path, discrete_vals, batches=10, param_idx_restrict_vals=None):
    """ Method for computing potential technology policy combinations 

    output_path:    The results for each combination is a vector of 7 compressed boolean values (positive or negative) representing:
                    ['Aerosol effect','CO2 effect','Biodiv. incl. climate effect','Biogeochem. effect','Freshwater effect','Ocean acid. effect','Land-use effect'] 
                    The vectors are concatenated and stored in numpy format. Note: A positive value means that the boundary process is expanding and vice versa.
    discrete_vals: Number of discrete possible combinations
    batches (integer): To avoid memory problems the process can be divided in a number of batches.
    param_idx_restrict_vals: a dictionary where the keys define index values of the tech params and the values denote the value that theuy should be fixed at e.g. we can run all combinations except those where other inputs are set equal to 0

    """
    num_variables = len(sm.prod_change_dict)
    total =len(discrete_vals)**num_variables
    combinations = product(discrete_vals, repeat=num_variables)
    batched_combinations = batched(combinations, int(total/batches))
    
    df_independent_one_percent_tech_changes = compute_pb_tech_individual()
    for ii, bc in enumerate(batched_combinations):
        pb_combo_effects = []
        cnt = 0 
        for c in tqdm(bc, total=total):
            if param_idx_restrict_vals and not all([c[idx]==val for idx, val in param_idx_restrict_vals.items()]):
                continue
            cnt += 1
            dc_sum_bits = pb_boundary(c, df=df_independent_one_percent_tech_changes)
            pb_combo_effects.append(dc_sum_bits)
    
        discrete_vals_str = [str(d) for d in discrete_vals]

        file_name=f"pb_{ii}_combos_{'_'.join(discrete_vals_str)}_"
        if param_idx_restrict_vals:
            file_name = file_name + f"restrict_{cnt}" 
        with open(output_path / f"{file_name}.npy", "wb") as f:
            np.save(f, np.concatenate(pb_combo_effects))


def check_combos(discrete_vals, file_path, batches=10, param_idx_restrict_vals=None, file_name_extension=''):
    """ Method for loading the stored tech param combination results and evaluating then 
    Returns a generator containing the idx number and outcome that the policy combo has on a boundary. 
    """

    num_variables = len(sm.prod_change_dict)
    total =len(discrete_vals)**num_variables
    combinations = product(discrete_vals, repeat=num_variables)
    
    batched_combinations = batched(combinations, int(total/batches))
    discrete_vals_str = [str(d) for d in discrete_vals]
    
    for ii, bc in enumerate(batched_combinations):

        file_name = f"pb_{ii}_combos_{'_'.join(discrete_vals_str)}{file_name_extension}.npy"
        file = file_path / file_name
        if file.exists():
            print("loading:", file_name)
            pb_combo_effects = np.load(file)
            cnt=0
            for idx, c in tqdm(enumerate(bc), total=total):
                if param_idx_restrict_vals and not all([c[idx]==val for idx, val in param_idx_restrict_vals.items()]):
                    continue
                pc = pb_combo_effects[cnt] 
                dno = np.unpackbits(pc, count=7).reshape((7,)).view(bool)
                cnt += 1
                yield c, dno



def check_pb_violations(discrete_vals, file_path):
    num_variables = len(sm.prod_change_dict)
    total =len(discrete_vals)**num_variables
    combinations = product(discrete_vals, repeat=num_variables)
    batched_combinations = batched(combinations, int(total/10))
    discrete_vals_str = [str(d) for d in discrete_vals]
    

    good_for_all_pbs =[]
    for ii, bc in enumerate(batched_combinations):
        file_name = f"pb_{ii}_combos_{'_'.join(discrete_vals_str)}.npy"
        
        if file_path.exists():
            pb_combo_effects = np.load(file_path)
            for idx, c in tqdm(enumerate(bc), total=total):
                pc = pb_combo_effects[idx]
                dno = np.unpackbits(pc, count=7).reshape((7,)).view(bool)

                if all(dno):
                    good_for_all_pbs.append(c)
                    print("good_for_all_pbs")

    return good_for_all_pbs


if __name__=="__main__":
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)
    #import PBcombos as pbc


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
    boundaries = {'Aerosol effect': 1,
    'CO2 effect': 1,
    'Biodiv. incl. climate effect': 1,
    'Biogeochem. effect': 1,
    'Freshwater effect': 1,
    'Ocean acid. effect': 1,
    'Land-use effect': 1
    }
    result, tech_param_range = gen_latte(tech_params, boundaries, constraints=[0,1])   
    print(tech_param_range)
    print(result)

if __name__ == "old__main__":
    discrete_vals = [0,1,2]
    output_path = Path() / "results"
    param_constraint = {}
    tech_params = {
        ("A_LA", "Land use efficiency in agriculture"): 0,
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
    param_idx_restrict_vals = {4: 0, 7: 0, 12: 0, 14: 0, 16: 0}
    #[property_a[i] for i in good_indices]
    compute_tech_combos(output_path, discrete_vals, batches=1, param_idx_restrict_vals=param_idx_restrict_vals)

    #print(good_for_all_pbs)                                                                                                                                                                                                                             | 3/129140163 [00:00<32:29, 66225.85it/s]
    # pbc = [(0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 1, 1, 0, 1, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 1, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 1, 2, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 0, 1, 0, 1, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 1, 0, 0, 1, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 1, 1, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 2, 0, 0, 1, 0, 0, 0), (0, 0, 2, 1, 0, 0, 0, 0, 2, 0, 2, 1, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 1, 0, 0, 1, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 1, 1, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 1, 0, 0, 2, 0, 2, 1, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 2, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 2, 1, 0, 2, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0), (0, 0, 2, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 2, 2, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0), (0, 0, 2, 2, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0), (0, 0, 2, 2, 0, 0, 0, 0, 2, 0, 1, 1, 0, 0, 0, 0, 0), (0, 0, 2, 2, 0, 0, 0, 0, 2, 0, 2, 1, 0, 0, 0, 0, 0), (0, 0, 2, 2, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0)]
    # for c in pbc:
    #     print(pb_boundary(c, pack=False))
    # print(len(pbc))





# import numpy as np

# # Suppose you have three arrays
# arr1 = np.array([1, 0, 1], dtype=bool)
# arr2 = np.array([0, 1, 1], dtype=bool)
# arr3 = np.array([1, 1, 1], dtype=bool)

# # Apply packbits to each array
# packed_arr1 = np.packbits(arr1, axis=None)
# packed_arr2 = np.packbits(arr2, axis=None)
# packed_arr3 = np.packbits(arr3, axis=None)

# # Concatenate the packed arrays
# concatenated_packed_array = np.concatenate([packed_arr1, packed_arr2, packed_arr3])

# # Optionally, unpack the concatenated array
# unpacked_array = np.unpackbits(concatenated_packed_array)

# print("Concatenated packed array:", concatenated_packed_array, concatenated_packed_array.shape)
# print("Unpacked array:", unpacked_array)
# bb = np.unpackbits(packed_arr1, count=arr1.size).reshape(arr1.shape).view(bool)
# print(arr1)
# print('..')
# for pa in concatenated_packed_array:
#     print(np.unpackbits(pa, count=arr1.size).reshape(arr1.shape).view(bool))

tech_param_desc = {
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