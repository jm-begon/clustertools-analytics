import os
import warnings
from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict

from clustertools_analytics.array.base import Formater, MeanStd, GaussianPValue
from clustertools_analytics.array.colorer import LinearColorer
import pylatex


class LatexFormater(Formater):
    def __init__(self, float_format="{:.2f}", sc_formater="{:.2e}"):
        super().__init__(" & ", float_format, sc_formater)

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

        if isinstance(special, GaussianPValue):
            pv_str = self.sc_formater.format(special.p_value)
            return "{} ({})".format(ffloat(special.value, row, column), pv_str)
        raise ValueError("Unknown cell type '{}'".format(repr(special)))



class BaseLatexColorFormater(LatexFormater):
    def __init__(self, float_format="{:.2f}", sc_formater="{:.2e}"):
        super().__init__(float_format, sc_formater)

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
        prefix = self._color_prefix(float(special), row, column)
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



class LatexTableDoc(object):

    @classmethod
    def ready(cls, doc=None, new_page=False):
        if doc is None:
            return cls()
        if new_page:
            doc.new_page()
        return doc

    def __init__(self, **kwargs):
        self.tables = []
        geometry = {
                "landscape": True,
                "margin": "0.5in",
                "headheight": "20pt",
                "headsep": "10pt",
                "includeheadfoot": True
            }
        geometry.update(kwargs)
        self.doc = pylatex.Document(
            page_numbers=True,
            geometry_options=geometry
        )
        self.doc.packages.append(pylatex.Package("xcolor", options='table'))

        self.fpath = None
        self.len_last_page = 0


    def add_table(self, table, header, caption=None):
        self.len_last_page += len(table)
        if self.len_last_page > 35:
            self.len_last_page = len(table)
            self.new_page()

        with self.doc.create(pylatex.Center()) as center, \
                center.create(
                    pylatex.LongTable("l|" + "|c" * (len(header) - 1))) \
                        as latex_table:
            latex_table.add_hline()
            latex_table.add_row(header)
            latex_table.add_hline()
            latex_table.end_table_header()

            latex_table.append(pylatex.NoEscape(str(table)))
            latex_table.add_hline()

            if caption is not None:
                caption = caption.replace("_", "\\_")
                self.doc.append(pylatex.NoEscape(caption))

    def new_page(self):
        self.doc.append(pylatex.NewPage())

    def set_default_fpath(self, fpath):
        self.fpath = fpath



    def generate(self, fpath=None, what="pdf"):
        pdf = what == "pdf"
        tex = what == "tex"

        if what == "both":
            pdf = tex = True

        if fpath is None:
            fpath = self.fpath

        if fpath is None:
            raise ValueError("No destination specified.")

        if pdf:
            self.doc.generate_pdf((fpath), clean_tex=True)

        if tex:
            self.doc.generate_tex(fpath)
