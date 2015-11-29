#include <stdio.h>

long seqsum(long n) {
    long ret = 0;
    if (n > 0) {
        ret = n + seqsum(n-1);
    }
    return ret;
}

int main () {
    long a, b;

    printf("Enter a number:\n");
    scanf("%ld", &a);

    b = seqsum(a);
    printf("%ld\n", b);

    return 0;
}
