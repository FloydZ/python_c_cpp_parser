#include <stdio.h>
#include <iostream>

template<typename T, const int a>
void add_two_numbers(unsigned long *o,
                     const unsigned long *i0,
                     const unsigned long *i1=nullptr) {
    // *o = *i0 + *i1;
	int sum1 = 0, sum2 = 0;
	const int sum3 = 1;
	const int *k = &sum1;
	sum1 += a;
}

int main() {
}