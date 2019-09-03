import warnings
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .convention import default_factory
from .trajectory import TrajectoryDisplayer
from ..accessor import Accessor


class Subplot(object):
    def __init__(self, n_rows, n_cols, figure=None, sharey=False,
                 sharex=False):
        self._responsible_for_fig = False
        if figure is None:
            figure = plt.figure()
            self._responsible_for_fig = True
        self._fig = figure
        plt.subplots(n_rows, n_cols, sharey=sharey, num=self._fig.number,
                     sharex=sharex)

    def __iter__(self):
        return iter(self._fig.axes)

    def close(self):
        if self._fig is not None:
            plt.close(self._fig)

    def decorate(self, xlabel=None, ylabel=None, title=None):
        if title is not None:
            self._fig.suptitle(title)
        if xlabel is not None:
            self._fig.text(0.5, 0.04, xlabel, ha='center')
        if ylabel is not None:
            self._fig.axes[0].set_ylabel(ylabel)

    def make_legend(self, *args, **kwargs):
        handles, labels = None, None
        for ax in self:
            handles, labels = ax.get_legend_handles_labels()
        self._fig.legend(handles, labels, *args, **kwargs)
        # self._fig.tight_layout(rect=(0.2, 0.2, 0.8, 0.8))

    def adjust(self, left=None, bottom=None, right=None, top=None,
               wspace=None, hspace=None):
        # https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.subplots_adjust.html
        self._fig.subplots_adjust(left, bottom, right, top, wspace, hspace)


class HzSubplot(Subplot):
    def __init__(self, n_subplots, figure=None, sharex=False):
        super().__init__(n_rows=1, n_cols=n_subplots, figure=figure,
                         sharey=True, sharex=sharex)


class Plot2D(object):
    def __init__(self, decorated=None):
        self._fig = None
        self._decorated = None
        if decorated is None:
            # Responsible to close the figure
            self._fig = plt.figure()
            self._axes = self._fig.gca()
        elif isinstance(decorated, Figure):
            self._axes = decorated.gca()
        elif isinstance(decorated, Axes):
            self._axes = decorated
        elif isinstance(decorated, Plot2D):
            self._axes = decorated.axes
            self._decorated = decorated
        else:
            raise TypeError("Decorated of type '{}' is not allowed"
                            "".format(type(decorated)))

    @property
    def axes(self):
        return self._axes

    def plot_(self, cube, **kwargs):
        pass

    def plot(self, *cubes, **kwargs):
        filtered_cubes = []
        for cube in cubes:
            if len(cube) == 0:
                warnings.warn('{}.plot got empty cube "{}". Skipping'
                              ''.format(self.__class__.__name__,
                                        cube.name))
            else:
                filtered_cubes.append(cube)

        if self._decorated is not None:
            self._decorated.plot(*filtered_cubes, **kwargs)

        self.plot_all_(filtered_cubes, **kwargs)
        return self

    def plot_all_(self, filtered_cubes, **kwargs):
        for cube in filtered_cubes:
            try:
                self.plot_(cube, **kwargs)
            except Exception as e:
                raise ValueError("Error with cube '{}' ({})"
                                 "".format(cube.name,
                                           self.__class__.__name__)) from e

        try:
            if self._decorated is not None:
                self._decorated.pack()
            self.pack()
        except Exception as e:
            raise ValueError("Error while packing ({})"
                             "".format(self.__class__.__name__)) from e

    def pack(self):
        pass

    def close(self):
        if self._decorated is not None:
            self._decorated.close()
        if self._fig is not None:
            plt.close(self._fig)


class LegendeablePlot(Plot2D):
    def __init__(self, decorated=None, convention_factory=None):
        super().__init__(decorated=decorated)
        if convention_factory is None:
            convention_factory = default_factory
        self._convention_factory = convention_factory

    def create_convention(self, cube):
        return self._convention_factory(cube)


class ScatterPlot(LegendeablePlot):
    """
    Plot metric in scatter plot for several random states
    """

    def __init__(self, x_accessor, y_accessor,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self._get_x = x_accessor
        self._get_y = y_accessor

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)

        xs = self._get_x(cube)
        ys = self._get_y(cube)

        if xs.ndim == 0:
            # Same x for all ys
            xs = np.ones(ys.shape, dtype=xs.dtype) * xs

        self.axes.scatter(xs, ys, color=convention.color,
                          marker=convention.marker,
                          label=convention.label)


