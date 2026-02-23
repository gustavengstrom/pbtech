#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// Min and max functions
double min(double* array, int size) {
    double min_value = array[0];
    for (int i = 1; i < size; i++) {
        if (array[i] < min_value) {
            min_value = array[i];
        }
    }
    return min_value;
}

double max(double* array, int size) {
    double max_value = array[0];
    for (int i = 1; i < size; i++) {
        if (array[i] > max_value) {
            max_value = array[i];
        }
    }
    return max_value;
}

// Create a new matrix with the i-th row and ti-th column excluded
void exclude_row_col(double** Abtilde, int num_rows, int num_cols, int row_to_exclude, int col_to_exclude, double** result) {
    int row_idx = 0, col_idx = 0;

    for (int i = 0; i < num_rows; i++) {
        if (i == row_to_exclude) {
            continue;  // Skip the row to exclude
        }
        col_idx = 0;
        for (int j = 0; j < num_cols; j++) {
            if (j == col_to_exclude) {
                continue;  // Skip the column to exclude
            }
            result[row_idx][col_idx] = Abtilde[i][j];
            col_idx++;
        }
        row_idx++;
    }
}

// Function to free dynamically allocated memory
void free_matrix(double** matrix, int num_rows) {
    for (int i = 0; i < num_rows; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

// Function to calculate the volume recursively
double volume_calculation(double** Abmatrix, int num_rows, int num_cols) {
    int non_zero_mask[num_rows];
    int valid_rows = 0;

    // Create the non-zero mask
    for (int i = 0; i < num_rows; i++) {
        int all_zero = 1;
        for (int j = 1; j < num_cols; j++) {
            if (Abmatrix[i][j] != 0) {
                all_zero = 0;
                break;
            }
        }
        non_zero_mask[i] = !all_zero;
        if (non_zero_mask[i]) {
            valid_rows++;
        }
    }

    // Filter out rows where the mask is zero
    double** Abmatrix_filtered = (double**)malloc(valid_rows * sizeof(double*));
    int new_rows = 0;
    for (int i = 0; i < num_rows; i++) {
        if (non_zero_mask[i]) {
            Abmatrix_filtered[new_rows] = (double*)malloc(num_cols * sizeof(double));
            for (int j = 0; j < num_cols; j++) {
                Abmatrix_filtered[new_rows][j] = Abmatrix[i][j];
            }
            new_rows++;
        }
    }

    if (new_rows == 0) {
        free_matrix(Abmatrix_filtered, valid_rows);
        return 0;
    }

    if (num_cols == 3) {
        double vol_terms[valid_rows];
        int vol_count = 0;

        for (int i = 0; i < new_rows; i++) {
            double Abrow_i[num_cols];
            for (int j = 0; j < num_cols; j++) {
                Abrow_i[j] = Abmatrix_filtered[i][j];
            }

            if (Abrow_i[0] == 0) continue;

            int ti = -1;
            for (int idx = 1; idx < num_cols; idx++) {
                if (Abrow_i[idx] != 0) {
                    ti = idx;
                    break;
                }
            }

            double max_terms[valid_rows], min_terms[valid_rows];
            int max_count = 0, min_count = 0;

            for (int k = 0; k < new_rows; k++) {
                if (k == i) continue;
                double beta = 0, alpha = 0;

                for (int j = 0; j < num_cols; j++) {
                    if (j == 0) {
                        beta = Abmatrix_filtered[k][j] - (Abmatrix_filtered[k][ti] * Abrow_i[0] / Abrow_i[ti]);
                    } else if (j != ti) {
                        alpha = Abmatrix_filtered[k][j] - (Abmatrix_filtered[k][ti] * Abrow_i[j] / Abrow_i[ti]);
                        double xj = beta / alpha;
                        if (alpha < 0) {
                            max_terms[max_count++] = xj;
                        } else {
                            min_terms[min_count++] = xj;
                        }
                    }
                }
            }

            double min_part = (min_count == 0) ? 0 : min(min_terms, min_count);
            double max_part = (max_count == 0) ? 0 : max(max_terms, max_count);
            double vol_term = Abrow_i[0] * fmax(0, min_part - max_part) / fabs(Abrow_i[ti]);
            vol_terms[vol_count++] = vol_term;
        }

        double total_volume = 0;
        for (int i = 0; i < vol_count; i++) {
            total_volume += vol_terms[i];
        }

        free_matrix(Abmatrix_filtered, valid_rows);
        return total_volume / 2;
    } else {
        // Volume computation logic for higher dimensions
        double volume_terms[valid_rows];
        int volume_count = 0;

        for (int i = 0; i < new_rows; i++) {
            double** Abtilde = (double**)malloc(new_rows * sizeof(double*));
            for (int k = 0; k < new_rows; k++) {
                Abtilde[k] = (double*)malloc(num_cols * sizeof(double));
            }

            double Abrow_i[num_cols];
            for (int j = 0; j < num_cols; j++) {
                Abrow_i[j] = Abmatrix_filtered[i][j];
            }

            int ti = -1;
            for (int idx = 1; idx < num_cols; idx++) {
                if (Abrow_i[idx] != 0) {
                    ti = idx;
                    break;
                }
            }

            for (int k = 0; k < new_rows; k++) {
                if (k == i) continue;

                for (int j = 0; j < num_cols; j++) {
                    if (j == 0) {
                        Abtilde[k][j] = Abmatrix_filtered[k][j] - (Abmatrix_filtered[k][ti] * Abrow_i[j] / Abrow_i[ti]);
                    } else if (j != ti) {
                        Abtilde[k][j] = Abmatrix_filtered[k][j] - (Abmatrix_filtered[k][ti] * Abrow_i[j] / Abrow_i[ti]);
                    }
                }
            }

            // Exclude row i and column ti from Abtilde
            double** Abtilde_excluded = (double**)malloc((new_rows - 1) * sizeof(double*));
            for (int m = 0; m < new_rows - 1; m++) {
                Abtilde_excluded[m] = (double*)malloc((num_cols - 1) * sizeof(double));
            }
            exclude_row_col(Abtilde, new_rows, num_cols, i, ti, Abtilde_excluded);

            double volume_term = volume_calculation(Abtilde_excluded, new_rows - 1, num_cols - 1);
            if (volume_term) {
                volume_terms[volume_count++] = Abrow_i[0] * volume_term / fabs(Abrow_i[ti]);
            }

            free_matrix(Abtilde, new_rows);
            free_matrix(Abtilde_excluded, new_rows - 1);
        }

        double final_volume = 0;
        for (int i = 0; i < volume_count; i++) {
            final_volume += volume_terms[i];
        }

        free_matrix(Abmatrix_filtered, valid_rows);
        return final_volume / (num_cols - 1);
    }
}




int main() {
    FILE *file = fopen("./latte/pbtech/pb.hrep.latte", "r");
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    // Read the number of rows and columns from the first line
    int rows, cols;
    fscanf(file, "%d %d", &rows, &cols);

    // Dynamically allocate memory for the matrix
    double **constraints = (double **)malloc(rows * sizeof(double *));
    for (int i = 0; i < rows; i++) {
        constraints[i] = (double *)malloc(cols * sizeof(double));
    }

    // Read matrix values from the file
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            fscanf(file, "%lf", &constraints[i][j]);
        }
    }

    // Close the file
    fclose(file);

    printf("###################\n");
    printf("###### START ######\n");
    printf("###################\n");

    clock_t start = clock();

    // Calculate the volume using the dynamically allocated matrix
    double volume = volume_calculation(constraints, rows, cols);

    printf("Final volume: %f\n", volume);
    printf("Run time: %f seconds\n", (double)(clock() - start) / CLOCKS_PER_SEC);

    // Free dynamically allocated memory
    free_matrix(constraints, rows);

    return 0;
}
