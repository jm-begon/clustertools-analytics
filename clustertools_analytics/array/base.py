import os
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from functools import partial

from matplotlib.pyplot import get_cmap
import numpy as np
from scipy import stats

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

class CellType(object):
    pass

class MeanStd(CellType):
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __str__(self):
        return "{} +/- {}".format(self.mean, self.std)

    def __float__(self):
        return self.mean


class GaussianPValue(CellType):
    def __init__(self, value, pop_mean, pop_std,
                 bilateral=True):

        self.value = value

        z = (value - pop_mean) / pop_std
        self.p_value = 1 - stats.norm.cdf(abs(z))

        if bilateral:
            self.p_value *= 2

    def __str__(self):
        return "{} ({})".format(self.value, self.p_value)

    def __float__(self):
        return self.value



class Formater(object):
    def __init__(self, separator=" ", float_format="{:.2f}",
                 sc_formater="{:.2e}"):
        self.separator = separator
        self.float_format = float_format
        self.sc_formater = sc_formater

    def _format_float(self, value, row, column):
        return self.float_format.format(value)

    def _format_special(self, special, row, column):
        return str(special)

    def _format_cell(self, cell, row, column):
        if isinstance(cell, CellType):
            return self._format_special(cell, row, column)
        try:
            v = float(cell)
            return self._format_float(v, row, column)
        except ValueError:
            return str(cell)


    def rows(self, table_content):
        for r, row in enumerate(table_content):
            row_str = []
            for c, cell in enumerate(row):
                row_str.append(self._format_cell(cell, r, c))
            yield self.separator.join(row_str)

    def __call__(self, table_content):
        return os.linesep.join(list(self.rows(table_content)))


class TSVFormater(Formater):
    def __init__(self, float_format="{:.2f}", sc_formater="{:.2e}"):
        super().__init__("\t", float_format, sc_formater)

    def _format_special(self, special, row, column):
        if isinstance(special, MeanStd):
            return self._format_float(special.mean, row, column)
        return super()._format_special(special, row, column)


class CSVFormater(Formater):
    def __init__(self, float_format="{:.2f}", sc_formater="{:.2e}"):
        super().__init__(";", float_format, sc_formater)




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

    def __len__(self):
        return len(self.content)




if __name__ == '__main__':
    pass