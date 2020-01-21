"""
Nice color scheme can be found at http://colorbrewer2.org
The default matplotlib colormap:
    https://matplotlib.org/tutorials/colors/colormaps.html
    https://matplotlib.org/tutorials/colors/colormaps.html#palettable
"""
# TODO make color scheme ala matplotlib (https://matplotlib.org/tutorials/colors/colormap-manipulation.html)


class Convention(object):
    def __init__(self, label, color, linestyle="-", marker="o", hatch=None,
                 legend_name=None, alpha=1.):
        self.label = label
        self.color = color
        self.linestyle = linestyle
        self.marker = marker
        self.hatch = hatch
        self.alpha = alpha
        self.legend_name = legend_name


class ConventionFactory(object):
    def __call__(self, cube):
        pass


def default_factory(cube):
    return Convention(None, None, None, None)


class OverrideConventionFactory(ConventionFactory):
    def __init__(self, convention_factory, **kwargs):
        self.factory = convention_factory
        self.override_dict = kwargs

    def __call__(self, cube):
        convention = self.factory(cube)
        for k, v in self.override_dict.items():
            setattr(convention, k, v)
        return convention


class CstFactory(ConventionFactory):
    def __init__(self, label, color, linestyle="-", marker="o", hatch=None,
                 legend_name=None, alpha=1.):
        self.convetion = Convention(label, color, linestyle, marker,
                                    hatch, legend_name, alpha)

    def __call__(self, cube):
        return self.convetion