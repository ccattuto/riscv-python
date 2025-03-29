#include <stdio.h>

int main() {
    unsigned int sum = 0;

    for (int i = 0; i < 100; i++) {
        sum += i;
    }

    printf("sum = %u\n", sum);
    printf("sum = %u\n", sum);

    return 0;
}
