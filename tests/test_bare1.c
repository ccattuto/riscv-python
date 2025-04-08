// Bare metal C program with a simple loop.
// Terminates with exit code 4950.

int main() {
    volatile unsigned int sum = 0;

    for (int i = 0; i < 100; i++) {
        sum += i;
    }

    return sum;
}
