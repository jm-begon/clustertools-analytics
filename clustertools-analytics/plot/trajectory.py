class TrajectoryDisplayer(object):
    def __call__(self, ax, xs, yss, convention):
        """
        Parameters
        ----------
        xs: array [n_points]
            The xs
        yss: list [n_points, [n_states]]
            The ys to aggregate
        """
        insert_label = True
        yss = np.array(yss).T
        for ys in yss:
            ax.plot(xs, ys,
                    color=convention.color, alpha=0.8,
                    label=convention.label if insert_label else None,
                    linestyle=convention.linestyle)
            insert_label = False


class MinMaxMeanTrajectory(TrajectoryDisplayer):
    def __init__(self, display_all=True):
        self.display_all = display_all

    def __call__(self, ax, xs, yss, convention):
        mins = [y.min() for y in yss]
        maxs = [y.max() for y in yss]
        means = [y.mean() for y in yss]

        ax.fill_between(xs, mins, maxs,
                        facecolor=convention.color,
                        alpha=.5)

        ax.plot(xs, means, color=convention.color,
                label=convention.label,
                linestyle=convention.linestyle)

        if self.display_all:
            yss = np.array(yss).T
            for ys in yss:
                ax.plot(xs, ys,
                        color=convention.color, alpha=.1,
                        linestyle=convention.linestyle)


class StdBarTrajectory(TrajectoryDisplayer):
    def __call__(self, ax, xs, yss, convention):
        means = [y.mean() for y in yss]
        stds = [y.std() for y in yss]
        ax.errorbar(xs, means, yerr=stds,
                    color=convention.color, label=convention.label,
                    linestyle=convention.linestyle)