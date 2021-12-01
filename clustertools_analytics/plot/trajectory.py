import numpy as np

def filter_nans(ref, *others):
    nan = np.isnan(ref)
    if nan.any():
        mask = ~nan
    else:
        mask = slice(None)

    if len(others) == 0:
        return ref[mask]

    return tuple([ref[mask]] + [o[mask] for o in others])


def filter_nans_yss(xs, yss):
    for ys in yss:
        nan = np.isnan(ys)
        if nan.all():  # Skip all
            continue
        if nan.any():  # Skip those
            mask = ~nan
            yield xs[mask], ys[mask]

        else:
            yield xs, ys


class TrajectoryDisplayer(object):
    def __init__(self):
        self.label2color = {}


    def get_color(self, color, label):
        if color is not None:
            return color
        return self.label2color.get(label)

    def memorize_color(self, color, label):
        if label is not None:
            self.label2color[label] = color


    def __call__(self, ax, xs, yss, convention):
        """
        Parameters
        ----------
        xs: array [k]
            The xs
        yss: list [n, k]
            The ys to aggregate
        """
        for xs, ys in filter_nans_yss(xs, yss):
            color = convention.color
            label = convention.label

            color = self.get_color(color, label)

            l = ax.plot(xs, ys, color=color, alpha=0.8 * convention.alpha,
                        label=label if label not in self.label2color else None,
                        linestyle=convention.linestyle)[0]

            if color is None:
               color = l.get_c()

            self.memorize_color(color, label)





class MinMaxMeanTrajectory(TrajectoryDisplayer):
    def __init__(self, display_all=True):
        super().__init__()
        self.display_all = display_all

    def __call__(self, ax, xs, yss, convention):
        mins = np.nanmin(yss, axis=0)
        maxs = np.nanmax(yss, axis=0)
        means = np.nanmean(yss, axis=0)

        means, mins, maxs, xs_ = filter_nans(means, mins, maxs, xs)

        color = convention.color
        label = convention.label

        color = self.get_color(color, label)

        l = ax.plot(xs_, means, color=color,
                    label=label if label not in self.label2color else None,
                    linestyle=convention.linestyle,
                    alpha=convention.alpha,
                    zorder=2)[0]

        if color is None:
            color = l.get_c()

        self.memorize_color(color, label)

        ax.fill_between(xs_, mins, maxs,
                        facecolor=color,
                        alpha=.5*convention.alpha,
                        zorder=0)



        if self.display_all:
            for xs, ys in filter_nans_yss(xs, yss):
                ax.plot(xs, ys,
                        color=color, alpha=.1*convention.alpha,
                        linestyle=convention.linestyle,
                        zorder=1)


class StdBarTrajectory(TrajectoryDisplayer):
    def __call__(self, ax, xs, yss, convention):
        means = np.nanmean(yss, axis=0)
        stds = np.nanstd(yss, axis=0)

        means, stds, xs = filter_nans(means, stds, xs)

        ax.errorbar(xs, means, yerr=stds,
                    color=convention.color, label=convention.label,
                    linestyle=convention.linestyle, alpha=convention.alpha)