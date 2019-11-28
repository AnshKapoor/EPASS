A .mat file readable by the elPaSo Load Application tool consists of differen arrays with specific names.
-----
MATLAB workspace has to be saved via:
	>> save('FileName', '-v7.3');
-----
Version 7.3 is critical.

//Array 1:
Name:	ACoor
Descr.: Contains point coordinates in an array of size [(No. of Points) x 3]
	like:  c1    c2    c3
	l1     x1    y1    z1
	l2     x2    y2    z2
	l3     x3    y3    z3
	..     ..    ..    ..
	ln     xn    yn    zn


//Array 2 to x:
Name:	ADelta, AuE, AMA, ...
Descr.: Contains parameters used for the turbulent boundary layer load case
	Each array of size [1 x (No. of Points)]
	parameters: delta, uE, MA, c0, tauW, eta, rho, TKE, FL, dcpdx


//last array:
Name:	AData
Descr.: Contains time data for time variable data load case.
	Is an array of size [(No. of Samples per Point) x (No. of Points)]
	like:  pt.1  pt.2  pt.3 pt... pt.n 
        samp0  t0    t0	   t0   ...   
        samp1  t1    t1	   t1
        samp2  t2    t2	   t2
        ..     ..    ..	   ..
        sampn  tn    tn	   tn  .. ..  tn


