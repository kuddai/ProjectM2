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
        """
        we must extract acell pattern like this one:
        acell      7.6962876214E+00  7.6962876214E+00  7.6962876214E+00 Bohr
        amu      1.06000000E+02  2.00000000E+00              
        """
        acell_pattern = re.compile(r"""
            #header - indicate acell parameter
            acell\s+
            #Catch acell values in Bohr
            (?P<acell>
                #Match excatly 3 numbers. We don't catch this group
                (?:
                    #number in scientific notation. We don't catch this group
                    (?:-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)\s+
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
            #header - indicate that there are atom coordinates 
            #in bohr units after it
            Cartesian\scoordinates\s\(xcart\)\s\[bohr\]\s+
            ( #catch pattern 
              #(number in scientific notation with 
              #possible spaces after it) 
              #as many times as you can 
                #Match spaces and new lines after number. 
                #We don't catch this group 
                (?: 
                    #number in scientific notation. We don't catch this group
                    (?:-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)
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
    #due to the fact that list first element starts from 0 index
    atoms_ids = map(lambda x: x - 1, atoms_ids)
    #ensure uniqueness
    atoms_ids = list(set(atoms_ids))
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
    desc =  '''
            Plot hists of interatomic distances 
            for ABINIT MD output file 
            (only for orthohonal rprim)
            '''
    file_help = 'A path to the ABINIT MD output file'
    atoms_help = 'Indexes of atoms included in interatomic distances'
    offset_help =   """
                    Offset for distances in Angst. 
                    Default disabled.
                    To exclude irrelevant atoms. 
                    Normalized distribution graph is 
                    possible only when this option is 
                    used
                    """
    bins_help = """
                Number of bins which will be used to plot histogram.
                Default  is 75.
                """

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('file_name', help=file_help)
    parser.add_argument('atoms_ids', type=int, nargs='+', help=atoms_help)
    parser.add_argument('-o', '--offset', type=float, help=offset_help)
    parser.add_argument('-nb', '--number_of_bins', type=int, default=75, help=bins_help)

    args = parser.parse_args()
    acell, steps = get_data(args.file_name)
    pairs_ids = get_pairs_id(args.atoms_ids)

    #convert from zero based to 1 based
    print "generated pairs", map(lambda p: (p[0] + 1, p[1] + 1), pairs_ids) 

    dists = calc_distances(acell, steps, pairs_ids)
    #convert from default ABINIT Bohr units to Angst
    dists = map(lambda x: x * 0.529, dists)
    print "number of distances before offseting operation", len(dists)  
    if args.offset:
        dists = filter(lambda x: x < args.offset, dists)
    print "number of distances after offseting operation", len(dists)  
    
    print "min distance", min(dists)
    print "max distance", max(dists)
    mu, sigma = np.mean(dists), np.std(dists)
    print "mean distance", mu
    print "standard deviation", sigma
    print "probability value within 1.5 angst", norm_prob(sigma, mu, 0, 1.5)

    if args.offset:
        plot_hist_norm(dists, args.number_of_bins, mu, sigma)
    else:
        plot_hist(dists, args.number_of_bins)


if __name__ == "__main__":
    main()
