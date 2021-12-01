import warnings
from abc import ABCMeta
from functools import partial

import numpy as np

from clustertools import Datacube


def name_to_accessor(metric_accessor):
    if isinstance(metric_accessor, str):
        return GetByName(metric_accessor)
    return metric_accessor


class Accessor(object, metaclass=ABCMeta):
    def access(self, cube):
        pass

    def __call__(self, cube):
        """
        Return an numpy array of appropriate shape based on the `cube`.
        """
        try:
            return self.access(cube)
        except Exception as e:
            raise ValueError("Error with cube '{}' ({})"
                             "".format(cube.name,
                                       self.__class__.__name__)) from e

    @property
    def n_outputs(self):
        return 1


class NumpyfySqueeze(Accessor):
    def __init__(self, metric_name):
        self.metric_name = metric_name

    def access(self, cube):
        return cube(self.metric_name).numpyfy(True).squeeze()

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)


class GetByName(Accessor):
    def __init__(self, metric_name):
        self.metric_name = metric_name

    def access(self, cube):
        return cube(self.metric_name)

    def __repr__(self):
        return "{}(metric_name={})".format(self.__class__.__name__,
                                           self.metric_name)


class MetricOverParameter(Accessor):
    def __init__(self, metric_accessor, *parameter_names, aggregator=None,
                 auto_numpyfy=True):
        self.metric_accessor = name_to_accessor(metric_accessor)
        self.parameter_names = parameter_names
        self.aggregator = aggregator if aggregator is not None else \
            partial(np.array, dtype=np.float)
        self.auto_numpyfy = auto_numpyfy

    def access(self, cube):
        values = []
        for t, cube_i in cube.iter_dimensions(*self.parameter_names):
            v = self.metric_accessor(cube_i)
            if isinstance(v, Datacube):
                if self.auto_numpyfy:
                    v = v.numpyfy(True).squeeze()
                else:
                    raise ValueError("Datacube '{}' is not reduced by {} "
                                     "".format(cube.name, repr(self)))
            if v is None:
                d = {p: v for p,v in zip(self.parameter_names, t)}
                warnings.warn("Missing values for {} of "
                              "cube '{}' (at {}): {} from {}"
                              "".format(repr(d), cube.name, repr(self),
                                        cube_i, cube))
            else:
                values.append(v)

        return self.aggregator(values)

    def __repr__(self):
        return super().__repr__()  # TODO


class DiffAccessor(Accessor):
    def __init__(self, accessor_1, accessor_2):
        self.accessor_1 = name_to_accessor(accessor_1)
        self.accessor_2 = name_to_accessor(accessor_2)

    def access(self, cube):
        return self.accessor_1(cube) - self.accessor_2(cube)

    def __repr__(self):
        return "{}(accessor_1={}, accessor_2={})" \
               "".format(self.__class__.__name__, self.accessor_1,
                         self.accessor_2)


class DomainAccessor(Accessor):
    def __init__(self, parameter_name):
        self.parameter_name = parameter_name

    def access(self, cube):
        return np.array(float(v) for v, _ in
                        cube.iter_dimensions(self.parameter_name))

    def __repr__(self):
        return "{}(parameter_name={})".format(self.__class__.__name__,
                                              self.parameter_name)


class FirstAccess(MetricOverParameter):
    def access(self, cube):
        for _, cube_i in cube.iter_dimensions(*self.parameter_names):
            return self.aggregator(self.metric_accessor(cube_i))


class SeriesAccessor(Accessor, metaclass=ABCMeta):
    """
    `SeriesAccessor`
    ===============
    A `SeriesAccessor` instance is a callable which return, from a cube:

    xs: np.array [k]
        The absica
    yss: np.array [n, k]
        n series of k values, where n=p1 * p2 * ..., the domain of the
        parameters to synthesize
    """

    @property
    def n_outputs(self):
        return 2

    def __call__(self, cube):
        xs, yss = super().__call__(cube)
        if yss.ndim == 1:
            yss = yss[np.newaxis, ...]
        return xs, yss


class YSeriesXRangeAccessor(SeriesAccessor):
    """
    `SeriesAccessor`
    ===============
    A `SeriesAccessor` instance is a callable which returns, from a cube:

    xs: np.array [k]
        The absica
    yss: np.array [n, k]
        n series of k values, where n=p1 * p2 * ..., the domain of the
        parameters to synthesize
    """
    def __init__(self, y_name, *parameter_names):
        self.y_accessor = MetricOverParameter(y_name, *parameter_names,
                                              aggregator=None,
                                              auto_numpyfy=False)

    def __repr__(self):
        return "{}(y_name={}, parameter_names=*{})" \
               "".format(self.__class__.__name__,
                         repr(self.y_accessor.metric_accessor),
                         repr(self.y_accessor.parameter_names))

    def access(self, cube):
        yss = self.y_accessor(cube)
        xs = np.arange(yss.shape[1])
        return xs, yss


