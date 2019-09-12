from abc import ABCMeta

from matplotlib import pyplot as plt


class Layout(object, metaclass=ABCMeta):
    def __init__(self, figure=None):
        self._responsible_for_fig = False
        if figure is None:
            figure = plt.figure()
            self._responsible_for_fig = True
        self._fig = figure

    @property
    def figure(self):
        return self._fig

    def close(self):
        if self._fig is not None:
            plt.close(self._fig)

    def tighten_layout(self, h_pad=None, w_pad=None, rect=None):
        self._fig.tight_layout(h_pad=h_pad, w_pad=w_pad, rect=rect)

    def adjust(self, left=None, bottom=None, right=None, top=None,
               wspace=None, hspace=None):
        # https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.subplots_adjust.html
        self._fig.subplots_adjust(left, bottom, right, top, wspace, hspace)


class Subplot(Layout):
    def __init__(self, n_rows, n_cols, figure=None, sharey=False,
                 sharex=False):
        super().__init__(figure)

        plt.subplots(n_rows, n_cols, sharey=sharey, num=self._fig.number,
                     sharex=sharex)

    def __iter__(self):
        return iter(self._fig.axes)

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


class TwoLegendPlot(Layout):
    def __init__(self, figure=None):
        super().__init__(figure)
        self.legends = []

    def right_legend(self, legend, **kwargs):
        l = legend.decorate(self.figure, location="outside", **kwargs)
        self.legends.append(l)
        for l in self.legends:
            self.figure.gca().add_artist(l)

    def bottom_legend(self, legend, **kwargs):
        l = legend.decorate(self.figure, location="beneath", **kwargs)
        self.legends.append(l)
        for l in self.legends:
            self.figure.gca().add_artist(l)

