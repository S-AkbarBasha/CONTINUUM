// CONTINUUM Sample C Programs Catalog
const SAMPLES = {
    normal: {
        title: "Test 1: Normal Execution in Kali",
        desc: "Compiles and executes successfully on Primary Environment (Kali Linux). Exit 0, no failover required.",
        flags: ["-Wall", "-O2"],
        stdin: "",
        timeout: 10,
        simulate_kali_env: false,
        simulate_parrot_offline: false,
        code: `#include <stdio.h>

int main() {
    printf("===================================================\\n");
    printf("     CONTINUUM PROGRAM CONTINUITY SYSTEM           \\n");
    printf("===================================================\\n");
    printf("Executing on: Kali Linux (Primary Environment)\\n\\n");
    
    int numbers[] = {12, 45, 78, 23, 56, 89, 34};
    int n = sizeof(numbers) / sizeof(numbers[0]);
    int max = numbers[0];
    int sum = 0;
    
    for (int i = 0; i < n; i++) {
        if (numbers[i] > max) max = numbers[i];
        sum += numbers[i];
    }
    
    printf("[+] Array Elements Processed: %d\\n", n);
    printf("[+] Maximum Value Found     : %d\\n", max);
    printf("[+] Total Sum of Elements   : %d\\n", sum);
    printf("[+] Average Value           : %.2f\\n\\n", (float)sum / n);
    printf("[OK] Execution completed with Exit Code 0.\\n");
    return 0;
}
`
    },

    failover: {
        title: "Test 2: User-Approved Failover to Parrot OS",
        desc: "Requires header 'parrot_exclusive.h' (missing on Kali). Triggers environment failure classification -> prompts user for confirmation -> migrates to Parrot OS upon approval.",
        flags: ["-Wall", "-O2"],
        stdin: "",
        timeout: 10,
        simulate_kali_env: false,
        simulate_parrot_offline: false,
        code: `#include <stdio.h>
#include <parrot_exclusive.h>

int main() {
    printf("===================================================\\n");
    printf("     CONTINUUM FAILOVER RECOVERY VERIFIED          \\n");
    printf("===================================================\\n");
    printf("[!] Note: This program failed on Kali Linux due to\\n");
    printf("    missing dependency: <parrot_exclusive.h>\\n\\n");
    printf("[+] CONTINUUM classified the failure as an\\n");
    printf("    ENVIRONMENT FAULT, obtained user authorization,\\n");
    printf("    migrated source code, and resumed on Parrot OS!\\n\\n");
    printf("[+] Active OS Environment : Parrot OS 7.3 KDE Security\\n");
    printf("[+] Execution Status       : SUCCESS (Recovered)\\n");
    printf("[+] User-Approved Failover: VERIFIED\\n");
    return 0;
}
`
    },

    syntax_error: {
        title: "Test 3: C Syntax Error (No Migration)",
        desc: "Contains syntax mistakes (missing semicolon & undeclared identifier). Classified as Program Error; NO migration triggered.",
        flags: ["-Wall", "-O2"],
        stdin: "",
        timeout: 10,
        simulate_kali_env: false,
        simulate_parrot_offline: false,
        code: `#include <stdio.h>

int main() {
    printf("Checking compiler syntax validation...\\n")  // SYNTAX ERROR: Missing semicolon!
    
    int result = undeclared_variable * 2;              // ERROR: Undeclared identifier!
    printf("Result: %d\\n", result);
    return 0;
}
`
    },

    parrot_down: {
        title: "Test 4: Backup Environment Unavailable",
        desc: "Kali encounters environment failure, but Parrot OS backup is offline. CONTINUUM reports clear migration failure.",
        flags: ["-Wall", "-O2"],
        stdin: "",
        timeout: 10,
        simulate_kali_env: true,
        simulate_parrot_offline: true,
        code: `#include <stdio.h>
#include <parrot_exclusive.h>

int main() {
    printf("Simulating failover when backup node is offline.\\n");
    return 0;
}
`
    },

    timeout: {
        title: "Test 5: Program Execution Timeout",
        desc: "Enters an infinite loop. CONTINUUM terminates process after timeout limit and records timeout diagnostics.",
        flags: ["-Wall", "-O2"],
        stdin: "",
        timeout: 3,
        simulate_kali_env: false,
        simulate_parrot_offline: false,
        code: `#include <stdio.h>

int main() {
    printf("[*] Starting intensive computation simulation...\\n");
    printf("[*] Entering infinite loop to test watchdog timeout...\\n");
    fflush(stdout);
    
    volatile int counter = 0;
    while (1) {
        counter++;
        // Endless loop without break condition
    }
    
    return 0;
}
`
    },

    interactive_stdin: {
        title: "Interactive Input (Stdin Processing)",
        desc: "Demonstrates feeding standard input to the C program across environments.",
        flags: ["-Wall", "-O2"],
        stdin: "ContinuumUser 2026",
        timeout: 10,
        simulate_kali_env: false,
        simulate_parrot_offline: false,
        code: `#include <stdio.h>

int main() {
    char username[64];
    int year;
    
    printf("===================================================\\n");
    printf("          STDIN INTERACTION MODULE                 \\n");
    printf("===================================================\\n");
    printf("Please enter your name and project year: ");
    
    if (scanf("%63s %d", username, &year) == 2) {
        printf("\\n[+] Welcome, %s!\\n", username);
        printf("[+] Verified Session Year : %d\\n", year);
        printf("[+] Cross-OS Execution Engine: Active\\n");
    } else {
        printf("\\n[-] No stdin received or format mismatch.\\n");
    }
    
    return 0;
}
`
    },

    scanf_sum: {
        title: "Two Number Sum (scanf input)",
        desc: "Reads two integers via scanf() from stdin separated by newline and prints their sum.",
        flags: ["-Wall", "-O2"],
        stdin: "10\n20",
        timeout: 10,
        simulate_kali_env: false,
        simulate_parrot_offline: false,
        code: `#include <stdio.h>

int main() {
    int a, b;
    printf("Enter first number: ");
    scanf("%d", &a);

    printf("Enter second number: ");
    scanf("%d", &b);

    printf("Sum = %d\\n", a + b);
    return 0;
}
`
    }
};
