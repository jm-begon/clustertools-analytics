import numpy as np


def filter_nans(xs, yss):
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
    def __call__(self, ax, xs, yss, convention):
        """
        Parameters
        ----------
        xs: array [k]
            The xs
        yss: list [n, k]
            The ys to aggregate
        """
        insert_label = True
        for xs, ys in filter_nans(xs, yss):
            ax.plot(xs, ys,
                    color=convention.color, alpha=0.8*convention.alpha,
                    label=convention.label if insert_label else None,
                    linestyle=convention.linestyle)
            insert_label = False


class MinMaxMeanTrajectory(TrajectoryDisplayer):
    def __init__(self, display_all=True):
        self.display_all = display_all

    def __call__(self, ax, xs, yss, convention):
        mins = np.nanmin(yss, axis=0)
        maxs = np.nanmax(yss, axis=0)
        means = np.nanmean(yss, axis=0)

        xs_ = xs
        nan = np.isnan(means)
        if nan.any():
            mask = ~nan
            xs_ = xs[mask]
            mins, maxs, means = mins[mask], maxs[mask], means[mask]

        ax.fill_between(xs_, mins, maxs,
                        facecolor=convention.color,
                        alpha=.5*convention.alpha)

        ax.plot(xs_, means, color=convention.color,
                label=convention.label,
                linestyle=convention.linestyle,
                alpha=convention.alpha)

        if self.display_all:
            for xs, ys in filter_nans(xs, yss):
                ax.plot(xs, ys,
                        color=convention.color, alpha=.1*convention.alpha,
                        linestyle=convention.linestyle)


class StdBarTrajectory(TrajectoryDisplayer):
    def __call__(self, ax, xs, yss, convention):
        means = np.nanmean(yss, axis=0)
        stds = np.nanstd(yss, axis=0)

        nan = np.isnan(means)
        if nan.any():
            mask = ~nan
            xs, means, stds, = xs[mask], means[mask], stds[mask]

        ax.errorbar(xs, means, yerr=stds,
                    color=convention.color, label=convention.label,
                    linestyle=convention.linestyle, alpha=convention.alpha)