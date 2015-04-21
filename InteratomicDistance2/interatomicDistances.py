import sys, re

def get_steps(file_name):
    def get_raw_steps():
        """we must extract data patterns like this one:
            Cartesian coordinates (xcart) [bohr]
            1.75255604597822E-03  2.44698778617683E-03  3.18934151739078E-05
            3.84712955498547E+00 -1.92096780059473E-03  3.84685455237236E+00
            2.47640757288980E-03  3.84891394970560E+00  3.84925589870608E+00     
        """
        with open(file_name) as file:
            text = file.read()
            pattern = re.compile(r"""
                Cartesian\scoordinates\s\(xcart\)\s\[bohr\]\s+#header - indicate that there are atom coordinates in bohr after it
                ( #catch pattern (number in scientific notation with possible spaces after it) as many times as you can  
                    (?: #Match spaces and new lines after number. We don't wanna catch this group as well
                        (?:-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)#number in scientific notation. We don't catch this group
                    \s+)
                +)
                """, re.VERBOSE)
            raw_steps = re.findall(pattern, text)     
            return raw_steps

    def group(lst, n):        
        """group([0,3,4,10,2,3], 2) => iterator

        Group an iterable into an n-tuples iterable. Incomplete tuples
        are discarded e.g.

        >>> list(group(range(10), 3))
        [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
        """
        from itertools import islice
        return zip(*[islice(lst, i, None, n) for i in range(n)])   

    raw_steps = get_raw_steps()
    steps = [group([float(pos) for pos in rs.split()], 3) for rs in raw_steps]
    return steps

def main(file_name):
    print file_name
    with open(file_name) as file:
        text = file.read()
        pattern = re.compile(r"""
            Cartesian\scoordinates\s\(xcart\)\s\[bohr\]\s+#header - indicate that there are atom coordinates in bohr after it
            ( #catch pattern (number in scientific notation with possible spaces after it) as many times as you can  
                (?: #Match spaces and new lines after number. We don't wanna catch this group as well
                    (?:-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)#number in scientific notation. We don't catch this group
                \s+)
            +)
            """, re.VERBOSE)
        raw_steps = re.findall(pattern, text)#raw array of MD steps
        steps = [group([float(pos) for pos in rs.split()], 3) for rs in raw_steps]
        print steps[1]

if __name__ == "__main__":
    main(sys.argv[1])
