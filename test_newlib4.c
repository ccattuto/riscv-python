#include <stdio.h>
#include <stdlib.h>

#define WIDTH  80
#define HEIGHT 24
#define MAX_ITER 128

int main(void) {
    putchar('\0'); // triggers newlib-nano initialization

    for (int y = 0; y < HEIGHT; y++) {
        for (int x = 0; x < WIDTH; x++) {
            int cr = (x - WIDTH/2) * 4 * 1024 / WIDTH;
            int ci = (y - HEIGHT/2) * 4 * 1024 / HEIGHT;

            int zr = 0, zi = 0;
            int iter = 0;

            while (zr*zr + zi*zi < 4*1024*1024 && iter < MAX_ITER) {
                int zr2 = (zr*zr - zi*zi) / 1024 + cr;
                int zi2 = (2*zr*zi) / 1024 + ci;
                zr = zr2;
                zi = zi2;
                iter++;
            }

            int log;
            for (log = 0; log < 10; log++) {
                iter >>= 1;
                if (iter == 0) break;
            }

            //printf("%d %d %ld\n", x, y, iter);
            char c = " .:=+*#@"[log];
            putchar(c);
        }
        putchar('\n');
    }

    return 0;
}
