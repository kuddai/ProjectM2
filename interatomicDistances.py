import sys
import numpy as np
import argparse

def norm_prob(sigma, mu, x1, x2):
    import math
    from scipy.integrate import quad
    k = 1 / (sigma * math.sqrt(2 * math.pi))
    s = -1.0 / (2 * sigma * sigma)
    def f(x):
        return k * math.exp(s * (x - mu) * (x - mu))
    return quad(f, x1, x2)

def get_data(file_name):
    import re
    def get_text():
        with open(file_name) as file:
            return file.read()

    def get_raw_acell(text):
        """we must extract acell pattern like this one:
            acell      7.6962876214E+00  7.6962876214E+00  7.6962876214E+00 Bohr
              amu      1.06000000E+02  2.00000000E+00              
        """
        acell_pattern = re.compile(r"""
            acell\s+#header - indicate acell parameter
            (?P<acell>#Catch acell values in Bohr
                (?:#Match excatly 3 numbers. We don't catch this group
                    (?:-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)\s+#number in scientific notation. We don't catch this group
                ){3}
            )Bohr
            """, re.VERBOSE)
        match = re.search(acell_pattern, text) 
        return match.group("acell")

    def get_raw_steps(text):
        """we must extract steps like this one:
            Cartesian coordinates (xcart) [bohr]
            1.75255604597822E-03  2.44698778617683E-03  3.18934151739078E-05
            3.84712955498547E+00 -1.92096780059473E-03  3.84685455237236E+00
            2.47640757288980E-03  3.84891394970560E+00  3.84925589870608E+00     
        """       
        step_pattern = re.compile(r"""
            Cartesian\scoordinates\s\(xcart\)\s\[bohr\]\s+#header - indicate that there are atom coordinates in bohr after it
            ( #catch pattern (number in scientific notation with possible spaces after it) as many times as you can  
                (?: #Match spaces and new lines after number. We don't catch this group
                    (?:-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)#number in scientific notation. We don't catch this group
                \s+)
            +)
            """, re.VERBOSE)   
        return re.findall(step_pattern, text)   

    def get_numbers(raw_numbers):
        return np.array(map(float, raw_numbers.split()))

    def get_steps(raw_steps):
        def get_step(raw_step):
            coords = get_numbers(raw_step)
            step = coords.reshape(-1, 3)
            return step
        return [get_step(rs) for rs in raw_steps]

    text = get_text()
    raw_acell, raw_steps = get_raw_acell(text), get_raw_steps(text)
    acell, steps = get_numbers(raw_acell), get_steps(raw_steps)
    return (acell, steps)

def calc_distances(acell, steps, atom_pairs_ids):
    def generate_shifts():
        from itertools import product
        base = [-1, 0, 1]
        #generate variations with repetition
        shifts_norm = map(np.array, product(base, base, base))
        shifts = [sn * acell for sn in shifts_norm]
        return shifts

    def calc_pair_distances(pair, shifts):
        from numpy import linalg as la
        atom1, atom2 = pair
        diff = atom2 - atom1
        pair_distances = [la.norm(sh + diff) for sh in shifts]
        return pair_distances   

    def fetch_all_pairs():
        for step in steps:
            for pair_ids in atom_pairs_ids:
                id1, id2 = pair_ids
                atom1, atom2 = step[id1], step[id2]
                yield (atom1, atom2)

    shifts = generate_shifts()
    pairs = fetch_all_pairs()
    cpd = calc_pair_distances
    distances = [dist for p in pairs for dist in cpd(p, shifts)]
    return distances

def get_pairs_id(atoms_ids):
    from itertools import combinations
    atoms_ids = map(lambda x: x - 1, atoms_ids)#due to the fact that list first element starts from 0
    atoms_ids = list(set(atoms_ids))#ensure uniqueness
    return list(combinations(atoms_ids, 2))

