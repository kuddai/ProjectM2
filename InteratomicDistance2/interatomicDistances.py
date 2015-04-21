import sys
import numpy as np

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
        pair_distances = [la.norm(diff + sh) for sh in shifts]
        return pair_distances   

    def fetch_all_pairs():
        for step in steps:
            for pair_ids in atom_pairs_ids:
                id1, id2 = pair_ids
                atom1, atom2 = step[id1], step[id2]
                yield (atom1, atom2)

    shifts = generate_shifts()
    print len(shifts)
    pairs = fetch_all_pairs()
    cpd = calc_pair_distances
    distances = [dist for p in pairs for dist in cpd(p, shifts)]
    return distances

def plot_hist(distances):
    import matplotlib.pyplot as plt
    print len(distances)

    plt.hist(map(lambda x: x * 0.529, distances), 100, normed=True)
    #plt.hist([2, 3, 4])
    plt.title("Interatomic Distances")
    plt.xlabel("Distances Angst")
    plt.show()

def main(file_name):
    acell, steps = get_data(file_name)
    dists = calc_distances(acell, steps, [[4, 5]])
    plot_hist(dists)
    #print steps[0]
    #test_calc_distances()

def test_calc_distances():
    acell = np.array([2, 0, 0])
    steps = [
        [
            np.array([0, 0, 0]),
            np.array([1, 0, 0])
        ]
    ]
    pairs_ids = [[0, 1]]
    dist = calc_distances(acell, steps, pairs_ids)
    assert min(dist) == 1
    assert max(dist) == 3

if __name__ == "__main__":
    main(sys.argv[1])
