// This program implements Conway's Game of Life.
// It uses newlib-nano for minimal C library support and  dynamic memory allocation.
// The state of the board is shown on terminal using ANSI escape codes.
// It accepts an optional command-line parameter for the seed of the random number generator.

#include <stdio.h>
#include <stdlib.h>

#define ROWS 20
#define COLS 40
#define STEPS 1000

int **alloc_board() {
    int **board = malloc(ROWS * sizeof(int *));
    if (board == NULL) {
        printf("Memory allocation failed (row pointers)\n");
        return NULL;
    }
    for (int i = 0; i < ROWS; i++) {
        board[i] = calloc(COLS, sizeof(int));
        if (board[i] == NULL) {
            printf("Memory allocation failed (column)\n");
            return NULL;
        }
    }
    return board;
}

void free_board(int **board) {
    for (int i = 0; i < ROWS; i++)
        free(board[i]);
    free(board);
}

void random_init(int **board, int seed) {
    srand(seed);
    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLS; j++)
            board[i][j] = rand() % 2;
    }
}

int count_neighbors(int **board, int row, int col) {
    int sum = 0;
    for (int i = -1; i <= 1; ++i)
        for (int j = -1; j <= 1; ++j)
            if (!(i == 0 && j == 0)) {
                int r = row + i;
                int c = col + j;
                if (r >= 0 && r < ROWS && c >= 0 && c < COLS)
                    sum += board[r][c];
            }
    return sum;
}

void step(int **curr, int **next) {
    for (int i = 0; i < ROWS; ++i)
        for (int j = 0; j < COLS; ++j) {
            int alive = curr[i][j];
            int neighbors = count_neighbors(curr, i, j);

            if (alive && (neighbors == 2 || neighbors == 3))
                next[i][j] = 1;
            else if (!alive && neighbors == 3)
                next[i][j] = 1;
            else
                next[i][j] = 0;
        }
}

void print_board(int **board) {
    // Move cursor to top-left and clear screen
    printf("\033[H");

    for (int i = 0; i < ROWS; ++i) {
        for (int j = 0; j < COLS; ++j)
            if (board[i][j])
                printf("\033[32mO\033[0m");  // Green 'O', then reset
            else
                putchar('.');
        putchar('\n');
    }
    fflush(stdout);
}

int main(int argc, char *argv[]) {
    int rng_seed = 42;

    if (argc > 1)
        rng_seed = atoi(argv[1]);

    int **current = alloc_board();
    int **next = alloc_board();

    random_init(current, rng_seed);

    printf("\033[2J");

    for (int step_num = 0; step_num < STEPS; ++step_num) {
        print_board(current);
        printf("generation %05d\n", step_num);
        step(current, next);

        // Swap pointers
        int **temp = current;
        current = next;
        next = temp;
    }

    free_board(current);
    free_board(next);

    return 0;
}
