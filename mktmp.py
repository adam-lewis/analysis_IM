"""Trivial code to generate template files.
"""

print "1"


def mktmp(rgn_i,rgn_j,rgn_k,srgn_i1,srgn_i2,srgn_j1,srgn_j2,srgn_k1,srgn_k2,outfilename):
	"""Write to disk a file representing an empty matrix of given dimensions. Also write an identically
	shaped array of booleans, which are true if the index points to the subregion.
	rgn_i/j/k  : the dimensions of the full region to be simulated
        srgn_i/j/k : the dimensions of the deep integration subregion
	outfilename: the name of the file to be created
	"""

	import numpy as np
	import core.algebra as algebra

	
	regiontype = np.zeros((rgn_i,rgn_j,rgn_k), bool)
		
	array = np.zeros((rgn_i,rgn_j,rgn_k))
	

	for i in range(0,rgn_i):
		for j in range(0,rgn_j):
			for k in range(0,rgn_k):
				if (i>=(srgn_i1-1) and i<=(srgn_i2-1)) :
					if (j>=(srgn_j1-1) and j<=(srgn_j2-1)) :
						if (k>=(srgn_k1-1) and k<=(srgn_k2-1)) :
							regiontype[i,j,k]=True
			else:
				regiontype[i,j,k]=False
			
	region=algebra.info_array(array)
	regiontypename = 'bool' + outfilename
	np.save(regiontypename, regiontype) 
	algebra.save(outfilename,region)
	print "done"
	template_map = algebra.make_vect(algebra.load(outfilename))
