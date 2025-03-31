#include <stdio.h>
#include <stdlib.h>

int main() {
    unsigned int sum = 0;

    for (int i = 0; i < 100; i++) {
        sum += i;
    }

    printf("sum = %u\n", sum);

    printf("Type a character: ");
    fflush(stdout);
    int ch = getchar();
    printf("You typed: '%c'\n", ch);

    printf("sum = %u\n", sum);

    return 0;
}
