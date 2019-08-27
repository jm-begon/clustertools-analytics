import os
from abc import ABCMeta, abstractmethod
from collections import defaultdict

from matplotlib.pyplot import get_cmap
import numpy as np

"""
Example
=======
table = Table(LatexLinearShader())
table.fill_cell(1)
table.fill_cell(2)
table.fill_cell(3, new_column=False)
table.new_row()
table.fill_row("a", "b", "c")
print(table)
"""


class Formater(object):
    def __init__(self, separator=" ", float_format="{:.2f}"):
        self.separator = separator
        self.float_format = float_format

    def _format_float(self, value, row, column):
        return self.float_format.format(value)

    def rows(self, table_content):
        for r, row in enumerate(table_content):
            row_str = []
            for c, cell in enumerate(row):
                try:
                    v = float(cell)
                    row_str.append(self._format_float(v, r, c))
                except ValueError:
                    row_str.append(str(cell))
            yield self.separator.join(row_str)

    def __call__(self, table_content):
        return os.linesep.join(list(self.rows(table_content)))


class TSVFormater(Formater):
    def __init__(self, float_format="{:.2f}"):
        super().__init__("\t", float_format)


class CSVFormater(Formater):
    def __init__(self, float_format="{:.2f}"):
        super().__init__(";", float_format)


class LatexFormater(Formater):
    def __init__(self, float_format="{:.2f}"):
        super().__init__(" & ", float_format)

    def __call__(self, table_content):
        return "\\\\ {}".format(os.linesep).join(list(self.rows(table_content)))


class BaseFloatColorer(object, metaclass=ABCMeta):
    def memo(self, cell_value):
        try:
            float_value = float(cell_value)
            self.memo_float(float_value)
        except ValueError:
            pass

    @abstractmethod
    def memo_float(self, float_value):
        pass

    def pack(self):
        return self

    @abstractmethod
    def float_to_color(self, float_value):
        pass

    def __call__(self, float_value):
        self.pack()
        return self.float_to_color(float_value)


class LinearColorer(BaseFloatColorer):
    # Colormap: https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
    def __init__(self, shading_min=0, shading_max=.6, cmap="Greys"):
        self.shading_min = shading_min
        self.shading_max = shading_max
        self.max = float("-inf")
        self.min = float("inf")
        self.color_map = get_cmap(cmap)

    def memo_float(self, float_value):
        if float_value < self.min:
            self.min = float_value
        if self.max < float_value:
            self.max = float_value

    def float_to_color(self, float_value):
        normalized_value = np.interp(
            [float_value], [self.min, self.max],
            [self.shading_min, self.shading_max]
        )[0]
        return self.color_map(float(normalized_value))  # Float value for [0, 1]


class OrdinalColorer(BaseFloatColorer):
    def __init__(self, shading_min=0, shading_max=.6, cmap="Greys"):
        self.shading_min = shading_min
        self.shading_max = shading_max
        self.color_map = get_cmap(cmap)
        self.memory = []

    def memo_float(self, float_value):
        self.memory.append(float_value)

    def pack(self):
        self.memory.sort()

    def float_to_color(self, float_value):
        idx = 0
        for i, v in enumerate(self.memory):
            idx = i
            if float_value <= v:
                break
        normalized_value = np.interp(
            [idx], [0, len(self.memory)-1],
            [self.shading_min, self.shading_max]
        )[0]
        return self.color_map(float(normalized_value))  # Float value for [0, 1]


class BaseLatexColorFormater(LatexFormater):
    def __init__(self, float_format="{:.2f}"):
        super().__init__(float_format)

    @abstractmethod
    def _first_pass(self, table_content):
        """Return a colorer"""
        pass

    @abstractmethod
    def reset_colorer(self):
        pass

    @abstractmethod
    def pack_colorer(self):
        pass

    def rows(self, table_content):
        self.reset_colorer()
        self._first_pass(table_content)
        self.pack_colorer()
        for x in super().rows(table_content):
            yield x

    def color_to_str(self, r, g, b, a):
        return "\\cellcolor[rgb]{{{:.2f}, {:.2f}, {:.2f}}}" \
               "".format(r, g, b)


class LatexSubsetColorFormater(BaseLatexColorFormater, metaclass=ABCMeta):
    def __init__(self, float_format="{:.2f}", colorer_factory=LinearColorer):
        super().__init__(float_format)
        self.colorer_factory = colorer_factory
        self.colorers = defaultdict(colorer_factory)

    def reset_colorer(self):
        self.colorers = defaultdict(self.colorer_factory)

    def pack_colorer(self):
        for colorer in self.colorers.values():
            colorer.pack()

    @abstractmethod
    def _get_colorer(self, row, column):
        pass

    def _first_pass(self, table_content):
        for r, row in enumerate(table_content):
            for c, cell in enumerate(row):
                self._get_colorer(r, c).memo(cell)

    def _format_float(self, value, row, column):
        color = self._get_colorer(row, column).float_to_color(value)
        return "{color} {float_str}" \
               "".format(color=self.color_to_str(*color),
                         float_str=super()._format_float(value, row, column))


class LatexColorFormater(LatexSubsetColorFormater):
    def _get_colorer(self, row, column):
        return self.colorers[0]


class LatexColumnColorFormater(LatexSubsetColorFormater):
    def _get_colorer(self, row, column):
        return self.colorers[column]


class LatexRowColorFormater(LatexSubsetColorFormater):
    def _get_colorer(self, row, column):
        return self.colorers[row]


class Table(object):
    def __init__(self, formatter):
        self.formatter = formatter
        self.content = [[""]]

    def new_column(self):
        self.content[-1].append("")
        return self

    def fill_cell(self, content, new_column=True):
        self.content[-1][-1] = content
        if new_column:
            self.new_column()
        return self

    def delete_cell(self):
        self.content[-1] = self.content[-1][:-1]
        return self

    def new_row(self):
        self.content.append([""])
        return self

    def fill_row(self, *args, new_row=True):
        for arg in args:
            self.fill_cell(arg, new_column=True)
        if new_row:
            self.delete_cell()
            self.new_row()
        return self

    def delete_row(self):
        self.content = self.content[:-1]
        return self

    def __str__(self):
        return self.formatter(self.content)


class TableAndLatexFormater(object):
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

    def print_cell(self, arg, new_col=True):
        print(arg, end="")
        if new_col:
            self.newcol()

    def print_means_line(self, means, stds, factor=1):
        format = (lambda s: ("%.2f" % s))
        args = ["%s $\pm$ %s" % (format(m * factor), format(s * factor)) for
                m, s in zip(means, stds)]
        # format = (lambda m, s:("%f +- %f"%(m,s)).replace(".", ","))
        # args = [format(m,s) for m,s in zip(means, stds)]
        self.print_line(*args)

    def flush(self):
        pass


class ExcelTableAndFormater(object):
    def print_(self, *args):
        for arg in args:
            print(arg, "\t", end="")

    def newcol(self):
        print("\t", end="")

    def newline(self):
        print("")

    def print_cell(self, arg, new_col=True):
        print(arg, end="")
        if new_col:
            self.newcol()

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


class TableAndLatexShaderFormater(TableAndLatexFormater):
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

if __name__ == '__main__':
    pass