"""Statistical Manifold of Binomial distributions with the Fisher metric.

Lead authors: Jules Deschamps, Tra My Nguyen.
"""
from scipy.special import factorial
from scipy.stats import binom

import geomstats.backend as gs
from geomstats.geometry.base import OpenSet
from geomstats.geometry.euclidean import Euclidean
from geomstats.geometry.riemannian_metric import RiemannianMetric
from geomstats.information_geometry.base import (
    InformationManifoldMixin,
    ScipyUnivariateRandomVariable,
)


class BinomialDistributions(InformationManifoldMixin, OpenSet):
    """Class for the manifold of binomial distributions.

    This is the parameter space of binomial distributions
    i.e. the half-line of positive reals.
    """

    def __init__(self, n_draws, equip=True):
        super().__init__(
            dim=1,
            support_shape=(),
            embedding_space=Euclidean(dim=1, equip=False),
            equip=equip,
        )
        self.n_draws = n_draws
        self._scp_rv = BinomialDistributionsRandomVariable(self)

    @staticmethod
    def default_metric():
        """Metric to equip the space with if equip is True."""
        return BinomialMetric

    def belongs(self, point, atol=gs.atol):
        """Evaluate if a point belongs to the manifold of binomial distributions.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            Point to be checked.
        atol : float
            Tolerance to evaluate if point belongs to (0,1).
            Optional, default: gs.atol

        Returns
        -------
        belongs : array-like, shape=[...,]
            Boolean indicating whether point represents a binomial
            distribution.
        """
        belongs_shape = self.shape == point.shape[-self.point_ndim :]
        if not belongs_shape:
            shape = point.shape[: -self.point_ndim]
            return gs.zeros(shape, dtype=bool)
        return gs.squeeze(gs.logical_and(atol <= point, point <= 1 - atol), axis=-1)

    def random_point(self, n_samples=1):
        """Sample parameters of binomial distributions.

        The uniform distribution on [0, 1] is used.

        Parameters
        ----------
        n_samples : int
            Number of samples.
            Optional, default: 1.

        Returns
        -------
        samples : array-like, shape=[..., dim]
            Sample of points representing binomial distributions.
        """
        size = (n_samples, self.dim) if n_samples != 1 else (self.dim,)
        return gs.random.rand(*size)

    def projection(self, point, atol=gs.atol):
        """Project a point in ambient space to the parameter set.

        The parameter is floored to `gs.atol` if it is negative
        and to '1-gs.atol' if it is greater than 1.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            Point in ambient space.
        atol : float
            Tolerance to evaluate positivity.

        Returns
        -------
        projected : array-like, shape=[..., 1]
            Projected point.
        """
        return gs.where(
            gs.logical_or(point < atol, point > 1 - atol),
            (1 - atol) * gs.cast(point > 1 - atol, point.dtype)
            + atol * gs.cast(point < atol, point.dtype),
            point,
        )

    def sample(self, point, n_samples=1):
        """Sample from the binomial distribution.

        Sample from the binomial distribution with parameter provided by point.

        Parameters
        ----------
        point : array-like, shape=[..., dim]
            Point representing a binomial distribution.
        n_samples : int
            Number of points to sample with for each parameter in point.
            Optional, default: 1.

        Returns
        -------
        samples : array-like, shape=[..., n_samples]
            Sample from binomial distributions.
        """
        return self._scp_rv.rvs(point, n_samples)

    def point_to_pdf(self, point):
        """Compute pmf associated to point.

        Compute the probability mass function of the binomial
        distribution with parameters provided by point.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            Point representing a binomial distribution (probability of success).

        Returns
        -------
        pmf : function
            Probability mass function of the binomial distribution with
            parameters provided by point.
        """

        def pmf(k):
            """Generate parameterized function for binomial pmf.

            Parameters
            ----------
            k : array-like, shape=[n_samples,]
                Integers in {0, ..., n_draws} at which to
                compute the probability mass function.

            Returns
            -------
            pmf_at_k : array-like, shape=[..., n_samples]
                Values of pdf at k for each value of the parameters provided
                by point.
            """
            k = gs.reshape(gs.array(k), (-1,))
            const = factorial(self.n_draws) / (
                factorial(k) * factorial(self.n_draws - k)
            )
            return (
                gs.from_numpy(const)
                * (point**k)
                * ((1 - point) ** (self.n_draws - k))
            )

        return pmf


