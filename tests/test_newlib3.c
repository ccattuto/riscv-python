// This example tests dynamic memory allocation and deallocation (Newlib).

#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("Starting dynamic memory test...\n");

    for (int i = 0; i < 3; i++) {
        int *array = malloc(10 * sizeof(int));
        if (!array) {
            printf("Allocation failed!\n");
            return 1;
        }

        for (int j = 0; j < 10; j++) {
            array[j] = (i+1) * 100 + j;
        }

        printf("Block %d contents:", i);
        for (int j = 0; j < 10; j++) {
            printf(" %d", array[j]);
        }
        printf("\n");

        free(array);
    }

    printf("Done.\n");
    return 0;
}
