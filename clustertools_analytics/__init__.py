from .array.base import MeanStd, Formater, TSVFormater, CSVFormater, Table
from .array.latex import LatexFormater, LatexColorFormater, \
    LatexColumnColorFormater, LatexRowColorFormater
from .array.colorer import LinearColorer, OrdinalColorer

from .utils import EmptyCube, save_pdf, PDFSaver
from .plot.convention import Convention, ConventionFactory, default_factory, \
    OverrideConventionFactory
from .plot.layout import Subplot, HzSubplot, TwoLegendPlot
from .plot.plot import Plot2D, ScatterPlot, \
    TrajectoryPlot, BarPlot, ScatterSpaceHz, HorizontalLine, HistogramPlot, \
    BoxPlot, VerticalLine
from .plot.trajectory import TrajectoryDisplayer, MinMaxMeanTrajectory, \
    StdBarTrajectory
from .plot.decorators import TextDecorator, LegendDecorator, GridDecorator, \
    LimitDecorator, SameLimitDecorator, TimeConverter, TightLayout
from .accessor import Accessor, NumpyfySqueeze, MetricOverParameter, \
    name_to_accessor, DiffAccessor, DomainAccessor, YSeriesXRangeAccessor, \
    XSeriesYSeries, AtomicAcessor, SeriesAccessor, YSeriesByParamOverParams, \
    DeltaSeries
from .plot.widget import Legend


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"
__version__ = '0.0.1'
__date__ = "20 Mar. 2019"


__all__ = ["Formater", "TSVFormater", "CSVFormater", "LatexFormater",
           "LatexColorFormater", "Table",
           "LatexColumnColorFormater", "LatexRowColorFormater",
           "LinearColorer", "OrdinalColorer",
           "Convention", "ConventionFactory", "default_factory",
           "OverrideConventionFactory", "TwoLegendPlot",
           "Plot2D", "TightLayout", "HzSubplot", "ScatterPlot",
           "TrajectoryPlot", "BarPlot", "ScatterSpaceHz", "HorizontalLine",
           "HistogramPlot", "Subplot", "BoxPlot",
           "TrajectoryDisplayer", "MinMaxMeanTrajectory", "StdBarTrajectory",
           "TextDecorator", "LegendDecorator", "GridDecorator",
           "LimitDecorator", "SameLimitDecorator", "TimeConverter",
           "Accessor", "NumpyfySqueeze", "MetricOverParameter",
           "name_to_accessor", "DiffAccessor", "DomainAccessor",
           "XSeriesYSeries", "AtomicAcessor", "SeriesAccessor",
           "YSeriesXRangeAccessor", "YSeriesByParamOverParams", "DeltaSeries",
           "EmptyCube", "save_pdf", "PDFSaver", "VerticalLine", "Legend"]
