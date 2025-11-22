// Sample program using newlib (vs newlib-nano) with soft floating point support.
// This is compiled with --specs=nosys.specs (rather than --specs=nano.specs).

#include <stdio.h>
#include <math.h>

int main() {
    float a = 1.2345f;
    float b = 6.7890f;
    float c, d, e;
    int i;

    printf("Simple float operations:\n");

    c = a + b;
    d = a * b;
    e = b / a;

    printf("a + b = %f\n", c);
    printf("a * b = %f\n", d);
    printf("b / a = %f\n", e);

    printf("\nMath functions:\n");

    printf("sin(a) = %f\n", sinf(a));
    printf("cos(b) = %f\n", cosf(b));
    printf("exp(a) = %f\n", expf(a));
    printf("log(b) = %f\n", logf(b));

    printf("\nRunning float loop stress test:\n");

    float sum = 0.0f;
    for (i = 0; i < 1000; i++) {
        float x = (float)i / 100.0f;
        sum += sinf(x) * cosf(x) / (1.0f + x);
    }

    printf("Loop sum = %f\n", sum);

    return 0;
}