class TrajectoryPlot(LegendeablePlot):
    def __init__(self, data_accessor, trajectory_displayer=None,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self.data_accessor = data_accessor

        if trajectory_displayer is None:
            trajectory_displayer = TrajectoryDisplayer()
        self._trajectory_displayer = trajectory_displayer

    def plot_(self, cube, **kwargs):
        res = self.data_accessor(cube)
        if self.data_accessor.n_outputs == 1:
            yss = res
            xs = np.arange(len(yss))
        else:
            xs, yss = res
        convention = self.create_convention(cube)
        self._trajectory_displayer(self.axes, xs, yss, convention)


class BarPlot(LegendeablePlot):
    """
    Plot as bar plot
    """

    def __init__(self, height_accessor, vertical=True,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self.height_accessor = height_accessor
        self._n_bars = 0
        self._vertical = vertical

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        values = self.height_accessor(cube)
        xs = [self._n_bars]
        self._n_bars += 1
        ys = [values.mean()]
        std = [values.std()]

        plotter = self.axes.bar if self._vertical else self.axes.barh
        err_label = "yerr" if self._vertical else "xerr"

        plotter(xs, ys, color=convention.color, label=convention.label,
                hatch=convention.hatch, **{err_label: std})

        if self._vertical:
            self.axes.set_xticks([])
        else:
            self.axes.set_yticks([])


class HistogramPlot(LegendeablePlot):
    def __init__(self, distrib_accessor, n_bins=10, density=False,
                 cumulative=False, convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self.distrib_accessor = distrib_accessor
        self.n_bins = n_bins
        self.density = density
        self.cumulative = cumulative

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        distribution = self.distrib_accessor(cube)

        weights = None
        if self.density:
            weights = np.ones_like(distribution) / float(len(distribution))

        if distribution.ndim != 1:
            raise ValueError("Accessor did not yield a 1D tensor (got {}D)"
                             "".format(distribution.ndim))

        self.axes.hist(distribution, bins=self.n_bins, weights=weights,
                       cumulative=self.cumulative, color=convention.color,
                       histtype="step" if self.cumulative else "bar",
                       label=convention.label, hatch=convention.hatch)


class BoxPlot(LegendeablePlot):
    def __init__(self, distrib_accessor,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        # Look at https://stackoverflow.com/questions/16592222/matplotlib-group-boxplots
        # for how to plot each separately
        self.distrib_accessor = distrib_accessor
        self.distribs = []
        self.labels = []

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        distribution = self.distrib_accessor(cube)

        distribution = distribution.squeeze()

        if distribution.ndim != 1:
            raise ValueError("Accessor did not yield a 1D tensor (got {}D)"
                             "".format(distribution.ndim))

        self.distribs.append(distribution)
        self.labels.append(convention.label)

    def pack(self):
        self.axes.boxplot(self.distribs, labels=self.labels)


class ScatterSpaceHz(ScatterPlot):
    class IncrementalSpacer(Accessor):
        def __init__(self, n_groups):
            self.spacing = 1. / (n_groups + 1.)
            self.x_pos = self.spacing

        def access(self, cube):
            return np.array(self.x_pos)

        def increment(self):
            self.x_pos += self.spacing

    def __init__(self, y_accessor, convention_factory=None, decorated=None):
        super().__init__(x_accessor=ScatterSpaceHz.IncrementalSpacer,
                         y_accessor=y_accessor,
                         convention_factory=convention_factory,
                         decorated=decorated)

    def plot(self, *cubes, **kwargs):
        self._get_x = self._get_x(len(cubes))  # Ugly catch
        super().plot(*cubes, **kwargs)
        self.axes.set_xlim(0, 1)
        self.axes.set_xticks([])

    def plot_(self, cube, **kwargs):
        super().plot_(cube, **kwargs)
        self._get_x.increment()  # Ugly catch


class HorizontalLine(LegendeablePlot):
    def __init__(self, y_accessor, convention_factory=None, decorated=None,
                 linestyle=None, alpha=1, linewidth=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self.y_accessor = y_accessor
        self.linestyle = linestyle
        self.alpha = alpha
        self.linewidth = linewidth

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        ys = self.y_accessor(cube)
        linestyle = convention.linestyle if self.linestyle is None else \
            self.linestyle
        self.axes.axhline(np.nanmean(ys), color=convention.color,
                          alpha=self.alpha, linestyle=linestyle,
                          linewidth=self.linewidth)


class VerticalLine(LegendeablePlot):
    def __init__(self, y_accessor, convention_factory=None, decorated=None,
                 linestyle=None, alpha=1, linewidth=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self.y_accessor = y_accessor
        self.linestyle = linestyle
        self.alpha = alpha
        self.linewidth = linewidth

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        ys = self.y_accessor(cube)
        linestyle = convention.linestyle if self.linestyle is None else \
            self.linestyle
        self.axes.axvline(np.nanmean(ys), color=convention.color,
                          alpha=self.alpha, linestyle=linestyle,
                          linewidth=self.linewidth)
