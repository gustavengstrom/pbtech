# Computations for PBTECH paper

`Results_and_figures.ipynb`: contains the method `gen_latte` which can be used to run Latte from e.g. a notebook.

`Results_and_figures.py`: contains the following methods
  - `compute_pb_tech_individual`: for calculating the boundary pressure resulting from each resp tech change individually
  - `gen_hrep_file_new`: generates a hrep file which can be processed by Latte
  - `gen_latte`: method which can be used to run Latte from e.g. a notebook.
  - `compute_boundary_solved_tables`: Compute tables showing the number of boundaries solved and their probabilities

`compute_latte_combos.py`: contains code for computing specific boundary and parameter combinations. The results are stored in the results directory.


The `results` directory active sub directories :
* combo_latte_all_params: Contains results for general tech change using all params 
* combo_latte_gt: Contains results for green tech i.e. where other inputs are set to 0

The `hrep` directory stores hrep files used by e.g. `gen_latte` and `compute_latte_combos.py`

The `model_code` directory contains the code for solving the underlying model.

# Running Latte in the terminal

integrate --valuation=volume --cone-decompose "./latte/pbtech/pb.hrep.latte"