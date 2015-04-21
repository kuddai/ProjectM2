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

def calc_distances(data, pair_ids):
    def calc_shifts(acell):
        from itertools import product
        base = [-1, 0, 1]
        #generate variations with repetition
        shifts_norm = map(np.array, product(base, base, base))
        shifts = [sn * acell for sn in shifts_norm]
        return shifts
    acell, steps = data
    calc_shifts(acell)

def main(file_name):
    data = get_data(file_name)
    calc_distances(data, [])
    #print steps[0]

if __name__ == "__main__":
    main(sys.argv[1])
