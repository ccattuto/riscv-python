#include <stdio.h>
#include <setjmp.h>

// Declare a jump buffer
jmp_buf error_handler_buffer;

// A function that might "fail" and require jumping to an error handler
void process_data(int data_value) {
    printf("Processing data: %d\n", data_value);

    if (data_value < 0) {
        printf("Error: Data value is negative!\n");
        // Jump back to the setjmp location, returning '1' (error code)
        longjmp(error_handler_buffer, 1);
    } else if (data_value > 100) {
        printf("Error: Data value too large!\n");
        // Jump back, returning '2' (another error code)
        longjmp(error_handler_buffer, 2);
    }

    printf("Data value processed successfully: %d\n", data_value);
}

int main() {
    int error_code;

    printf("Program started.\n");

    // Set the jump point.
    // - Returns 0 on initial call.
    // - Returns non-zero if longjmp jumps back here.
    error_code = setjmp(error_handler_buffer);

    if (error_code == 0) {
        // --- TRY BLOCK ---
        // This code runs when setjmp is first called.
        printf("Initial setjmp successful. Entering 'try' block.\n");

        process_data(50);   // This should succeed
        process_data(-5);   // This will trigger a longjmp with error code 1
        process_data(200);  // This line will not be reached if the previous call jumps

        printf("'Try' block completed without errors.\n"); // Not reached if an error occurs

    } else {
        // --- CATCH BLOCK ---
        // This code runs if longjmp jumped back to setjmp.
        // 'error_code' will be the value passed to longjmp.
        printf("\n--- ERROR HANDLER ---\n");
        if (error_code == 1) {
            printf("Caught error: Negative data value.\n");
        } else if (error_code == 2) {
            printf("Caught error: Data value too large.\n");
        } else {
            printf("Caught unknown error code: %d\n", error_code);
        }
        printf("Continuing after error handling.\n");
    }

    printf("\nProgram finished.\n");
    return 0;
}
