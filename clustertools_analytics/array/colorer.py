from abc import ABCMeta, abstractmethod
from functools import partial

import numpy as np
from matplotlib.cm import get_cmap


class BaseFloatColorer(object, metaclass=ABCMeta):
    @classmethod
    def make_factory(cls, cmap, **kwargs):
        return partial(cls, cmap=cmap, **kwargs)

    def memo(self, cell_value):
        try:
            float_value = float(cell_value)
            self.memo_float(float_value)
        except ValueError:
            pass

    @abstractmethod
    def memo_float(self, float_value):
        pass

    def pack(self):
        return self

    @abstractmethod
    def float_to_color(self, float_value):
        pass

    def __call__(self, float_value):
        self.pack()
        return self.float_to_color(float_value)


class LinearColorer(BaseFloatColorer):
    # Colormap: https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
    def __init__(self, shading_min=0, shading_max=.6, cmap="Greys"):
        self.shading_min = shading_min
        self.shading_max = shading_max
        self.max = float("-inf")
        self.min = float("inf")
        self.color_map = get_cmap(cmap)

    def memo_float(self, float_value):
        if float_value < self.min:
            self.min = float_value
        if self.max < float_value:
            self.max = float_value

    def float_to_color(self, float_value):
        normalized_value = np.interp(
            [float_value], [self.min, self.max],
            [self.shading_min, self.shading_max]
        )[0]
        return self.color_map(float(normalized_value))  # Float value for [0, 1]


class OrdinalColorer(BaseFloatColorer):
    def __init__(self, shading_min=0, shading_max=.6, cmap="Greys",
                 skip_rate=None):
        self.shading_min = shading_min
        self.shading_max = shading_max
        self.color_map = get_cmap(cmap)
        self.skip_rate = skip_rate
        self.memory = []

    def memo_float(self, float_value):
        self.memory.append(float_value)

    def pack(self):
        self.memory.sort()

    def float_to_color(self, float_value):
        idx = 0
        for i, v in enumerate(self.memory):
            idx = i
            if float_value <= v:
                break
        if self.skip_rate is not None:
            ref = self.skip_rate * len(self.memory)
            if self.skip_rate >= 0 and idx < ref:
                return None
            elif self.skip_rate < 0 and idx >= -ref:
                return None
        normalized_value = np.interp(
            [idx], [0, len(self.memory)-1],
            [self.shading_min, self.shading_max]
        )[0]
        return self.color_map(float(normalized_value))  # Float value for [0, 1]


class CircularColorerFactory(object):
    def __init__(self, *color_factories):
        self.index = 0
        self.color_factories = color_factories

    def __call__(self):
        colorer = self.color_factories[self.index]()
        self.index = (self.index + 1) % len(self.color_factories)
        return colorer