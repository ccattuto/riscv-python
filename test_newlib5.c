// This example generates a random maze using the recursive backtracking algorithm.
// It uses newlib-nano for minimal C library support.

#include <stdio.h>
#include <stdlib.h>

#define WIDTH  79  // must be odd
#define HEIGHT 31  // must be odd

char **maze;

int dx[] = { 0, 1, 0, -1 };
int dy[] = { -1, 0, 1, 0 };

void init_maze() {
    maze = malloc(HEIGHT * sizeof(char*));
    for (int y = 0; y < HEIGHT; y++) {
        maze[y] = malloc(WIDTH);
        for (int x = 0; x < WIDTH; x++) {
            maze[y][x] = '#';
        }
    }
}

int in_bounds(int x, int y) {
    return x > 0 && y > 0 && x < WIDTH - 1 && y < HEIGHT - 1;
}

void carve(int x, int y) {
    maze[y][x] = ' ';

    int dirs[] = { 0, 1, 2, 3 };
    // Fisher-Yates shuffle
    for (int i = 3; i > 0; i--) {
        int j = rand() % (i + 1);
        int tmp = dirs[i]; dirs[i] = dirs[j]; dirs[j] = tmp;
    }

    for (int i = 0; i < 4; i++) {
        int nx = x + dx[dirs[i]] * 2;
        int ny = y + dy[dirs[i]] * 2;

        if (in_bounds(nx, ny) && maze[ny][nx] == '#') {
            maze[y + dy[dirs[i]]][x + dx[dirs[i]]] = ' ';
            carve(nx, ny);
        }
    }
}

void print_maze() {
    for (int y = 0; y < HEIGHT; y++) {
        for (int x = 0; x < WIDTH; x++) {
            putchar(maze[y][x]);
        }
        putchar('\n');
    }
}

void free_maze() {
    for (int y = 0; y < HEIGHT; y++) {
        free(maze[y]);
    }
    free(maze);
}


int main() {
    putchar('\0'); // triggers newlib-nano initialization

    srand(42);  // make output deterministic
    init_maze();
    carve(1, 1);
    print_maze();
    free_maze();
    
    return 0;
}
