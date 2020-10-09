import os
import copy
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

class Customizable(object):
    def __init__(self, **properties):
        self.properties = properties

    def __getitem__(self, item):
        return self.properties[item]

    def __setitem__(self, key, value):
        self.properties[key] = value
        return self



class CellType(Customizable):
    pass



class Number(CellType):
    @classmethod
    def only_if_raw(cls, content):
        if isinstance(content, CellType):
            return content
        return cls(content)

    def __init__(self, content, format="{:.2f}", **properties):
        super().__init__(**properties)
        self.format = format
        self.content = content

    def __str__(self):
        return self.format.format(self.content)

    def __float__(self):
        return self.content


class CompositeElement(CellType):
    def __init__(self, sub, parent, **properties):
        super().__init__(**properties)
        self.sub = sub
        self.parent = parent

    def __getitem__(self, item):
        el = self.properties.get(item)
        if not el:
            el = super().__getitem__(item)
        return el

    def __str__(self):
        return str(self.sub)



class MeanStd(Number):
    def __init__(self, mean, std, **properties):
        super().__init__(**properties)
        self.mean = CompositeElement(Number.only_if_raw(mean), self)
        self.std = CompositeElement(Number.only_if_raw(std), self)


    def __str__(self):
        return "{} +/- {}".format(self.mean, self.std)

    def __float__(self):
        return float(self.mean)


class PValue(Number):
    def __init__(self, value, p_value, **properties):
        super().__init__(**properties)
        self.value = CompositeElement(Number.only_if_raw(value), self)
        self.p_value = CompositeElement(Number.only_if_raw(p_value), self)

    def __str__(self):
        return "{} ({})".format(self.value, self.p_value)


    def __float__(self):
        return float(self.value)


class GaussianPValue(PValue):
    def __init__(self, value, pop_mean, pop_std,
                 bilateral=True, **properties):

        z = (float(value) - pop_mean) / pop_std
        p_value = 1 - stats.norm.cdf(abs(z))

        if bilateral:
            p_value *= 2
        super().__init__(value, p_value, **properties)

    def __str__(self):
        return "{} ({})".format(self.value, self.p_value)

    def __float__(self):
        return float(self.value)


class AbstractRow(object):
    pass

class Row(list, AbstractRow):
    pass

class RowSeparation(AbstractRow):
    def __init__(self, double_sep=False):
        self.double_sep = double_sep



class Table(object):
    def __init__(self):
        self.rows = []

    def new_row_separation(self, double_sep=False):
        self.rows.append(RowSeparation(double_sep))

    def new_row(self):
        self.rows.append(Row())
        return self

    def new_column(self, content=None):
        if len(self.rows) == 0 or not isinstance(self.rows[-1], Row):
            self.new_row()
        if content is not None:
            self.rows[-1].append(content)
        return self

    def fill_cell(self, content, new_column=True):
        self.rows[-1][-1] = content
        if new_column:
            self.new_column()
        return self

    def delete_cell(self):
        self.rows[-1] = self.rows[-1][:-1]
        return self


    def fill_row(self, *args, new_row=True):
        for arg in args:
            self.fill_cell(arg, new_column=True)
        if new_row:
            self.delete_cell()
            self.new_row()
        return self

    def delete_row(self):
        self.rows = self.rows[:-1]
        return self

    def __len__(self):
        return len(self.rows)

    def shape(self):
        max_width = 0
        for row in self.rows:
            try:
                l = len(row)
                if l > max_width:
                    max_width = l
            except TypeError:
                pass
        return len(self.rows), max_width


class Layout(object):
    @classmethod
    def from_dicts(cls, *dicts):
        return cls(*[Customizable(**d) for d in dicts])

    def __init__(self, *customizables):
        self.customizables = customizables



class FullTable(object):
    def __init__(self, table_content, layout=None, caption=None):
        self.table_content = table_content
        if layout is None:
            _, width = table_content.shape
            dicts = [{"left-align": True}] + [{"left-align": True,
                                               "left-border": True}
                                              for _ in range(width)]
            layout = Layout.from_dicts(*dicts)
        self.layout = layout
        self.caption = caption




class Renderer(object):
    def __init__(self, caption_first=True):
        self.caption_first = caption_first
        self.rendering = []

    @property
    def default_separator(self):
        return " "

    def cell_2_str(self, cell):
        return str(cell)

    def render_row(self, row):
        if isinstance(row, RowSeparation):
            self.render_single_row_separation()
            if row.double_sep:
                self.render_single_row_separation()
        else:
            cell_strs = [self.cell_2_str(cell) for cell in row]
            self.rendering.append(self.default_separator.join(cell_strs))

    def render_single_row_separation(self):
        pass

    def acknowledge_layout(self, layout):
        pass

    def write_caption(self, caption):
        pass

    def render_content(self, table_content):
        for row in table_content.rows:
            self.render_row(row)

    def __call__(self, full_table):
        if self.caption_first:
            self.write_caption(full_table.caption)

        self.acknowledge_layout(full_table.layout)

        self.render_content(full_table.table_content)

        if not self.caption_first:
            self.write_caption(full_table.caption)

        return self.pack()

    def pack(self):
        return os.linesep.join(self.rendering)



class TSVRenderer(Renderer):
    @property
    def default_separator(self):
        return "\t"

class CSVRenderer(Renderer):
    @property
    def default_separator(self):
        return ";"




if __name__ == '__main__':
    pass