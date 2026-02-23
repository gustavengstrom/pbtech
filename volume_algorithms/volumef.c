#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>
#include <math.h>

#define MAX_ROWS 5  // Number of rows based on your input
#define MAX_COLS 3  // Number of columns based on your input

typedef struct {
    double data[MAX_ROWS][MAX_COLS];
    int rows;
    int cols;
} Matrix;

void initialize_matrix(Matrix *m, double input[MAX_ROWS][MAX_COLS], int rows, int cols) {
    m->rows = rows;
    m->cols = cols;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            m->data[i][j] = input[i][j];
        }
    }
}

double volume_calculation(Matrix *Abmatrix) {
    double vol_terms[MAX_ROWS] = {0};
    int vol_count = 0;

    for (int i = 0; i < Abmatrix->rows; i++) {
        double *Abrow_i = Abmatrix->data[i];
        if (Abrow_i[0] == 0) continue;

        int ti = -1;
        for (int idx = 1; idx < Abmatrix->cols; idx++) {
            if (Abrow_i[idx] != 0) {
                ti = idx;
                break;
            }
        }

        double max_terms[MAX_ROWS] = {0};
        double min_terms[MAX_ROWS] = {0};
        int max_count = 0, min_count = 0;

        for (int k = 0; k < Abmatrix->rows; k++) {
            if (k == i) continue;

            double beta = Abmatrix->data[k][0] - Abmatrix->data[k][ti] * Abrow_i[0] / Abrow_i[ti];
            for (int j = 0; j < Abmatrix->cols; j++) {
                if (j == 0 || j == ti) continue;

                double alpha = Abmatrix->data[k][j] - Abmatrix->data[k][ti] * Abrow_i[j] / Abrow_i[ti];
                double xj = beta / alpha;

                if (alpha < 0) {
                    max_terms[max_count++] = xj;
                } else {
                    min_terms[min_count++] = xj;
                }
            }
        }

        double min_part = (min_count == 0) ? 0 : min_terms[0];
        for (int j = 1; j < min_count; j++) {
            if (min_terms[j] < min_part) {
                min_part = min_terms[j];
            }
        }

        double max_part = (max_count == 0) ? 0 : max_terms[0];
        for (int j = 1; j < max_count; j++) {
            if (max_terms[j] > max_part) {
                max_part = max_terms[j];
            }
        }

        vol_terms[vol_count++] = Abrow_i[0] * fmax(0, min_part - max_part) / fabs(Abrow_i[ti]);
    }

    double total_volume = 0;
    for (int i = 0; i < vol_count; i++) {
        total_volume += vol_terms[i];
    }

    return total_volume / 2.0;
}

int main() {
    printf("\n###################\n###### START ######\n###################\n");

    clock_t start_time = clock();

    // Initialize constraints based on your input
    double input[MAX_ROWS][MAX_COLS] = {
        {2, 2, -2},
        {3, -4, -2},
        {4, -1, 2},
        {0, 1, 0},
        {0, 0, 1}
    };

    Matrix constraints;
    initialize_matrix(&constraints, input, MAX_ROWS, MAX_COLS);

    double final_vol = volume_calculation(&constraints);
    printf("Final volume: %f\n", final_vol);

    clock_t end_time = clock();
    printf("Run time: %f seconds\n", (double)(end_time - start_time) / CLOCKS_PER_SEC);

    return 0;
}