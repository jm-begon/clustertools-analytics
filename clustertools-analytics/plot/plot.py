import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .convention import default_factory
from .trajectory import TrajectoryDisplayer


class HzSubplot(object):
    def __init__(self, n_subplots, figure=None):
        self._responsible_for_fig = False
        if figure is None:
            figure = plt.figure()
            self._responsible_for_fig = True
        self._fig = figure
        plt.subplots(1, n_subplots, sharey='row', num=self._fig.number)

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
                print('{}.plot got empty cube "{}". Skipping'
                      ''.format(self.__class__.__name__,
                                cube.name))  # TODO make it a warning
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
            except Exception:
                print("Error with cube '{}' ({})"
                      "".format(cube.name, self.__class__.__name__))
                raise

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

    def __init__(self, x_getter, y_getter,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self._get_x = x_getter
        self._get_y = y_getter

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        xs = []
        ys = []

        for (_, cube_i) in cube.iter_dimensions("random_state"):
            xs.append(self._get_x(cube_i))
            ys.append(self._get_y(cube_i))

        xs = np.array(xs)
        ys = np.array(ys)

        self.axes.scatter(xs, ys, color=convention.color,
                          marker=convention.marker,
                          label=convention.label)


class AbstractTrajectoryPlot(LegendeablePlot):
    def __init__(self, trajectory_displayer=None,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        if trajectory_displayer is None:
            trajectory_displayer = TrajectoryDisplayer()
        self._trajectory_displayer = trajectory_displayer

    def _get_xs_and_yss(self, cube):
        pass

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        xs, yss = self._get_xs_and_yss(cube)
        self._trajectory_displayer(self.axes, xs, yss, convention)


class TrajectoryPlot(AbstractTrajectoryPlot):
    """
    Plot trajectories for several random state
    """

    def __init__(self, metric_name="valid_accuracies",
                 trajectory_displayer=None, convention_factory=None,
                 decorated=None):
        super().__init__(trajectory_displayer=trajectory_displayer,
                         decorated=decorated,
                         convention_factory=convention_factory)
        self._metric_name = metric_name

    @property
    def metric_name(self):
        return self._metric_name

    def _get_xs_and_yss(self, cube):
        yss = cube(self.metric_name).numpyfy(True).squeeze().T
        xs = np.arange(yss.shape[0])

        return xs, yss


class DeltaTrajectoryPlot(AbstractTrajectoryPlot):
    def __init__(self, metric_name_1="train_accuracies",
                 metric_name_2="valid_accuracies", trajectory_displayer=None,
                 convention_factory=None, decorated=None):
        super().__init__(trajectory_displayer=trajectory_displayer,
                         decorated=decorated,
                         convention_factory=convention_factory)
        self.metric_name_1 = metric_name_1
        self.metric_name_2 = metric_name_2

    def _get_xs_and_yss(self, cube):
        yss1 = cube(self.metric_name_1).numpyfy(True).squeeze().T
        yss2 = cube(self.metric_name_2).numpyfy(True).squeeze().T

        yss = yss1 - yss2
        xs = np.arange(yss.shape[0])

        return xs, yss


class BarPlot(LegendeablePlot):
    """
    Plot as bar plot
    """

    def __init__(self, metric_name="duration", vertical=True,
                 convention_factory=None, decorated=None):
        super().__init__(decorated=decorated,
                         convention_factory=convention_factory)
        self._metric_name = metric_name
        self._n_bars = 0
        self._vertical = vertical

    def plot_(self, cube, **kwargs):
        convention = self.create_convention(cube)
        values = cube(self._metric_name).numpyfy(True)
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


class ScatterSpaceHz(ScatterPlot):
    class IncrementalSpacer(object):
        def __init__(self, n_groups):
            self.spacing = 1. / (n_groups + 1.)
            self.x_pos = self.spacing

        def __call__(self, cube, **kwargs):
            return self.x_pos

        def increment(self):
            self.x_pos += self.spacing

    def __init__(self, y_getter, convention_factory=None, decorated=None):
        super().__init__(x_getter=ScatterSpaceHz.IncrementalSpacer,
                         y_getter=y_getter,
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
