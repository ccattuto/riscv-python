// This example stress tests fread() and fseek() and the syscalls they rely on.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FILENAME    "fseek_stress_test.bin"
#define FILESIZE    (1024 * 1024)  // 1 MB
#define BLOCKSIZE   256
#define ITERATIONS  1000

unsigned char pattern(size_t index) {
    return (unsigned char)((index * 47 + 13) & 0xFF);
}

int main() {
    FILE *fp;
    unsigned char buffer[BLOCKSIZE];

    // STEP 1: Create file with known pattern
    fp = fopen(FILENAME, "wb");
    if (!fp) { perror("fopen write"); return 1; }

    for (size_t offset = 0; offset < FILESIZE; offset += BLOCKSIZE) {
        for (size_t i = 0; i < BLOCKSIZE; i++) {
            buffer[i] = pattern(offset + i);
        }
        fwrite(buffer, 1, BLOCKSIZE, fp);
    }
    fclose(fp);
    printf("Initial 1MB file written\n");

    // STEP 2: Random-seek stress
    fp = fopen(FILENAME, "r+b");
    if (!fp) { perror("fopen r+b"); return 1; }

    long pos = 0;
    for (int iter = 0; iter < ITERATIONS; iter++) {
        int direction = rand() % 3;
        long delta = (rand() % (BLOCKSIZE * 4));  // ± up to 1KB
        long new_pos;

        // randomized seek
        switch (direction) {
            case 0: new_pos = rand() % (FILESIZE - BLOCKSIZE); break;
            case 1: new_pos = pos + delta; break;
            case 2: new_pos = pos - delta; break;
        }

        // clip to file boundary
        if (new_pos < 0) new_pos = 0;
        if (new_pos > FILESIZE - BLOCKSIZE) new_pos = FILESIZE - BLOCKSIZE;

        if (fseek(fp, new_pos, SEEK_SET) != 0) {
            perror("fseek");
            fclose(fp);
            return 1;
        }

        fread(buffer, 1, BLOCKSIZE, fp);

        for (size_t i = 0; i < BLOCKSIZE; i++) {
            unsigned char expected = pattern(new_pos + i);
            if (buffer[i] != expected) {
                printf("Data mismatch at %d+%d: got 0x%02x, expected 0x%02x\n",
                       new_pos, i, buffer[i], expected);
                fclose(fp);
                return 1;
            }
        }

        pos = new_pos;
    }

    fclose(fp);
    printf("Random seek + verify complete (%d iterations)\n", ITERATIONS);
    return 0;
}