class BinomialMetric(RiemannianMetric):
    """Class for the Fisher information metric on binomial distributions.

    References
    ----------
    .. [AM1981] Atkinson, C., & Mitchell, A. F. (1981). Rao's distance measure.
        Sankhyā: The Indian Journal of Statistics, Series A, 345-365.
    """

    def squared_dist(self, point_a, point_b):
        """Compute squared distance associated with the binomial Fisher Rao metric.

        Parameters
        ----------
        point_a : array-like, shape=[..., 1]
            Point representing a binomial distribution (probability of success).
        point_b : array-like, shape=[..., 1]
            Point representing a binomial distribution (probability of success).

        Returns
        -------
        squared_dist : array-like, shape=[...,]
            Squared distance between points point_a and point_b.
        """
        return gs.squeeze(
            4
            * self._space.n_draws
            * (gs.arcsin(gs.sqrt(point_a)) - gs.arcsin(gs.sqrt(point_b))) ** 2,
            axis=-1,
        )

    def metric_matrix(self, base_point):
        """Compute the metric matrix at the tangent space at base_point.

        Parameters
        ----------
        base_point : array-like, shape=[..., 1]
            Point representing a binomial distribution.

        Returns
        -------
        mat : array-like, shape=[..., 1, 1]
            Metric matrix.
        """
        return gs.expand_dims(
            self._space.n_draws / (base_point * (1 - base_point)), axis=-1
        )

    def _geodesic_path(self, t, initial_phase, frequency):
        """Generate parameterized function for geodesic curve.

        Parameters
        ----------
        t : array-like, shape=[n_times,]
            Times at which to compute points of the geodesics.

        Returns
        -------
        geodesic : array-like, shape=[..., n_times, 1]
            Values of the geodesic at times t.
        """
        return gs.expand_dims(gs.sin(frequency * t + initial_phase) ** 2, axis=-1)

    def _geodesic_ivp(self, initial_point, initial_tangent_vec):
        """Solve geodesic initial value problem.

        Compute the parameterized function for the geodesic starting at
        initial_point with initial velocity given by initial_tangent_vec.

        Parameters
        ----------
        initial_point : array-like, shape=[..., 1]
            Initial point.

        initial_tangent_vec : array-like, shape=[..., 1]
            Tangent vector at initial point.

        Returns
        -------
        path : function
            Parameterized function for the geodesic curve starting at
            initial_point with velocity initial_tangent_vec.
        """
        initial_phase = gs.arcsin(gs.sqrt(initial_point))
        frequency = initial_tangent_vec / (
            2.0 * gs.sqrt(initial_point) * gs.sqrt(1 - initial_point)
        )
        return lambda t: self._geodesic_path(t, initial_phase, frequency)

    def _geodesic_bvp(self, initial_point, end_point):
        """Solve geodesic boundary problem.

        Compute the parameterized function for the geodesic starting at
        initial_point and ending at end_point.

        Parameters
        ----------
        initial_point : array-like, shape=[..., 1]
            Initial point.
        end_point : array-like, shape=[..., 1]
            End point.

        Returns
        -------
        path : function
            Parameterized function for the geodesic curve starting at
            initial_point and ending at end_point.
        """
        initial_phase = gs.arcsin(gs.sqrt(initial_point))
        frequency = gs.arcsin(gs.sqrt(end_point)) - initial_phase
        return lambda t: self._geodesic_path(t, initial_phase, frequency)

    def exp(self, tangent_vec, base_point):
        """Compute exp map of a base point in tangent vector direction.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., 1]
            Tangent vector at base point.
        base_point : array-like, shape=[..., 1]
            Base point.

        Returns
        -------
        exp : array-like, shape=[..., 1]
            End point of the geodesic starting at base_point with
            initial velocity tangent_vec.
        """
        return (
            gs.sin(
                tangent_vec / (2.0 * gs.sqrt(base_point) * gs.sqrt(1 - base_point))
                + gs.arcsin(gs.sqrt(base_point))
            )
            ** 2
        )

    def log(self, point, base_point):
        """Compute log map using a base point and an end point.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            End point.
        base_point : array-like, shape=[..., 1]
            Base point.

        Returns
        -------
        tangent_vec : array-like, shape=[..., 1]
            Initial velocity of the geodesic starting at base_point and
            reaching point at time 1.
        """
        return (
            2
            * gs.sqrt(base_point)
            * gs.sqrt(1 - base_point)
            * (gs.arcsin(gs.sqrt(point)) - gs.arcsin(gs.sqrt(base_point)))
        )


class BinomialDistributionsRandomVariable(ScipyUnivariateRandomVariable):
    """A binomial random variable."""

    def __init__(self, space):
        rvs = lambda *args, **kwargs: binom.rvs(space.n_draws, *args, **kwargs)
        super().__init__(space, rvs)

    def _flatten_params(self, point, pre_flat_shape):
        flat_point = gs.reshape(gs.broadcast_to(point, pre_flat_shape), (-1,))
        return {"p": flat_point}

    def pdf(self, x, point):
        """Evaluate the probability density function at x.

        Parameters
        ----------
        x : array-like, shape=[n_samples, *support_shape]
            Sample points at which to compute the probability density function.
        point : array-like, shape=[..., *space.shape]
            Point representing a distribution.

        Returns
        -------
        pdf_at_x : array-like, shape=[..., n_samples, *support_shape]
            Values of pdf at x for each value of the parameters provided
            by point.
        """
        return gs.from_numpy(
            binom.pmf(x, self.space.n_draws, point),
        )
