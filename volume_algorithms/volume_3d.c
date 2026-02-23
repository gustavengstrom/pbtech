#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define ROWS 6
#define COLS 4

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
void exclude_row_col(double Abtilde[ROWS][COLS], int num_rows, int num_cols, int row_to_exclude, int col_to_exclude, double result[ROWS][COLS]) {
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


// Function to calculate the volume recursively
double volume_calculation(double Abmatrix[ROWS][COLS], int num_rows, int num_cols) {
    int non_zero_mask[ROWS];
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
    double Abmatrix_filtered[ROWS][COLS];
    int new_rows = 0;
    for (int i = 0; i < num_rows; i++) {
        if (non_zero_mask[i]) {
            for (int j = 0; j < num_cols; j++) {
                Abmatrix_filtered[new_rows][j] = Abmatrix[i][j];
            }
            new_rows++;
        }
    }

    if (new_rows == 0) {
        return 0;
    }

    // Volume computation logic for 3 columns (i.e., a 2D problem)
    if (num_cols == 3) {
        double vol_terms[ROWS] = {0};
        int vol_count = 0;

        for (int i = 0; i < new_rows; i++) {
            double Abrow_i[COLS];
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

            double max_terms[ROWS] = {0}, min_terms[ROWS] = {0};
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
            // printf("vol_term: %f\n", vol_term);
            vol_terms[vol_count++] = vol_term;
        }

        double total_volume = 0;
        for (int i = 0; i < vol_count; i++) {
            total_volume += vol_terms[i];
        }
        // printf("2d volume: %f\n", total_volume);
        return total_volume / 2;
    } else {
        // Volume computation logic for higher dimensions
        double volume_terms[ROWS] = {0};
        int volume_count = 0;

        for (int i = 0; i < new_rows; i++) {
            double Abtilde[ROWS][COLS] = {0};
            double Abrow_i[COLS];
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
            exclude_row_col(Abtilde, new_rows, num_cols, i, ti, Abtilde);

            // Print the matrix
            // for (int i = 0; i < ROWS; i++) {
            //     for (int j = 0; j < COLS; j++) {
            //         printf("%6.2f ", Abtilde[i][j]);
            //     }
            //     printf("\n");
            // }

            double volume_term = volume_calculation(Abtilde, new_rows - 1, num_cols - 1);
            if (volume_term) {
                volume_terms[volume_count++] = Abrow_i[0] * volume_term / fabs(Abrow_i[ti]);
            }
        }

        double final_volume = 0;
        for (int i = 0; i < volume_count; i++) {
            final_volume += volume_terms[i];
        }

        return final_volume / (num_cols - 1);
    }
}

int main() {
    double constraints[ROWS][COLS] = {
        {2, 1, -2, 2},
        {3, -1, 4, 2},
        {4, 1, 1, -2},
        {0, -1, 0, 0},
        {0, 0, -1, 0},
        {0, 0, 0, -1}
    };
    // double constraints[ROWS][COLS] = {
    //     {2, 2, -2},
    //     {3, -4, -2},
    //     {4, -1, 2},
    //     {0, 1, 0},
    //     {0, 0, 1}
    // };

    printf("###################\n");
    printf("###### START ######\n");
    printf("###################\n");

    clock_t start = clock();

    double volume = volume_calculation(constraints, ROWS, COLS);

    printf("Final volume: %f\n", volume);
    printf("Run time: %f seconds\n", (double)(clock() - start) / CLOCKS_PER_SEC);

    return 0;
}
