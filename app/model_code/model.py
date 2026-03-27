import numpy as np
import pandas as pd
import os, sys
from itertools import product
import re


class SolveModel(object):
    def __init__(self, params):

        for k, v in params.items():
            setattr(self, k, v)

        self.Lambda_MA = (
            self.Lambda_M
        )  # 1/1.7        # supply elast. intermediates to agriculture
        self.Lambda_MT = self.Lambda_M  # supply elast. intermediates to timber
        self.Lambda_MY = self.Lambda_M  # supply elast. intermediates to final goods
        self.Lambda_MP = self.Lambda_M  # supply elast. intermediates to fertilizers
        self.Lambda_MFi = self.Lambda_M  # supply elast. intermediates to fisheries

        self.var_desc_dict = {
            "L_A": (r"$L_A$", "(land-share agriculture)"),
            "L_T": (r"$L_T$", "(land-share timber)"),
            "L_U": (r"$L_U$", "(land-share other)"),
            "E": (r"$E$", "(fossil-fuel extracted)"),
            "E_Eps": (r"$E_{\mathcal{E}}$", "(fossil-fuel use energy serv.)"),
            "E_P": (r"$E_P$", "(fossil-fuel use fertilizer prod.)"),
            "E_Fi": (r"$E_F$", "(fossil-fuel use fisheries)"),
            "A": (r"$A\;\;$", "(agriculture total production)"),
            "A_B": (r"$A_B$", "(agriculture prod. for biofuels)"),
            "A_F": (r"$A_F$", "(agriculture prod. for food)"),
            "Eps": (r"$\mathcal{E}\;\;$", "(energy services)"),
            "Eps_A": (r"$\mathcal{E}_A$", "(energy for agriculture)"),
            "Eps_Y": (r"$\mathcal{E}_{Y}$", "(energy services for final goods)"),
            "P": (r"$P\;\;$", "(fertilizer production)"),
            "W": (r"$W\;$", "(water production)"),
            "Pho": (r"$\mathcal{P}\;\;$", "(phosphate extraction)"),
            "R": (r"$R\;\;$", "(renewables production)"),
            "Fi": (r"$F\;\;$", "(fisheries production)"),
            "T": (r"$T\;\;$", "(timber production)"),
            "Y": (r"$Y\;\;$", "(final goods)"),
            "MA": (r"$M_A\;\;$", "(intermediaries agriculture.)"),
            "MT": (r"$M_T\;\;$", "(intermediaries timber.)"),
            "MFi": (r"$M_F\;\;$", "(intermediaries fisheries)"),
            "MY": (r"$M_Y\;\;$", "(intermediaries final goods.)"),
            "MP": (r"$M_P\;\;$", "(intermediaries fertilizers)"),
        }

        # prepare list of price changes and labels
        self.price_desc_dict = {
            "p_A": (r"$p_A$", "(agricultural goods)"),
            "p_E": (r"$p_E$", "(fossil-fuels)"),
            "p_Eps": (r"$p_{\mathcal{E}}$", "(energy services)"),
            "p_Fi": (r"$p_{F}$", "(fisheries)"),
            "p_L": (r"$p_{L}$", "(land)"),
            "p_MA": (r"$p_{M_A}$", "(intermediaries agric.)"),
            "p_MFi": (r"$p_{M_F}$", "(intermediaries fisheries)"),
            "p_MP": (r"$p_{M_P}$", "(intermediaries fertilizers.)"),
            "p_MT": (r"$p_{M_T}$", "(intermediaries timber)"),
            "p_MY": (r"$p_{M_Y}$", "(intermediaries final goods)"),
            "p_P": (r"$p_{P}$", "(fertilizers)"),
            "p_Pho": (r"$p_{Pho}$", "(phosphate)"),
            "p_R": (r"$p_{R}$", "(renewables)"),
            "p_T": (r"$p_{T}$", "(timber)"),
            "p_W": (r"$p_{W}$", "(water)"),
            "p_Y": (r"$p_{Y}$", "(final goods)"),
        }

        self.prod_change_dict = {
            "A_LA": 0,
            "A_EpsA": 0,
            "A_P": 0,
            "A_W": 0,
            "A_MA": 0,
            "P_EP": 0,
            "P_Pho": 0,
            "P_MP": 0,
            "Eps_AB": 0,
            "Eps_EEps": 0,
            "Eps_R": 0,
            "Y_EpsY": 0,
            "Y_MY": 0,
            "Fi_EFi": 0,
            "Fi_MFi": 0,
            "T_LT": 0,
            "T_MT": 0,
        }
        self.prod_change_tex = {
            "A_LA": 0,
            "A_EpsA": 0,
            "A_P": 0,
            "A_W": 0,
            "A_MA": 0,
            "P_EP": 0,
            "P_Pho": 0,
            "P_MP": "$$P_{M_P}$$",
            "Eps_AB": r"$$\mathcal{E}_{A_{B}}$$",
            "Eps_EEps": r"$\mathcal{E}_{E_{\mathcal{E}}}\;\;$",
            "Eps_R": r"$\mathcal{E}_{R}\;\;$",
            "Y_EpsY": r"$Y_{\mathcal{E}_Y}\;\;$",
            "Y_MY": r"$Y_{\mathcal{E}_{M_Y}}\;\;$",
            "Fi_EFi": 0,
            "Fi_MFi": 0,
            "T_LT": 0,
            "T_MT": 0,
        }

    def gen_coef_matrix(self, var_dict, biofuel_tax=0):

        # dp = prod_change_dict
        v = var_dict
        vci = v["vci"]
        pci = v["pci"]
        dp = v["prod_change_dict"]
        # locals().update(var_dict)# Coefficient  Matrix (rows: equations, columns: variables)
        # note: python vectors starts with index zero
        coef_matrix = np.zeros((41, 41))
        # print(locals())
        # Policy variable vector (carbon tax)
        policy_vector = np.zeros((41, 1))

        ## Populate coefficient matrix and policy vector (note: document equation numbers specified in brackets)

        # Market clearing Fixed totat land: eq. [72]
        coef_matrix[0, vci["L_A"]] = v["Q_LA"]
        coef_matrix[0, vci["L_T"]] = v["Q_LT"]
        coef_matrix[0, vci["L_U"]] = v["Q_LU"]

        # Market clearing constraint fossil fuel: eq. [73]
        coef_matrix[1, vci["E"]] = -1
        coef_matrix[1, vci["E_Eps"]] = v["Q_EEps"]
        coef_matrix[1, vci["E_P"]] = v["Q_EP"]
        coef_matrix[1, vci["E_Fi"]] = v["Q_EFi"]

        # Market clearing agric. output: eq. [74]
        coef_matrix[2, vci["A"]] = -1
        coef_matrix[2, vci["A_B"]] = v["Q_AB"]
        coef_matrix[2, vci["A_F"]] = v["Q_AF"]

        # Market clearing energy. services: eq. [75]
        coef_matrix[3, vci["Eps"]] = -1
        coef_matrix[3, vci["Eps_A"]] = v["Q_EpsA"]
        coef_matrix[3, vci["Eps_Y"]] = v["Q_EpsY"]

        # Agricultural prod. : eq. [76]
        coef_matrix[4, vci["L_A"]] = v["GammaA_LA"]
        coef_matrix[4, vci["A"]] = -1.0
        coef_matrix[4, vci["Eps_A"]] = v["GammaA_EpsA"]
        coef_matrix[4, vci["P"]] = v["GammaA_P"]
        coef_matrix[4, vci["W"]] = v["GammaA_W"]
        coef_matrix[4, vci["MA"]] = v["GammaA_MA"]
        policy_vector[4] = (
            -v["GammaA_LA"] * dp["A_LA"]
            - v["GammaA_EpsA"] * dp["A_EpsA"]
            - v["GammaA_P"] * dp["A_P"]
            - v["GammaA_W"] * dp["A_W"]
            - v["GammaA_MA"] * dp["A_MA"]
        )

        # Timber prod. : eq. [77]
        coef_matrix[5, vci["L_T"]] = v["GammaT_LT"]
        coef_matrix[5, vci["T"]] = -1.0
        coef_matrix[5, vci["MT"]] = v["GammaT_MT"]
        policy_vector[5] = -v["GammaT_LT"] * dp["T_LT"] - v["GammaT_MT"] * dp["T_MT"]

        # Fertilizer prod. : eq. [78]
        coef_matrix[6, vci["P"]] = -1
        coef_matrix[6, vci["E_P"]] = v["GammaP_EP"]
        coef_matrix[6, vci["Pho"]] = v["GammaP_Pho"]
        coef_matrix[6, vci["MP"]] = v["GammaP_MP"]
        policy_vector[6] = (
            -v["GammaP_EP"] * dp["P_EP"]
            - v["GammaP_Pho"] * dp["P_Pho"]
            - v["GammaP_MP"] * dp["P_MP"]
        )

        # Energy prod. : eq. [79]
        coef_matrix[7, vci["Eps"]] = -1.0
        coef_matrix[7, vci["A_B"]] = v["GammaEps_AB"]
        coef_matrix[7, vci["E_Eps"]] = v["GammaEps_EEps"]
        coef_matrix[7, vci["R"]] = v["GammaEps_R"]
        policy_vector[7] = (
            -v["GammaEps_AB"] * dp["Eps_AB"]
            - v["GammaEps_EEps"] * dp["Eps_EEps"]
            - v["GammaEps_R"] * dp["Eps_R"]
        )

        # Final good prod. : eq. [80]
        coef_matrix[8, vci["Y"]] = -1.0
        coef_matrix[8, vci["Eps_Y"]] = v["GammaY_EpsY"]
        coef_matrix[8, vci["MY"]] = v["GammaY_MY"]
        policy_vector[8] = (
            -v["GammaY_EpsY"] * dp["Y_EpsY"] - v["GammaY_MY"] * dp["Y_MY"]
        )

        # Fisheries prod.
        coef_matrix[9, vci["Fi"]] = -1.0
        coef_matrix[9, vci["E_Fi"]] = v["GammaFi_EFi"]
        coef_matrix[9, vci["MFi"]] = v["GammaFi_MFi"]
        policy_vector[9] = (
            -v["GammaFi_EFi"] * dp["Fi_EFi"] - v["GammaFi_MFi"] * dp["Fi_MFi"]
        )

        # foc: agric. wrt land use
        coef_matrix[10, pci["p_A"]] = 1
        coef_matrix[10, pci["p_L"]] = -1
        coef_matrix[10, vci["L_A"]] = -v["V_A"] - 1 / v["sigma_A"]
        coef_matrix[10, vci["A"]] = 1 / v["sigma_A"]
        policy_vector[10] = -(1 - 1 / v["sigma_A"]) * dp["A_LA"]

        # foc: agric. wrt P (fertiliz)
        coef_matrix[11, pci["p_A"]] = 1
        coef_matrix[11, pci["p_P"]] = -1
        coef_matrix[11, vci["A"]] = 1 / v["sigma_A"]
        coef_matrix[11, vci["P"]] = (
            -(1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_P"]
            - 1 / v["sigma_nLA"]
        )
        coef_matrix[11, vci["MA"]] = (
            -(1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_MA"]
        )
        coef_matrix[11, vci["W"]] = (
            -(1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_W"]
        )
        coef_matrix[11, vci["Eps_A"]] = (
            -(1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_EpsA"]
        )
        policy_vector[11] = (
            (1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_P"]
            - (1 - 1 / v["sigma_nLA"])
        ) * dp["A_P"]
        policy_vector[11] = (
            policy_vector[11]
            + ((1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_MA"]) * dp["A_MA"]
        )
        policy_vector[11] = (
            policy_vector[11]
            + (1 / v["sigma_A"] - 1 / v["sigma_nLA"]) * v["GammanLA_W"] * dp["A_W"]
        )
        policy_vector[11] = (
            policy_vector[11]
            + (1 / v["sigma_A"] - 1 / v["sigma_nLA"])
            * v["GammanLA_EpsA"]
            * dp["A_EpsA"]
        )

        # foc: agric. wrt P and MA
        coef_matrix[12, pci["p_P"]] = 1
        coef_matrix[12, pci["p_MA"]] = -1
        coef_matrix[12, vci["MA"]] = -1 / v["sigma_nLA"]
        coef_matrix[12, vci["P"]] = 1 / v["sigma_nLA"]
        policy_vector[12] = (
            -(1 - 1 / v["sigma_nLA"]) * dp["A_MA"]
            + (1 - 1 / v["sigma_nLA"]) * dp["A_P"]
        )

        # foc: agric. wrt P and W
        coef_matrix[13, pci["p_P"]] = 1
        coef_matrix[13, pci["p_W"]] = -1
        coef_matrix[13, vci["W"]] = -1 / v["sigma_nLA"]
        coef_matrix[13, vci["P"]] = 1 / v["sigma_nLA"]
        policy_vector[13] = (
            -(1 - 1 / v["sigma_nLA"]) * dp["A_W"] + (1 - 1 / v["sigma_nLA"]) * dp["A_P"]
        )

        # foc: agric. wrt P and Eps_A
        coef_matrix[14, pci["p_P"]] = 1
        coef_matrix[14, pci["p_Eps"]] = -1
        coef_matrix[14, vci["Eps_A"]] = -1 / v["sigma_nLA"]
        coef_matrix[14, vci["P"]] = 1 / v["sigma_nLA"]
        policy_vector[14] = (
            -(1 - 1 / v["sigma_nLA"]) * dp["Eps_AB"]
            + (1 - 1 / v["sigma_nLA"]) * dp["A_P"]
        )

        # foc: Eps. wrt E_Eps
        coef_matrix[15, pci["p_Eps"]] = 1
        coef_matrix[15, pci["p_E"]] = -1
        coef_matrix[15, vci["Eps"]] = 1 / v["sigma_Eps"]
        coef_matrix[15, vci["E_Eps"]] = -1 / v["sigma_Eps"]
        policy_vector[15] = -(1 - 1 / v["sigma_Eps"]) * dp["Eps_EEps"]

        # foc: Eps. wrt A_B
        policy_vector[16] = biofuel_tax / (1 + v["tau_E"])
        coef_matrix[16, pci["p_Eps"]] = 1
        coef_matrix[16, pci["p_A"]] = -1
        coef_matrix[16, vci["Eps"]] = 1 / v["sigma_Eps"]
        coef_matrix[16, vci["A_B"]] = -1 / v["sigma_Eps"]
        policy_vector[16] = -(1 - 1 / v["sigma_Eps"]) * dp["Eps_AB"]

        # foc: Eps. wrt R
        coef_matrix[17, pci["p_Eps"]] = 1
        coef_matrix[17, pci["p_R"]] = -1
        coef_matrix[17, vci["Eps"]] = 1 / v["sigma_Eps"]
        coef_matrix[17, vci["R"]] = -1 / v["sigma_Eps"]
        policy_vector[17] = -(1 - 1 / v["sigma_Eps"]) * dp["Eps_R"]

        # foc: P wrt E_P
        coef_matrix[18, pci["p_P"]] = 1
        coef_matrix[18, pci["p_E"]] = -1
        coef_matrix[18, vci["P"]] = 1 / v["sigma_P"]
        coef_matrix[18, vci["E_P"]] = -1 / v["sigma_P"]
        policy_vector[18] = -(1 - 1 / v["sigma_P"]) * dp["P_EP"]

        # foc: P wrt Pho
        coef_matrix[19, pci["p_P"]] = 1
        coef_matrix[19, pci["p_Pho"]] = -1
        coef_matrix[19, vci["P"]] = 1 / v["sigma_P"]
        coef_matrix[19, vci["Pho"]] = -1 / v["sigma_P"]
        policy_vector[19] = -(1 - 1 / v["sigma_P"]) * dp["P_Pho"]

        # foc: P wrt MP
        coef_matrix[20, pci["p_P"]] = 1
        coef_matrix[20, pci["p_MP"]] = -1
        coef_matrix[20, vci["P"]] = 1 / v["sigma_P"]
        coef_matrix[20, vci["MP"]] = -1 / v["sigma_P"]
        policy_vector[20] = -(1 - 1 / v["sigma_P"]) * dp["P_MP"]

        # foc: T wrt L_T
        coef_matrix[21, pci["p_T"]] = 1
        coef_matrix[21, pci["p_L"]] = -1
        coef_matrix[21, vci["T"]] = 1 / v["sigma_T"]
        coef_matrix[21, vci["L_T"]] = -1 / v["sigma_T"] - v["V_T"]
        policy_vector[21] = -(1 - 1 / v["sigma_T"]) * dp["T_LT"]

        # foc: T wrt MT
        coef_matrix[22, pci["p_T"]] = 1
        coef_matrix[22, pci["p_MT"]] = -1
        coef_matrix[22, vci["T"]] = 1 / v["sigma_T"]
        coef_matrix[22, vci["MT"]] = -1 / v["sigma_T"]
        policy_vector[22] = -(1 - 1 / v["sigma_T"]) * dp["T_MT"]

        # foc: Y wrt EpsY
        coef_matrix[23, pci["p_Y"]] = 1
        coef_matrix[23, pci["p_Eps"]] = -1
        coef_matrix[23, vci["Y"]] = 1 / v["sigma_Y"]
        coef_matrix[23, vci["Eps_Y"]] = -1 / v["sigma_Y"]
        policy_vector[23] = -(1 - 1 / v["sigma_Y"]) * dp["Y_EpsY"]

        # foc: Y wrt MY
        coef_matrix[24, pci["p_Y"]] = 1
        coef_matrix[24, pci["p_MY"]] = -1
        coef_matrix[24, vci["Y"]] = 1 / v["sigma_Y"]
        coef_matrix[24, vci["MY"]] = -1 / v["sigma_Y"]
        policy_vector[24] = -(1 - 1 / v["sigma_Y"]) * dp["Y_MY"]

        # foc: Fi wrt E_Fi
        coef_matrix[25, pci["p_Fi"]] = 1
        coef_matrix[25, pci["p_E"]] = -1
        coef_matrix[25, vci["Fi"]] = 1 / v["sigma_Fi"]
        coef_matrix[25, vci["E_Fi"]] = -1 / v["sigma_Fi"]
        policy_vector[25] = -(1 - 1 / v["sigma_Fi"]) * dp["Fi_EFi"]

        # foc: Fi wrt MFi
        coef_matrix[26, pci["p_Fi"]] = 1
        coef_matrix[26, pci["p_MFi"]] = -1
        coef_matrix[26, vci["Fi"]] = 1 / v["sigma_Fi"]
        coef_matrix[26, vci["MFi"]] = -1 / v["sigma_Fi"]
        policy_vector[26] = -(1 - 1 / v["sigma_Fi"]) * dp["Fi_MFi"]

        # foc: fossil extraction
        # policy_vector[27] = 1.0/(1+v['tau_E'])
        coef_matrix[27, pci["p_E"]] = 1
        coef_matrix[27, vci["E"]] = -v["Lambda_E"]

        # foc: phosphate extraction
        coef_matrix[28, pci["p_Pho"]] = 1
        coef_matrix[28, vci["Pho"]] = -v["Lambda_Pho"]

        # foc: water extraction
        coef_matrix[29, pci["p_W"]] = 1
        coef_matrix[29, vci["W"]] = -v["Lambda_W"]

        # foc: renewables extraction
        coef_matrix[30, pci["p_R"]] = 1
        coef_matrix[30, vci["R"]] = -v["Lambda_R"]

        # foc: MA extraction
        coef_matrix[31, pci["p_MA"]] = 1
        coef_matrix[31, vci["MA"]] = -v["Lambda_MA"]

        # foc: MFi extraction
        coef_matrix[32, pci["p_MFi"]] = 1
        coef_matrix[32, vci["MFi"]] = -v["Lambda_MFi"]

        # foc: MP extraction
        coef_matrix[33, pci["p_MP"]] = 1
        coef_matrix[33, vci["MP"]] = -v["Lambda_MP"]

        # foc: MT extraction
        coef_matrix[34, pci["p_MT"]] = 1
        coef_matrix[34, vci["MT"]] = -v["Lambda_MT"]

        # foc: MY extraction
        coef_matrix[35, pci["p_MY"]] = 1
        coef_matrix[35, vci["MY"]] = -v["Lambda_MY"]

        # foc: U wrt A_F & Fi
        coef_matrix[36, pci["p_A"]] = 1
        coef_matrix[36, pci["p_Fi"]] = -1
        coef_matrix[36, vci["A_F"]] = 1 / v["sigma_F"]
        coef_matrix[36, vci["Fi"]] = -1 / v["sigma_F"]

        # foc: U wrt T & L_U
        coef_matrix[37, pci["p_T"]] = 1
        coef_matrix[37, pci["p_L"]] = -1
        coef_matrix[37, vci["T"]] = 1 / v["sigma_nF"]
        coef_matrix[37, vci["L_U"]] = -1 / v["sigma_nF"]

        # foc: U wrt T & Y
        coef_matrix[38, pci["p_T"]] = 1
        coef_matrix[38, pci["p_Y"]] = -1
        coef_matrix[38, vci["T"]] = 1 / v["sigma_nF"]
        coef_matrix[38, vci["Y"]] = -1 / v["sigma_nF"]

        # foc: U wrt A_F & Y
        coef_matrix[39, pci["p_A"]] = 1
        coef_matrix[39, pci["p_Y"]] = -1
        coef_matrix[39, vci["A_F"]] = (
            1 / v["sigma_F"] + (1 / v["sigma_U"] - 1 / v["sigma_F"]) * v["GammaF_AF"]
        )
        coef_matrix[39, vci["Y"]] = (
            -1 / v["sigma_nF"] - (1 / v["sigma_U"] - 1 / v["sigma_nF"]) * v["GammanF_Y"]
        )
        coef_matrix[39, vci["Fi"]] = (1 / v["sigma_U"] - 1 / v["sigma_F"]) * v[
            "GammaF_Fi"
        ]
        coef_matrix[39, vci["T"]] = (
            -(1 / v["sigma_U"] - 1 / v["sigma_nF"]) * v["GammanF_T"]
        )
        coef_matrix[39, vci["L_U"]] = (
            -(1 / v["sigma_U"] - 1 / v["sigma_nF"]) * v["GammanF_LU"]
        )

        # foc: Budget
        coef_matrix[40, pci["p_A"]] = v["GammaU_AF"]
        coef_matrix[40, vci["A_F"]] = v["GammaU_AF"]
        coef_matrix[40, pci["p_Y"]] = v["GammaU_Y"]
        coef_matrix[40, vci["Y"]] = v["GammaU_Y"]
        coef_matrix[40, pci["p_Fi"]] = v["GammaU_Fi"]
        coef_matrix[40, vci["Fi"]] = v["GammaU_Fi"]
        coef_matrix[40, pci["p_L"]] = v["GammaU_LU"]
        coef_matrix[40, vci["L_U"]] = v["GammaU_LU"]
        coef_matrix[40, pci["p_T"]] = v["GammaU_T"]
        coef_matrix[40, vci["T"]] = v["GammaU_T"]

        # print('policy_vector')
        return coef_matrix, policy_vector

    def gen_results(self, robust_check=False, biofuel_tax=0):

        sigma_U = self.sigma_U
        sigma_F = self.sigma_F
        sigma_nF = self.sigma_nF
        sigma_A = self.sigma_A
        sigma_P = self.sigma_P
        sigma_nLA = self.sigma_nLA
        sigma_Eps = self.sigma_Eps
        sigma_Fi = self.sigma_Fi
        sigma_T = self.sigma_T
        sigma_Y = self.sigma_Y
        Lambda_R = self.Lambda_R
        Lambda_E = self.Lambda_E
        Lambda_W = self.Lambda_W
        Lambda_Pho = self.Lambda_Pho
        Lambda_M = self.Lambda_M
        Q_LA = self.Q_LA
        Q_LT = self.Q_LT
        Q_AB = self.Q_AB
        Q_EpsA = self.Q_EpsA
        Q_EP = self.Q_EP
        Q_EFi = self.Q_EFi
        GammaU_F = self.GammaU_F
        GammaF_Fi = self.GammaF_Fi
        GammanF_Y = self.GammanF_Y
        GammanF_LU = self.GammanF_LU
        GammaA_LA = self.GammaA_LA
        GammanLA_P = self.GammanLA_P
        GammanLA_W = self.GammanLA_W
        GammaP_EP = self.GammaP_EP
        GammaEps_AB = self.GammaEps_AB
        GammaEps_EEps = self.GammaEps_EEps
        GammaFi_EFi = self.GammaFi_EFi
        GammaT_LT = self.GammaT_LT
        GammaY_EpsY = self.GammaY_EpsY
        GammanLA_EpsA = self.GammanLA_EpsA
        GammaP_Pho = self.GammaP_Pho
        V_T = self.V_T
        V_A = self.V_A
        tau_E = self.tau_E
        Lambda_MA = (
            self.Lambda_M
        )  # 1/1.7        # supply elast. intermediates to agriculture
        Lambda_MT = self.Lambda_M  # supply elast. intermediates to timber
        Lambda_MY = self.Lambda_M  # supply elast. intermediates to final goods
        Lambda_MP = self.Lambda_M  # supply elast. intermediates to fertilizers
        Lambda_MFi = self.Lambda_M  # supply elast. intermediates to fisheries

        # quantity shares (e.g. Q_LA = LA/L)
        Q_LU = 1 - Q_LT - Q_LA  # share of land used for recreation
        # Q_EP = 1-Q_EEps-Q_EFi    # share of fossil fuel used for fertilizer prod.

        Q_EEps = 1 - Q_EFi - Q_EP  # share of fossil fuel used for fisheries prod.
        self.Q_EEps = Q_EEps

        Q_AF = 1 - Q_AB  # share of agri. prod. used for food prod.
        Q_EpsY = 1 - Q_EpsA  # share of energy used for final goods prod.

        # factor shares (Gamma)
        GammaU_nF = 1 - GammaU_F  # factor share non-food (utility)
        GammaF_AF = 1 - GammaF_Fi  # factor share agricultural (food)
        GammanF_T = 1 - GammanF_LU - GammanF_Y  # factor share timber (non-food)
        GammaA_nLA = 1 - GammaA_LA  # factor share non-land (agric. prod)

        GammaEps_R = (
            1 - GammaEps_AB - GammaEps_EEps
        )  # factor share renewables (energy services prod.)
        GammaFi_MFi = (
            1 - GammaFi_EFi
        )  # factor share intermediates (energy services prod.)
        GammaT_MT = 1 - GammaT_LT  # factor share intermediates (energy services prod.)
        GammaY_MY = (
            1 - GammaY_EpsY
        )  # factor share intermediates (energy services prod.)
        GammanLA_MA = (
            1 - GammanLA_W - GammanLA_P - GammanLA_EpsA
        )  # factor share intermediates (non-land)
        GammaP_MP = (
            1 - GammaP_EP - GammaP_Pho
        )  # factor share intermediates (fertilizer prod.)

        GammaT_LTLT = GammaT_LT - 1
        GammaY_EpsYEpsY = GammaY_EpsY - 1

        GammaA_P = GammaA_nLA * GammanLA_P
        GammaA_W = GammaA_nLA * GammanLA_W
        GammaA_EpsA = GammaA_nLA * GammanLA_EpsA
        GammaU_AF = GammaU_F * GammaF_AF
        GammaU_Fi = GammaU_F * GammaF_Fi
        GammaU_Y = GammaU_F * GammanF_Y
        GammaU_LU = GammaU_F * GammanF_LU
        GammaU_T = GammaU_F * GammanF_T
        GammaA_MA = GammaA_nLA * GammanLA_MA

        local_variables = locals()
        local_variables.pop("robust_check", None)
        local_variables.pop("biofuel_tax", None)
        local_variables.pop("var_desc_dict", None)
        local_variables.pop("price_desc_dict", None)

        # print(local_variables)

        lv_lists, lv_strings = {}, {}
        for k, val in iter(local_variables.items()):
            if isinstance(val, list):
                if robust_check:
                    lv_lists[k] = val
                else:
                    # third param in list the mean
                    lv_strings[k] = val[2]
            else:
                lv_strings[k] = val

        # example: [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
        distinct_combination_sets = list(product(range(2), repeat=len(lv_lists)))
        results_matrix = np.zeros((41, len(distinct_combination_sets)))
        mean_results = np.zeros((41, 1))

        # print distinct_combination_sets
        # result_set = []
        # Variable order for columns of matrix an rows in the outcome vector:
        # L_A, L_T, L_U, E, E_eps, E_P, E_Fi, A, A_B, A_F, Eps, Eps_A, Eps_Y, P, W, Pho, R, Fi, T, Y, MA, MT, MFi, MY, MP
        vci = {
            "L_A": 0,
            "L_T": 1,
            "L_U": 2,
            "E": 3,
            "E_Eps": 4,
            "E_P": 5,
            "E_Fi": 6,
            "A": 7,
            "A_B": 8,
            "A_F": 9,
            "Eps": 10,
            "Eps_A": 11,
            "Eps_Y": 12,
            "P": 13,
            "W": 14,
            "Pho": 15,
            "R": 16,
            "Fi": 17,
            "T": 18,
            "Y": 19,
            "MA": 20,
            "MT": 21,
            "MFi": 22,
            "MY": 23,
            "MP": 24,
        }
        pci = {
            "p_A": 25,
            "p_E": 26,
            "p_Eps": 27,
            "p_Fi": 28,
            "p_L": 29,
            "p_MA": 30,
            "p_MFi": 31,
            "p_MP": 32,
            "p_MT": 33,
            "p_MY": 34,
            "p_P": 35,
            "p_Pho": 36,
            "p_R": 37,
            "p_T": 38,
            "p_W": 39,
            "p_Y": 40,
        }

        # print(prod_change_dict)
        lv_strings["vci"] = vci
        lv_strings["pci"] = pci
        lv_strings["prod_change_dict"] = self.prod_change_dict
        counter = 0
        for combo in distinct_combination_sets:
            combo_id = 0
            lc = {}
            for key, val in iter(lv_lists.items()):
                lc[key] = val[combo[combo_id]]
                combo_id += 1
            p = lv_strings.copy()
            p.update(lc)
            coef_matrix, policy_vector = self.gen_coef_matrix(p, biofuel_tax)
            # Invert cooeficient matrix and multiply with policy vector
            results = np.dot(np.linalg.inv(coef_matrix), policy_vector)
            results_matrix[:, counter] = results[:, 0]
            counter += 1
        # print('results: ', results_matrix[:,counter-2])
        # print('counter: ', counter)
        max_results = np.amax(results_matrix, axis=1)
        min_results = np.amin(results_matrix, axis=1)
        lc = {}
        for key, val in iter(lv_lists.items()):
            lc[key] = val[2]
            combo_id += 1
        p = lv_strings.copy()
        p.update(lc)

        coef_matrix, policy_vector = self.gen_coef_matrix(p, biofuel_tax)

        # Invert cooeficient matrix and multiply with policy vector
        mean_results = np.dot(np.linalg.inv(coef_matrix), policy_vector)
        # print(mean_results)

        # display results in table
        sol_var_list = []
        for key, var in self.var_desc_dict.items():
            var_desc = var[0] + " " + "$\text{" + var[1] + "}$"
            sol_var_list.append(
                {
                    "description": var_desc,
                    "max value": max_results[vci[key]],
                    "min value": min_results[vci[key]],
                    "mean value": mean_results[vci[key]][0],
                }
            )

        # display results in table
        sol_price_list = []
        for key, var in self.price_desc_dict.items():
            var_desc = var[0] + " " + "$\text{" + var[1] + "}$"
            sol_price_list.append(
                {
                    "description": var_desc,
                    "max value": results[pci[key]][0],
                    "min value": results[pci[key]][0],
                    "mean value": mean_results[pci[key]][0],
                }
            )

        df_quantities = pd.DataFrame(sol_var_list)
        df_prices = pd.DataFrame(sol_price_list)

        return df_quantities, df_prices

    def pb_effects(self, df_q):
        # 'Aerosol effect': the net change in radiative forcing from imposing a carbon tax (note: a positive value implies a increase in radiative forcing aka a decrease of AOD)
        AOD_global_biomass = 0.0022015015814673216
        AOD_global_fbf = 0.038414748418532686
        Q_bio = 95371 / (
            1000 * (4662.1 + 3309.4 + 3772.1) + 95371
        )  # Share of biofuels in tot biofuel+fossil prod.
        Q_ff = 1 - Q_bio
        df_q.loc[:, "Aerosol effect"] = 0
        df_q.loc[2, "Aerosol effect"] = (
            -AOD_global_biomass * df_q.loc[2, "mean value"]
        )  # Natural land
        df_q.loc[4, "Aerosol effect"] = (
            AOD_global_fbf * df_q.loc[4, "mean value"] * Q_ff * self.Q_EEps
        )  # Fossil fuel consump. energy services
        df_q.loc[5, "Aerosol effect"] = (
            AOD_global_fbf * df_q.loc[5, "mean value"] * Q_ff * self.Q_EP
        )  # Fossil fuel consump.  Fertilizer Prod
        df_q.loc[6, "Aerosol effect"] = (
            AOD_global_fbf * df_q.loc[6, "mean value"] * Q_ff * self.Q_EFi
        )  # Fossil fuel consump. fisheries
        df_q.loc[8, "Aerosol effect"] = (
            AOD_global_fbf * df_q.loc[8, "mean value"] * Q_bio
        )  # Biofuel fuel prod

        # CLIMATE CHANGE
        total_emissions = 44.153
        df_q.loc[:, "CO2 effect"] = 0
        df_q.loc[2, "CO2 effect"] = (
            -1 * 5.387 * df_q.loc[2, "mean value"] / total_emissions
        )  # change in natural land
        df_q.loc[3, "CO2 effect"] = (
            3.98 * df_q.loc[3, "mean value"] / total_emissions
        )  # fossil fuel extraction
        df_q.loc[4, "CO2 effect"] = (
            25.960 * df_q.loc[4, "mean value"] / total_emissions
        )  # Fossil-Fuel Use Energy Serv.
        df_q.loc[5, "CO2 effect"] = (
            0.575 * df_q.loc[5, "mean value"] / total_emissions
        )  # Fossils in fertilizer production
        df_q.loc[6, "CO2 effect"] = (
            0.14 * df_q.loc[6, "mean value"] / total_emissions
        )  # Fossils in fisheries
        df_q.loc[7, "CO2 effect"] = (
            6.093 * df_q.loc[7, "mean value"] / total_emissions
        )  # Emissions from Agriculture
        df_q.loc[19, "CO2 effect"] = (
            1.9 * df_q.loc[19, "mean value"] / total_emissions
        )  # Fossil-Fuel Use Final goods

        # BIODIVERSITY
        total_num_threats = 25779  # Non-mutually exclusive sum
        df_q.loc[:, "biodiv-val"] = 0
        df_q.loc[3, "biodiv-val"] = 56  # Energy production (OIL and GAS)
        df_q.loc[16, "biodiv-val"] = 56  # Energy production (Renewable Energy)
        df_q.loc[17, "biodiv-val"] = 1118  # Over exploitation (Fishing)
        df_q.loc[18, "biodiv-val"] = 4049  # Over exploitation (Logging)
        df_q.loc[7, "biodiv-val"] = 5407 - 112  # Agricultural activity
        df_q.loc[13, "biodiv-val"] = 1523  # Pollution (Agriculture)
        df_q.loc[19, "biodiv-val"] = (
            907 + (1901 - 1523) + 236 + 1219 + 833
        )  # Urban dev. (industrial) + Pollution (except Agriculture) + Human dist. (work) + Transport + Energy production (Mining)
        df_q.loc[:, "Biodiv. effect"] = (
            df_q["mean value"] * df_q["biodiv-val"] / total_num_threats
        )
        df_q.loc[:, "Biodiv. climate effect"] = (
            0 * df_q["CO2 effect"] * 1688 / total_num_threats
        )
        df_q.loc[:, "Biodiv. incl. climate effect"] = 100 * (
            (1 + df_q.loc[:, "Biodiv. effect"] / 100)
            * (1 + df_q.loc[:, "Biodiv. climate effect"] / 100)
            - 1
        )
        df_q = df_q.drop(columns=["biodiv-val"])
        df_q = df_q.drop(columns=["Biodiv. effect", "Biodiv. climate effect"])

        # BIOGEOCHEMICAL
        df_q.loc[:, "Biogeochem. effect"] = 0
        df_q.loc[5, "Biogeochem. effect"] = df_q.loc[5, "mean value"]
        df_q.loc[15, "Biogeochem. effect"] = df_q.loc[15, "mean value"]

        # WATER
        df_q.loc[:, "Freshwater effect"] = 0
        df_q.loc[14, "Freshwater effect"] = df_q.loc[14, "mean value"]

        # OCEAN ACID
        df_q.loc[:, "Ocean acid. effect"] = 0
        df_q.loc[:, "Ocean acid. effect"] = df_q.loc[:, "CO2 effect"]

        # LAND USE
        df_q.loc[:, "Land-use effect"] = 0
        df_q.loc[2, "Land-use effect"] = df_q.loc[2, "mean value"]

        # OZONE
        df_q.loc[:, "Ozone effect"] = 0
        df_q.loc[3, "Ozone effect"] = (
            -1 if df_q.loc[3, "mean value"] < 0 else 1
        )  # N02 fossil fuels
        df_q.loc[7, "Ozone effect"] = (
            -1 if df_q.loc[7, "mean value"] < 0 else 1
        )  #  NO2 from agric.
        df_q.loc[8, "Ozone effect"] = (
            -1 if df_q.loc[8, "mean value"] < 0 else 1
        )  #  NO2 from biofuel burning.
        df_q.loc[19, "Ozone effect"] = (
            -1 if df_q.loc[19, "mean value"] < 0 else 1
        )  # NO2 from industry.

        # CHEMICALS
        df_q.loc[:, "Chem. effect"] = 0
        df_q.loc[3, "Chem. effect"] = (
            -1 * int(df_q.loc[3, "mean value"] < 0) + df_q.loc[3, "Chem. effect"]
        )  # fossil fuels
        df_q.loc[7, "Chem. effect"] = (
            -1 * int(df_q.loc[7, "mean value"] < 0) + df_q.loc[7, "Chem. effect"]
        )  # agric.
        df_q.loc[19, "Chem. effect"] = (
            -1 * int(df_q.loc[19, "mean value"] < 0) + df_q.loc[19, "Chem. effect"]
        )  # industry.

        return df_q


    def pb_food_price_effect(self, df_prices):
        # Food price effect (% change in food price index)
        price_change_fisheries = df_prices.at[3, "mean value"]
        #print("Price change fish:", df_prices.at[3, "description"])
        
        price_change_agric = df_prices.at[0, "mean value"]
        #print("Price change agri:", df_prices.at[0, "description"])
        price_change_food = price_change_fisheries*self.GammaF_Fi + (1-self.GammaF_Fi)*price_change_agric
        
        return price_change_food
    
    def pb_food_quantity_effect(self, df_quantities):
        # Food price effect (% change in food price index)
        quantity_change_agric = df_quantities.at[9, "mean value"]
        #print("Quant change agri:", df_quantities.at[9, "description"])

        quantity_change_fisheries = df_quantities.at[17, "mean value"]
        #print("Quant change fish:", df_quantities.at[17, "description"])
        price_change_food = quantity_change_fisheries*self.GammaF_Fi + (1-self.GammaF_Fi)*quantity_change_agric
        
        return price_change_food

def solve(params):
    # params: params.df_typing_formatting.to_dict('records')

    if params:
        model_params = {row["keys"]: row["values"] for row in params}
        # print(model_params)
        sm = SolveModel(model_params)
        df_carbontax_quantities, df_carbontax_prices = sm.gen_results(
            robust_check=False, biofuel_tax=0
        )
        df_carbontax_quantities = sm.pb_effects(df_carbontax_quantities)
        for idx, row in df_carbontax_quantities.iterrows():
            df_carbontax_quantities.at[idx, "description"] = re.findall(
                r"\{\(([\w\s\.\-]*)", row["description"]
            )[0].title()

        df_carbontax_quantities = df_carbontax_quantities.drop(
            columns=["max value", "min value"]
        )
        df_carbontax_quantities.sum()
        return (
            df_carbontax_quantities  # [["description", "mean value", "Aerosol effect"]]
        )
    return None


typology = {
    r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Production}}": [],
    r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Inputs}}": [],
    r"\multicolumn{5}{l}{\\textit{Energy-related sectors and  Services}}": [],
    r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}": [],
    r"\multicolumn{5}{l}{\\textit{Others}}": [],
}


table_text = {
    "L_A": (
        r"\hspace{0.2cm}Land-Share Agriculture",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Inputs}}",
    ),
    "L_T": (
        r"\hspace{0.2cm}Land-Share Timber",
        r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}",
    ),
    "L_U": (
        r"\hspace{0.2cm}Land-Share Natural",
        r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}",
    ),
    "E": (
        r"\hspace{0.2cm}Fossil-Fuel Extraction",
        r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}",
    ),
    "E_Eps": (
        r"\hspace{0.2cm}Fossil-Fuel in Energy Services",
        r"\multicolumn{5}{l}{\\textit{Energy-related sectors and  Services}}",
    ),
    "E_P": (
        r"\hspace{0.2cm}Fossil-Fuel in Fertilizer Prod.",
        r"\multicolumn{5}{l}{\\textit{Energy-related sectors and  Services}}",
    ),
    "E_Fi": (
        r"\hspace{0.2cm}Fossil-Fuel in Fisheries",
        r"\multicolumn{5}{l}{\\textit{Energy-related sectors and  Services}}",
    ),
    "A": (
        r"\hspace{0.2cm}Total",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Production}}",
    ),
    "A_B": (
        r"\hspace{0.2cm}Biofuels",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Production}}",
    ),
    "A_F": (
        r"\hspace{0.2cm}Food",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Production}}",
    ),
    "Eps": (
        r"\hspace{0.2cm}Energy Services",
        r"\multicolumn{5}{l}{\\textit{Energy-related sectors and  Services}}",
    ),
    "Eps_A": (
        r"\hspace{0.2cm}Energy in Agriculture",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Inputs}}",
    ),
    "Eps_Y": (
        r"\hspace{0.2cm}Energy in Manufacturing",
        r"\multicolumn{5}{l}{\\textit{Energy-related sectors and  Services}}",
    ),
    "P": (
        r"\hspace{0.2cm}Fertilizer Production",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Inputs}}",
    ),
    "W": (
        r"\hspace{0.2cm}Water Production",
        r"\multicolumn{5}{l}{\\textit{Agricultural Sector: Inputs}}",
    ),
    "Pho": (
        r"\hspace{0.2cm}Phosphate Extraction",
        r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}",
    ),
    "R": (
        r"\hspace{0.2cm}Renewables Production",
        r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}",
    ),
    "Fi": (
        r"\hspace{0.2cm}Fisheries Production",
        r"\multicolumn{5}{l}{\\textit{Extractive Sectors}}",
    ),
    "T": (r"\hspace{0.2cm}Timber Production", r"\multicolumn{5}{l}{\\textit{Others}}"),
    "Y": (r"\hspace{0.2cm}Manufacturing", r"\multicolumn{5}{l}{\\textit{Others}}"),
}
