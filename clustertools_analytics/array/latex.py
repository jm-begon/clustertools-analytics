import os
import warnings
from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict

from clustertools_analytics.array.base import Formater, MeanStd, GaussianPValue, \
    Renderer
from clustertools_analytics.array.colorer import LinearShader
import pylatex



# TODO remove
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


class LatexRenderer(Renderer):
    def __init__(self, caption_first=True):
        super().__init__(caption_first)
        self.tabular = None

    @property
    def default_separator(self):
        return " & "

    def cell_2_str(self, cell):
        pass

    def render_single_row_separation(self):
        self.rendering.append("\\hline")

    def write_caption(self, caption):
        pass

    def acknowledge_layout(self, layout):
        pass




# TODO adapt for full table
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
