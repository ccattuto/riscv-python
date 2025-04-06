#include <stdio.h>

int main(void) {
    unsigned int sum = 0;

    putchar('\0'); // triggers newlib-nano initialization

    for (int i = 0; i < 100; i++)
        sum += i;

    printf("sum = %u\n", sum);

    printf("Type a character: ");
    fflush(stdout);
    int ch = getchar();
    printf("You typed: '%c'\n", ch);

    return 0;
}
