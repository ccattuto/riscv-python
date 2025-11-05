// Picolibc stdio setup
#include <stdio.h>
#include <unistd.h>

// Define stdin, stdout, stderr for picolibc
// picolibc's FDEV_SETUP_STREAM takes 4 arguments: (put, get, flags, file_descriptor)
static FILE __stdio_in = FDEV_SETUP_STREAM(NULL, NULL, _FDEV_SETUP_READ, 0);
static FILE __stdio_out = FDEV_SETUP_STREAM(NULL, NULL, _FDEV_SETUP_WRITE, 1);
static FILE __stdio_err = FDEV_SETUP_STREAM(NULL, NULL, _FDEV_SETUP_WRITE, 2);

FILE *const stdin = &__stdio_in;
FILE *const stdout = &__stdio_out;
FILE *const stderr = &__stdio_err;
