#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>
#include <math.h>

#define MAX_ROWS 100  // Adjust as necessary for large files
#define MAX_COLS 10   // Adjust as necessary based on input file structure

typedef struct {
    double data[MAX_ROWS][MAX_COLS];
    int rows;
    int cols;
} Matrix;

void initialize_matrix(Matrix *m, int rows, int cols) {
    m->rows = rows;
    m->cols = cols;
    memset(m->data, 0, sizeof(m->data));
}


// Function to read matrix constraints from a file dynamically
void read_constraints_from_file(const char *filename, Matrix *m) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "Error opening file: %s\n", filename);
        exit(1);
    }

    char line[256];
    int row = 0;
    int col_count = 0;
    int is_first_line = 1;

    while (fgets(line, sizeof(line), file)) {
        // Skip the first line, if needed
        if (is_first_line) {
            is_first_line = 0;
            continue;
        }

        // Remove newline characters
        line[strcspn(line, "\n")] = 0;
        if (strlen(line) == 0) continue;  // Skip empty lines

        // Determine column count dynamically from the first valid line
        if (col_count == 0) {
            char *token = strtok(line, " ");
            while (token != NULL) {
                col_count++;
                token = strtok(NULL, " ");
            }
            m->cols = col_count;  // Set the number of columns
        }

        // Parse the row into matrix
        int col = 0;
        char *token = strtok(line, " ");
        while (token != NULL && col < m->cols) {
            m->data[row][col++] = atof(token);  // Using atof to handle float conversion
            token = strtok(NULL, " ");
        }

        row++;
    }

    fclose(file);

    // Update matrix rows based on the number of rows read
    m->rows = row;
}

// Function to print the matrix for debugging
void print_matrix(const Matrix *m) {
    printf("Matrix (%d x %d):\n", m->rows, m->cols);
    for (int i = 0; i < m->rows; i++) {
        for (int j = 0; j < m->cols; j++) {
            printf("%f ", m->data[i][j]);
        }
        printf("\n");
    }
}

// Function to process (negate) the constraints as in your Python code
void process_constraints(Matrix *m) {
    // Negating all columns except the first one
    for (int i = 0; i < m->rows; i++) {
        for (int j = 1; j < m->cols; j++) {
            m->data[i][j] *= -1;
        }
    }
}

double volume_calculation(Matrix *Abmatrix) {
    double vol_terms[MAX_ROWS] = {0};
    int vol_count = 0;

    for (int i = 0; i < Abmatrix->rows; i++) {
        double *Abrow_i = Abmatrix->data[i];
        if (Abrow_i[0] == 0) continue;

        printf("Processing row %d: ", i);
        for (int j = 0; j < Abmatrix->cols; j++) {
            printf("%f ", Abrow_i[j]);
        }
        printf("\n");

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

        printf("Row %d: min_part = %f, max_part = %f\n", i, min_part, max_part);

        vol_terms[vol_count++] = Abrow_i[0] * fmax(0, min_part - max_part) / fabs(Abrow_i[ti]);
    }

    double total_volume = 0;
    for (int i = 0; i < vol_count; i++) {
        total_volume += vol_terms[i];
    }

    printf("Total volume terms: %f\n", total_volume);
    return total_volume / 2.0;
}

int main() {
    printf("\n###################\n###### START ######\n###################\n");

    clock_t start_time = clock();

    // Initialize the matrix for constraints
    Matrix constraints;
    initialize_matrix(&constraints, MAX_ROWS, MAX_COLS);

    // Read constraints from the file
    const char *filename = "./latte/pbtech/lasserre_test.hrep.latte";
    read_constraints_from_file(filename, &constraints);

    // Print matrix after reading
    printf("Matrix after reading from file:\n");
    print_matrix(&constraints);

    // Process the constraints (negation)
    process_constraints(&constraints);

    // Print matrix after processing
    printf("Matrix after processing (negation):\n");
    print_matrix(&constraints);

    // Calculate the volume
    double final_vol = volume_calculation(&constraints);
    printf("Final volume: %f\n", final_vol);

    clock_t end_time = clock();
    printf("Run time: %f seconds\n", (double)(end_time - start_time) / CLOCKS_PER_SEC);

    return 0;
}