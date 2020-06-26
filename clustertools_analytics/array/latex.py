import os
import warnings
from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict

from clustertools_analytics.array.base import Formater, MeanStd
from clustertools_analytics.array.colorer import LinearColorer


class LatexFormater(Formater):
    def __init__(self, float_format="{:.2f}"):
        super().__init__(" & ", float_format)

    def __call__(self, table_content):
        return "\\\\ {}".format(os.linesep).join(list(self.rows(table_content)))

    def _format_float_raw(self, value, row, column):
        # Hack to get out of circular calls
        return super()._format_float(value, row, column)


    def _format_special(self, special, row, column, raw=False):
        ffloat = self._format_float_raw if raw else self._format_float
        if isinstance(special, MeanStd):
            return "{} $\\pm$ {}".format(ffloat(special.mean, row, column),
                                         ffloat(special.std, row, column))
        raise ValueError("Unknown cell type '{}'".format(repr(special)))



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
                if isinstance(cell, MeanStd):
                    self._get_colorer(r, c).memo(cell.mean)
                    continue
                try:
                    v = float(cell)
                    self._get_colorer(r, c).memo(v)
                except ValueError:
                    if not isinstance(cell, str):
                        warnings.warn("Uncolorable content '{}'. "
                                      "Skipping".format(cell))

    def _color_prefix(self, value, row, column):
        color = self._get_colorer(row, column).float_to_color(value)
        if color is None:
            return ""
        return self.color_to_str(*color)


    def _format_special(self, special, row, column, raw=False):
        if raw:
            return super()._format_special(special, row, column, True)
        if not isinstance(special, MeanStd):
            raise ValueError("Unknown cell type '{}'".format(repr(special)))
        prefix = self._color_prefix(special.mean, row, column)
        return "{} {}".format(prefix, super()._format_special(special, row, column, True))



    def _format_float(self, value, row, column):
        prefix = self._color_prefix(value, row, column)
        return "{} {}".format(prefix, super()._format_float(value, row, column))



class LatexColorFormater(LatexSubsetColorFormater):
    def _get_colorer(self, row, column):
        return self.colorers[0]


class LatexColumnColorFormater(LatexSubsetColorFormater):
    def _get_colorer(self, row, column):
        return self.colorers[column]


class LatexRowColorFormater(LatexSubsetColorFormater):
    def _get_colorer(self, row, column):
        return self.colorers[row]

