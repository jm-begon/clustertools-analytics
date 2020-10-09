from abc import ABCMeta, abstractmethod
from functools import partial

import numpy as np
from matplotlib.cm import get_cmap

from clustertools_analytics.array.base import Number
from clustertools_analytics.array.customizer import CellCustomizer


class CircularColorerFactory(object):
    def __init__(self, *color_factories):
        self.index = 0
        self.color_factories = color_factories

    def __call__(self):
        colorer = self.color_factories[self.index]()
        self.index = (self.index + 1) % len(self.color_factories)
        return colorer


class BaseColorPicker(object, metaclass=ABCMeta):
    def __init__(self, *reference_values):
        self.reference_values = reference_values

    def __call__(self, float_value):
        pass


class Shader(BaseColorPicker):
    def __init__(self, *reference_values, shading_min=0, shading_max=.6,
                 cmap="Greys"):
        super().__init__(reference_values)
        self.shading_min = shading_min
        self.shading_max = shading_max
        self.color_map = get_cmap(cmap)

    def interpolate(self, value, min_value, max_value):
        normalized_value = np.interp(
            [value], [min_value, max_value],
            [self.shading_min, self.shading_max]
        )[0]
        return self.color_map(float(normalized_value))  # Float value for [0, 1]


class LinearShader(Shader):
    # Colormap: https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
    def __init__(self, *reference_values, shading_min=0, shading_max=.6,
                 cmap="Greys"):
        super().__init__(*reference_values, shading_min=shading_min,
                         shading_max=shading_max, cmap=cmap)

        self.max = float("-inf")
        self.min = float("inf")
        for float_value in self.reference_values:
            if float_value < self.min:
                self.min = float_value
            if self.max < float_value:
                self.max = float_value


    def __call__(self, float_value):
        return self.interpolate(float_value, self.min, self.max)


class OrdinalShader(Shader):
    def __init__(self, *reference_values, shading_min=0, shading_max=.6,
                 cmap="Greys", skip_rate=None, inverse=False):

        reference_values = [x for x in reference_values]  # copy as a list
        reference_values.sort(reverse=inverse)
        super().__init__(*reference_values, shading_min=shading_min,
                         shading_max=shading_max, cmap=cmap)
        self.skip_rate = skip_rate
        self.inverse = inverse

    def _lookup_float_index(self, float_value):
        idx = 0
        for i, v in enumerate(self.reference_values):
            idx = i
            if not self.inverse and float_value <= v:
                break
            if self.inverse and float_value >= v:
                break
        return idx

    def _should_skip(self, idx):
        if self.skip_rate is not None:
            ref = self.skip_rate * len(self.reference_values)
            if self.skip_rate >= 0 and idx < ref:
                return True
            elif self.skip_rate < 0 and idx >= -ref:
                return True
        return False

    def __call__(self, float_value):
        idx = self._lookup_float_index(float_value)
        if not self._should_skip(idx):
            return self.interpolate(idx, 0, len(self.reference_values)-1)



class Colorer(CellCustomizer):
    @classmethod
    def make_factory(cls, color_picker_factory, **kwargs):
        return partial(cls, color_picker_factory=partial(color_picker_factory, **kwargs))

    @classmethod
    def get_default_filter_class(cls):
        return Number

    def __init__(self, color_picker_factory, background=True):
        self.color_picker_factory = color_picker_factory
        self.color_picker = None
        self.background = background
        self.memory = []

    def memo(self, cell_value):
        try:
            float_value = float(cell_value)
            self.memory.append(float_value)
        except ValueError:
            pass

    def pack(self):
        self.color_picker = self.color_picker_factory(*self.memory)


    def customize_approved_cell(self, cell):
        if not self.color_picker:
            self.pack()

        color = self.color_picker(float(cell))
        p = "background_color" if self.background else "color"
        cell[p] = color