def plot_hist(dists, num_bins):
    import matplotlib.pyplot as plt
    

    plt.hist(dists, num_bins)
    #plt.hist([2, 3, 4])
    plt.title(r'Histogram of Interatomic Distances')
    plt.xlabel("Distances Angst")
    plt.show()

def plot_hist_norm(dists, num_bins, mu, sigma):
    import matplotlib.mlab as mlab
    import matplotlib.pyplot as plt
    font_size = 30
    # the histogram of the data
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = ax.hist(dists, num_bins, normed=1, facecolor='green', alpha=0.5)
    left = min(bins) * 0.85
    right = max(bins) * 1.15
    bins = np.insert(bins, [0, len(bins)], [left, right])
    #bins = np.append(bins, right)
    # add a 'best fit' line
    y = mlab.normpdf(bins, mu, sigma)

    ax.plot(bins, y, 'r--', linewidth=2.7)
    plt.xlabel('Distances Angst', fontsize=font_size)
    plt.ylabel('Probability Density', fontsize=font_size)
    legend = r'$\mu={0:.2f},\ \sigma={1:.2f}$'.format(mu, sigma)
    ax.text(0.8, 0.9, legend, 
        horizontalalignment='center', 
        verticalalignment='center', 
        transform=ax.transAxes, 
        fontsize=30,
        bbox=dict(facecolor='red', alpha=0.5) )
    
    plt.title(r'Histogram of Interatomic Distances', fontsize = 30)
    plt.tick_params(axis='both', which='major', labelsize=25)
    plt.tick_params(axis='both', which='minor', labelsize=25)
    # Tweak spacing to prevent clipping of ylabel
    plt.subplots_adjust(left=0.15)
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Plot hists of interatomic distances')
    parser.add_argument('file_name', help='a path to the ABINIT MD output file')
    parser.add_argument('atoms_ids', type=int, nargs='+', help='indexes of atoms included in interatomic distances')
    #parser.add_argument('-ng', '--number_of_gaussians', type=int, default=1, help='number of gaussians to approximate distribution')
    parser.add_argument('-o', '--offset', type=float, help='offset distances in Angst. Normalized distribution possible only with this option')
    parser.add_argument('-nb', '--number_of_bins', type=int, default=75, help='number of bins which will be used to plot histogram')
    args = parser.parse_args()
    acell, steps = get_data(args.file_name)
    pairs_ids = get_pairs_id(args.atoms_ids)
    print "generated pairs", map(lambda p: (p[0] + 1, p[1] + 1), pairs_ids) #convert from zero based to 1 based
    dists = calc_distances(acell, steps, pairs_ids)
    dists = map(lambda x: x * 0.529, dists)#from Bohr to Angst
    print "number of distances before offset", len(dists)  
    if args.offset:
        dists = filter(lambda x: x < args.offset, dists)
    print "number of distances after offset", len(dists)  
    
    print "min distance", min(dists)
    print "max distance", max(dists)
    mu, sigma = np.mean(dists), np.std(dists)
    print "mean distance", mu
    print "standard deviation", sigma
    print "probability within 1.5 angst", norm_prob(sigma, mu, 0, 1.5)
    if args.offset:
        plot_hist_norm(dists, args.number_of_bins, mu, sigma)
    else:
        plot_hist(dists, args.number_of_bins)
    #print steps[0]
    #test_calc_distances()


if __name__ == "__main__":
    main()
#PdH3_md
#dist 19.4117858195
#shift [-7.69628762  7.69628762  7.69628762]
#step 581
#a1 [ 3.90363717 -0.56109823 -0.84978193]
#a2 [-0.51770614  3.71501498  0.76210253]
#diff [-4.42134332  4.27611321  1.61188446]
#diff + shift [-12.11763094  11.97240083   9.30817208]
#sqr [ 146.83697954  143.33838164   86.64206752]
#sum sqr 376.817428703
#sqrt sum sqr 19.4117858195
#norm 19.4117858195
