// Bare metal C program with a simple loop.
// Should return 4950.

int main() {
    volatile unsigned int sum = 0;

    for (int i = 0; i < 100; i++) {
        sum += i;
    }

    return sum;
}
