import os
from contextlib import contextmanager

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
