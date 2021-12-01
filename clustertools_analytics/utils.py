import os
import warnings
from contextlib import contextmanager

import numpy as np
from scipy.stats import chi2

from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class EmptyCube(object):
    """Empty cube to avoid exceptions being raised"""
    def __init__(self, decorated):
        self.decorated = decorated

    def __call__(self, *args, **kwargs):
        return self

    def __len__(self):
        return len(self.decorated)

    def __repr__(self):
        return repr(self.decorated)

    def __getattr__(self, name):
        return getattr(self.decorated, name)


@contextmanager
def save_pdf(fname):
    fpath = os.path.realpath("{}.pdf".format(fname))
    pp = PdfPages(fpath)
    fig = plt.figure()
    try:
        yield
    finally:
        pp.savefig(fig)
        plt.close(fig)
        pp.close()


class PDFSaver(object):
    @classmethod
    def create_empty_figure(cls, **kwargs):
        return plt.figure(**kwargs)

    def __init__(self, fname):
        self.fpath = os.path.realpath("{}.pdf".format(fname))
        self.fig = None
        self.PdfPages = None

    def _close(self, save=True):
        if self.fig is not None:
            try:
                if save:
                    self.PdfPages.savefig(self.fig)
            finally:
                plt.close(self.fig)

    def new_figure(self):
        self._close()
        self.fig = plt.figure()
        return self.fig

    def drop_figure(self):
        self._close(False)
        self.fig = None

    def __enter__(self):
        self.PdfPages = PdfPages(self.fpath)
        self.new_figure()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._close(exc_val is None)
        finally:
            self.PdfPages.close()

    def new_note(self, message, new_fig_for_note=True, new_fig=False):
        fig = self.new_figure() if new_fig_for_note else self.fig
        plt.text(0.5, 0.5, message, verticalalignment='center',
                 horizontalalignment='center', wrap=True)

        fig.patch.set_visible(False)
        for ax in fig.axes:
            ax.axis('off')

        if new_fig:
            return self.new_figure()
        return fig

    def switch_figure(self, figure, save_current=True):
        self._close(save_current)
        self.fig = figure
        return self.fig


class Ellipse2D(object):
    @classmethod
    def create_dispersion(cls, xs, ys, ci=0.95):
        from scipy import linalg

        # Filter nan
        nans = np.logical_or(np.isnan(xs), np.isnan(ys))
        if np.sum(nans) > 0:
            warnings.warn("Skipping NaNs")
            xs = xs[~nans]
            ys = ys[~nans]

        # Estimate parameters
        center = np.mean(xs), np.mean(ys)
        cov = np.cov(xs, ys)

        # Adjust size to confidence interval
        scale = chi2.ppf(ci, 2)
        U, S, V = linalg.svd(cov)
        S2 = np.array([[S[0], 0], [0, S[1]]]) * scale
        cov = U @ S2 @ V

        return cls(center, cov)

    def __init__(self, center, cov):
        self.center = center
        self.cov = cov
        self.eps = 1e-10

    @property
    def eigenvalues(self):
        a, b, c = self.cov[0, 0], self.cov[0, 1], self.cov[1, 1]
        p = (a + c) / 2.
        q = np.sqrt(((a-c)/2.)**2 + b**2)
        return p+q, p-q

    @property
    def major_axis(self):
        return np.sqrt(self.eigenvalues[0])

    @property
    def minor_axis(self):
        return np.sqrt(self.eigenvalues[1])

    @property
    def angle(self):
        a, b, c = self.cov[0, 0], self.cov[0, 1], self.cov[1, 1]
        if np.abs(b) < self.eps:
            return 0 if a >= c else np.pi/2
        return np.arctan2(self.major_axis**2-a, b)

    @property
    def angle_deg(self):
        return 180 * self.angle / np.pi

    def get_width_height(self):
        l1, l2 = self.eigenvalues
        d1, d2 = 2*np.sqrt(l1), 2*np.sqrt(l2)

        if self.cov[0, 0] > self.cov[1, 1]:
            return d1, d2
        else:
            return d2, d1

    def is_inside(self, x, y):
        x_c = x - self.center[0]
        y_c = y - self.center[1]

        angle = -self.angle
        cos = np.cos(angle)
        sin = np.sin(angle)

        x_e = x_c * cos - y_c * sin
        y_e = x_c * sin + y_c * cos

        r_x, r_y = [d/2 for d in self.get_width_height()]

        print("Radii:", r_x, r_y)

        x2, a2, y2, b2 = x_e**2, r_x**2, y_e**2, r_y**2

        return x2*b2 + y2*a2 <= a2*b2


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    from matplotlib.patches import Ellipse

    center = (150, 500)
    cov = np.array([[9, 5], [5, 4]])

    raw_ellipse = Ellipse2D(center, cov)

    rng = np.random.default_rng()

    ps = rng.multivariate_normal(center, cov, 10000)
    xs, ys = ps[:, 0], ps[:, 1]

    ellipse = Ellipse2D.create_dispersion(xs, ys)

    ii = ellipse.is_inside(xs, ys)

    fig = plt.figure()
    plt.scatter(xs, ys)

    width, height = ellipse.get_width_height()

    plt_ell = Ellipse(ellipse.center, width, height, ellipse.angle_deg,
                      facecolor="none", edgecolor='r')
    ax = fig.gca()
    ax.add_patch(plt_ell)
    plt.show()

    plt.close()


