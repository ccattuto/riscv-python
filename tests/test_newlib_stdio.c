// This examples demonstrates the use of Newlib-nano.

#include <stdio.h>

int main(void) {
    unsigned int sum = 0;

    for (int i = 0; i < 100; i++)
        sum += i;

    printf("sum = %u\n", sum);

    printf("Type a character: ");
    fflush(stdout);
    int ch = getchar();
    printf("You typed: '%c'\n", ch);

    return 0;
}
