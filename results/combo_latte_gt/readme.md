This folder contains probability volume results for the 12 dimensional green tech polyhedra without other inputs.

The results in this folder were computed using the file `compute_latte_combos.py`


# Result in pbtech/results/combo_latte_gt/pb_1_1_0_1_1_1.hrep.latte.txt  `U(1,1,0,1,1,1)`

This U(1,1,0,1,1,1) combo was not feasible to compute using latte and hence derived using the following method 

First, let U denote non mutually exclusive volumes and V the mutually exclusive volumes. Hence, the following relationships must hold:

a) U(1,1,0,1,1,1) = V(1,1,1,1,1,1) + V(1,1,0,1,1,1)
b) U(0,1,0,1,1,1) = V(1,1,1,1,1,1) + V(1,1,0,1,1,1) + V(0,1,1,1,1,1) + V(0,1,0,1,1,1)
c) U(0,1,1,1,1,1) = V(1,1,1,1,1,1) + V(0,1,1,1,1,1)

Where U(0,1,0,1,1,1) was computed to 0.9176386463193846 and U(0,1,1,1,1,1) to 4.913540475207658e-09 using latte. Further, we were also able to calculate the Mutually exclusive volume: V(0,1,0,1,1,1) = 0.10802364068595177900708866119253e-11 using Latte.

This allowed us to derive also V(1,1,0,1,1,1) 

From b) and c) we can write:
V(1,1,0,1,1,1) = U(0,1,0,1,1,1) - U(0,1,1,1,1,1) - V(0,1,0,1,1,1) =  0.9176386463193846 -  4.913540475207658e-09 - 0.10802364068595177900708866119253e-11 = 0.9176386414047639

Inserting this into a) gives us:

U(1,1,0,1,1,1) = V(1,1,0,1,1,1) + V(1,1,1,1,1,1) = 0.9176386414047639 + 4.913540475207658e-09 = 0.9176386463183044
