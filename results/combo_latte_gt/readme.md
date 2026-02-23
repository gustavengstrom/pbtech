This folder contains probability volume results for the 12 dimensional green tech polyhedra without other inputs.

The results in this folder were computed using the file `compute_latte_combos.py`


# Result in pbtech/results/combo_latte_gt/pb_1_1_0_1_1_1.hrep.latte.txt  `U(1,1,0,1,1,1)`

This (0,1,0,1,1,1) combo was difficult to solve using latte and hence derived using the following formula (U denotes non mutually exclusive volumes and V the mutually exclusive volumes):

U(0,1,0,1,1,1) = V(1,1,1,1,1,1) + V(1,1,0,1,1,1) + V(0,1,1,1,1,1) + V(0,1,0,1,1,1)

Where the Mutually exclusive volume: V(0,1,0,1,1,1) = 0.10802364068595177900708866119253e-11 was calculated using Latte.

=> which allowed us to derived V(1,1,0,1,1,1) 

V(1,1,0,1,1,1) = U(0,1,0,1,1,1) - V(1,1,1,1,1,1) - V(0,1,1,1,1,1) - V(0,1,0,1,1,1) =  0.9176386463193846 -  4.913540475207658e-09 - 0.0 - 0.10802364068595177900708866119253e-11 = 0.9176386414047639

and hence

U(1,1,0,1,1,1) = V(1,1,0,1,1,1) + V(1,1,1,1,1,1) = 0.9176386414047639 + 4.913540475207658e-09 = 0.9176386463183044