class XSeriesYSeries(YSeriesXRangeAccessor):
    def __init__(self, x_name, y_name, *parameter_names):
        super().__init__(y_name, *parameter_names)
        self.x_accessor = FirstAccess(x_name, *parameter_names,
                                      aggregator=None,
                                      auto_numpyfy=False)

    def __repr__(self):
        return "{}(x_name={}, y_name={}, parameter_names=*{})" \
               "".format(self.__class__.__name__,
                         repr(self.x_accessor.metric_accessor),
                         repr(self.y_accessor.metric_accessor),
                         repr(self.y_accessor.parameter_names))

    def access(self, cube):
        yss = self.y_accessor(cube)
        xs = self.x_accessor(cube)
        return xs, yss


class InterpXYSeries(XSeriesYSeries):
    def __init__(self, interp_points, x_accessor, y_accessor, *parameter_names,
                 left=None, right=None, period=None):
        self.interp_points = interp_points
        super().__init__(x_accessor, y_accessor, *parameter_names)
        self.left = left
        self.right = right
        self.period = period


    def access(self, cube):
        yss = self.y_accessor(cube)
        xs = self.x_accessor(cube)
        if xs.ndim == 2:
            xss = xs
        else:
            xss = [xs for _ in range(len(yss))]

        ps = self.interp_points if not isinstance(self.interp_points, Accessor) \
            else self.interp_points(cube)

        if ps.ndim == 2:
            pss = ps
        else:
            pss = [ps for _ in range(len(yss))]

        results = []
        for ps, xs, ys in zip(pss, xss, yss):
            r = np.interp(ps, xs, ys, left=self.left, right=self.right,
                          period=self.period)
            results.append(r)

        results = np.array(results)

        return pss[0], results




class YSeriesByParamOverParams(SeriesAccessor):
    """
    The values are of an atomic metric, ordered by a parameter domain value.
    The number of datapoints (n) are from the other parameters
    """
    def __init__(self, metric_name, by_param_name, *parameter_names):
        self.by_param_name = by_param_name
        self.metric_accessor = name_to_accessor(metric_name)
        self.parameter_names = parameter_names

    def access(self, cube):
        values = []
        xs = []
        for (x,), cube_i in cube.iter_dimensions(self.by_param_name):
            xs.append(float(x))
            for _, cube_ii in cube_i.iter_dimensions(*self.parameter_names):
                values.append(self.metric_accessor(cube_ii))

        xs = np.array(xs)
        yss = np.array(values, dtype=np.float).T
        return xs, yss

    def __repr__(self):
        return "{}(metric_name={}, by_param_name={}, parameter_names=*{})" \
               "".format(self.__class__.__name__,
                         repr(self.metric_accessor),
                         repr(self.by_param_name),
                         repr(self.y_accessor.parameter_names))


class MedianFilteredSeries(SeriesAccessor):
    def __init__(self, decorated, window_size=10):
        self.decorated = decorated
        self.window_size = window_size

    def access(self, cube):
        from scipy.ndimage import median_filter
        xs, yss = self.decorated.access(cube)

        yss = median_filter(yss, size=(1, self.window_size))

        return xs, yss


class SamplingSeries(SeriesAccessor):
    def __init__(self, decorated, sampling_rate=.1):
        self.decorated = decorated
        self.sampling_rate = sampling_rate

    def access(self, cube):
        from scipy.ndimage import median_filter
        xs, yss = self.decorated.access(cube)

        span = int(self.sampling_rate * len(xs))
        xs, yss = xs[::span], yss[:, ::span]
        return xs, yss


class DeltaSeries(SeriesAccessor):
    def __init__(self, first_accessors, second_accessors):
        self.first_accessors = first_accessors
        self.second_accessors = second_accessors

    def access(self, cube):
        xs, yss1 = self.first_accessors(cube)
        _, yss2 = self.second_accessors(cube)
        return xs, yss1 - yss2

    def __repr__(self):
        return "{}(first_accessors={}, second_accessors={})" \
               "".format(self.__class__.__name__,
                         repr(self.first_accessors),
                         repr(self.second_accessors),)


class AtomicAcessor(MetricOverParameter):
    """
    `AtomicAccessor`
    ===============
    An `AtomicAcessor` instance is a callable which returns, from a cube:

    vs: np.array [k]
    """
    def __init__(self, metric_name, *parameter_names):
        super().__init__(metric_name, *parameter_names, aggregator=None,
                         auto_numpyfy=False)



