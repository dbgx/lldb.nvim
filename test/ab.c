#include <stdio.h>
#include <unistd.h>

long slowsum(long n) {
    long f = 1;
    while (n > 0) {
	f += n;
	n -= 1;
	usleep(200000);
    }
    return f;
}

int main () {
    long aa = 4;
    long bb = 32;
    long cc;

    cc = slowsum(aa);
    printf("%ld\n", cc);

    cc = slowsum(bb);
    printf("%ld\n", cc);

    return 0;
}
