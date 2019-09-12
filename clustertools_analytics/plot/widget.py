from abc import ABCMeta, abstractmethod
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib as mpl

from clustertools_analytics import Plot2D


class Widget(object, metaclass=ABCMeta):

    def get_axes(self, decorated):
        if decorated is None:
            # Responsible to close the figure
            fig = plt.figure()
            return fig.gca()
        elif isinstance(decorated, Figure):
            return decorated.gca()
        elif isinstance(decorated, Axes):
            return decorated
        elif isinstance(decorated, Plot2D):
            return decorated.axes

    @abstractmethod
    def decorate(self, decorated, **kwargs):
        pass


class Legend(Widget):
    @classmethod
    def make_handle(cls, type="line", marker=None, color=None, linestyle=None,
                    label=None, alpha=None):
        if type == "line":
            handle = mpl.lines.Line2D([], [], marker=marker, color=color,
                                      linestyle=linestyle, label=label,
                                      alpha=alpha)
        else:
            raise AttributeError("Unknown handle type '{}'".format(type))

        return handle

    def __init__(self, title, handles):
        self.title = title
        self.handles = handles

    def decorate(self, decorated, location="best", **kwargs):
        labels = [h.get_label() for h in self.handles]
        if location == "outside":
            # Shrink current axis by 20%
            # box = self.axes.get_position()
            # self.axes.set_position(
            #     [box.x0, box.y0, box.width * .95, box.height])

            l = self.get_axes(decorated).legend(handles=self.handles,
                                                labels=labels,
                                                loc="upper left",
                                                bbox_to_anchor=(1.02, 1),
                                                borderaxespad=0.,
                                                title=self.title,
                                                **kwargs)
        elif location == "beneath":
            l = self.get_axes(decorated).legend(handles=self.handles,
                                                labels=labels,
                                                loc="upper left",
                                                bbox_to_anchor=(0, -0.3),
                                                borderaxespad=0.,
                                                title=self.title,
                                                **kwargs)
        else:
            l = self.get_axes(decorated).legend(handles=self.handles,
                                                labels=labels,
                                                loc=location,
                                                title=self.title, **kwargs)

        return l
