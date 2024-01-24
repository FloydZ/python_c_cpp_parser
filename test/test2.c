void add_two_numbers(unsigned long *o, const unsigned long *i0, const unsigned long *i1) {
    // *o = *i0 + *i1;
	int sum1 = 0, sum2 = 0;
	for (int i = 0; i < 10; i++){
		sum1 += i0[i];
	}
	for (int i = 0; i < 10; i++){
		sum2 += i1[i];
	}
	for (int i = 0; i < 10; i++){
		o[i] = i0[i] + i1[1] - sum1 + sum2;
	}
}
