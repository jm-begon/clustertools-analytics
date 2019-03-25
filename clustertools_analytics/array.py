import numpy as np


class LatexFormater(object):
    def print_(self, *args):
        size = len(args)
        for i, arg in enumerate(args):
            print(arg, end="")
            if i < size - 1:
                self.newcol()

    def newcol(self):
        print(" & ", end="")

    def newline(self):
        print("\\\\")

    def print_line(self, *args):
        self.print_(*args)
        self.newline()

    def print_means_line(self, means, stds, factor=1):
        format = (lambda s: ("%.2f" % s))
        args = ["%s $\pm$ %s" % (format(m * factor), format(s * factor)) for
                m, s in zip(means, stds)]
        # format = (lambda m, s:("%f +- %f"%(m,s)).replace(".", ","))
        # args = [format(m,s) for m,s in zip(means, stds)]
        self.print_line(*args)

    def flush(self):
        pass


class ExcelFormater(object):
    def print_(self, *args):
        for arg in args:
            print(arg, "\t", end="")

    def newcol(self):
        print("\t", end="")

    def newline(self):
        print("")

    def print_line(self, *args):
        self.print_(*args)
        self.newline()

    def print_means_line(self, means, stds, factor=1):
        format = (lambda s: ("%f" % s).replace(".", ","))
        args = [format(m * factor) for m in means]
        # format = (lambda m, s:("%f +- %f"%(m,s)).replace(".", ","))
        # args = [format(m,s) for m,s in zip(means, stds)]
        self.print_line(*args)

    def flush(self):
        pass


class LatexShadeFormater(LatexFormater):
    def __init__(self, gray_min=0.4, gray_max=1):
        self.buffer = [[]]
        self.max = float("-inf")
        self.min = float("inf")
        self.gray_min = gray_min
        self.gray_max = gray_max

    def print_(self, *args):
        self.buffer[-1].extend((lambda: str(arg)) for arg in args)

    def newcol(self):
        #self.buffer[-1].append([])
        pass

    def newline(self):
        self.buffer.append([])

    def print_means_line(self, means, stds, factor=1):
        def prepare_for_print(value):
            def print_it():
                gray_value = np.interp([value], [self.min, self.max],
                                       [self.gray_max, self.gray_min])
                return "\\cellcolor[gray]{%.2f} %.2f" % (gray_value, value*factor)
            return print_it

        self.min = min(self.min, *means)
        self.max = max(self.max, *means)
        self.buffer[-1].extend(prepare_for_print(mean) for mean in means)
        self.newline()

    def flush(self):
        for row in self.buffer:
            size = len(row)

            for i, print_me in enumerate(row):
                print(print_me(), end=" ")
                if i < size-1:
                    print("&", end=" ")
            print("\\\\")
        self.buffer = [[]]
        self.max = float("-inf")
        self.min = float("inf")
