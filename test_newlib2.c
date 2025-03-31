#include <stdio.h>
#include <stdbool.h>

#define MAX_PRIMES 1000

int main() {
    int primes[MAX_PRIMES];
    int count = 0;
    int num = 2;

    while (count < MAX_PRIMES) {
        bool is_prime = true;
        for (int i = 0; i < count; i++) {
            if (num % primes[i] == 0) {
                is_prime = false;
                break;
            }
        }
        if (is_prime) {
            primes[count++] = num;
            printf("%d\n", num);
        }
        num++;
    }

    return 0;
}
