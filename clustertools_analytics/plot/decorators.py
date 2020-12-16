import matplotlib.ticker as ticker

from .plot import Plot2D


class TextDecorator(Plot2D):
    def __init__(self, decorated, xlabel=None, ylabel=None, title=None,
                 xlabel_rot=None):
        super().__init__(decorated)
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.xlabel_rot = xlabel_rot

    def plot_(self, cube, **kwargs):
        if self.xlabel:
            self.axes.set_xlabel(self.xlabel)
        if self.xlabel_rot:
            for tick in self.axes.get_xticklabels():
                tick.set_rotation(self.xlabel_rot)
        if self.ylabel:
            self.axes.set_ylabel(self.ylabel)
        if self.title:
            self.axes.set_title(self.title)


class LegendDecorator(Plot2D):

    def __init__(self, decorated, location='best', title=None, zorder=None,
                 **props):
        super().__init__(decorated)
        self.location = location
        self.title = title
        self.zorder = zorder
        self.props = props

    def plot_(self, cube, **kwargs):
        if self.location == "outside":
            # Shrink current axis by 20%
            box = self.axes.get_position()
            self.axes.set_position(
                [box.x0, box.y0, box.width * .95, box.height])

            legend = self.axes.legend(loc="upper left", bbox_to_anchor=(1, 1),
                                      title=self.title, prop=self.props)
        else:
            legend = self.axes.legend(loc=self.location, title=self.title,
                                      prop=self.props)

        if self.zorder is not None:
            legend.zorder = self.zorder




class GridDecorator(Plot2D):
    def __init__(self, decorated, xgrid=True, ygrid=True):
        super().__init__(decorated)
        self.xgrid = xgrid
        self.ygrid = ygrid

    def plot_(self, cube, **kwargs):
        self.axes.grid(False)
        if self.xgrid:
            self.axes.xaxis.grid(True)
        if self.ygrid:
            self.axes.yaxis.grid(True, which="both")


class LimitDecorator(Plot2D):
    def __init__(self, decorated, x_min=None, x_max=None, y_min=None,
                 y_max=None):
        # TODO add support for ticks
        super().__init__(decorated)
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    def plot_(self, cube, **kwargs):

        self.axes.set_xlim(self.x_min, self.x_max)
        self.axes.set_ylim(self.y_min, self.y_max)


class SameLimitDecorator(Plot2D):
    def plot(self, *cubes, **kwargs):
        super().plot(*cubes, **kwargs)
        y_min, y_max = self.axes.get_ylim()
        x_min, x_max = self.axes.get_xlim()

        min = y_min if y_min < x_min else x_min
        max = y_max if y_max > x_max else x_max

        self.axes.set_xlim(min, max)
        self.axes.set_ylim(min, max)

        return self


class TimeConverter(Plot2D):
    def __init__(self, decorated, on_x=True, label="Duration"):
        super().__init__(decorated)
        self.on_x = on_x
        self.label = label

    def plot_(self, cube, **kwargs):
        if self.on_x:
            get_ticks = self.axes.get_xticks
            formatter = self.axes.xaxis.set_major_formatter
            set_label = self.axes.set_xlabel
        else:
            get_ticks = self.axes.get_yticks
            formatter = self.axes.xaxis.set_major_formatter
            set_label = self.axes.set_ylabel

        # print([t.get_text() for t in get_ticks()])

        # ticks = np.array([float(t.get_text()) for t in get_ticks()])
        ticks = get_ticks()
        ref_val = ticks[int(len(ticks) / 2)]
        if ref_val / 86400 > 1:
            # Days
            unit = "Days"
            divider = 86400
        elif ref_val / 3600 > 1:
            # Hours
            unit = "Hours"
            divider = 3600
        elif ref_val / 60 > 1:
            # Minutes
            unit = "Minutes"
            divider = 60
        else:
            # Seconds
            unit = "Seconds"
            divider = 1

        formatter(
            ticker.FuncFormatter(lambda x, pos: '{:.2f}'.format(x / divider)))
        set_label("{} [{}]".format(self.label, unit))


class TightLayout(Plot2D):
    def __init__(self, decorated=None, pad=1.08, h_pad=None, w_pad=None,
                 rect=None):
        super().__init__(decorated)
        self.pad = pad
        self.h_pad = h_pad
        self.w_pad = w_pad
        self.rect = rect

    def pack(self):
        self.axes.figure.tight_layout(pad=self.pad, h_pad=self.h_pad,
                                      w_pad=self.w_pad, rect=self.rect)


# class TrajectoryDecorator(Plot2D):
#     def __init__(self, decorated, ylabel, xlabel="Epochs", subtitle=None,
#                  y_min=None, y_max=None):
#         if subtitle is None:
#             subtitle = "{} with repect to {}".format(ylabel, xlabel)
#         super().__init__(
#             GridDecorator(
#                 LegendDecorator(
#                     DBAndArchTextDecorator(
#                         LimitDecorator(decorated, y_min=y_min, y_max=y_max),
#                         xlabel, ylabel, subtitle
#                     )
#                 )
#             )
#         )
