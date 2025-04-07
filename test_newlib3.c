// This example tests the dynamic memory allocation and deallocation.

#include <stdio.h>
#include <stdlib.h>

int main() {
    putchar('\0'); // triggers newlib-nano initialization
    
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
