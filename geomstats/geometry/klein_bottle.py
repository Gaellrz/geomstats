"""
The Klein Bottle manifold.

Lead author: Juliane Braunsmann
"""

import geomstats.backend as gs
from geomstats.geometry.manifold import Manifold
from geomstats.geometry.riemannian_metric import RiemannianMetric


class KleinBottleMetric(RiemannianMetric):
    """Class for the Klein Bottle Metric.

    Implements exp and log using explicit formulas.

    Parameters
    ----------
    space : KleinBottle
        Underlying manifold.
    """

    def __init__(self, space, **kwargs):
        super().__init__(dim=2, shape=(2,), default_coords_type="intrinsic")
        self._space: KleinBottle = space

    def injectivity_radius(self, base_point):
        """Compute the radius of the injectivity domain.

        This is is the supremum of radii r for which the exponential map is a
        diffeomorphism from the open ball of radius r centered at the base
        point onto its image.

        Parameters
        ----------
        base_point : array-like, shape=[..., 2]
            Point on the manifold. Unused.

        Returns
        -------
        radius : float
            Injectivity radius.
        """
        return 1 / 2

    def inner_product(self, tangent_vec_a, tangent_vec_b, base_point=None):
        """Inner product between two tangent vectors at a base point.

        Parameters
        ----------
        tangent_vec_a: array-like, shape=[..., 2]
            Tangent vector at base point.
        tangent_vec_b: array-like, shape=[..., 2]
            Tangent vector at base point.
        base_point: array-like, shape=[..., 2]
            Base point.
            Optional, default: None, unused.

        Returns
        -------
        inner_product : array-like, shape=[...,]
            Inner-product.
        """
        return gs.dot(tangent_vec_a, tangent_vec_b)

    def exp(self, tangent_vec, base_point, **kwargs):
        """Exponential map.

        Computed by adding tangent_vec to base_point and finding canonical
        representation in the unit square.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., 2]
            Tangent vector at the base point.
        base_point : array-like, shape=[..., 2]
            Point on the manifold.

        Returns
        -------
        exp : array-like, shape=[..., dim]
            Point on the manifold.
        """
        if base_point.ndim == 1 and tangent_vec.ndim > 1:
            while base_point.ndim < tangent_vec.ndim:
                base_point = gs.expand_dims(base_point, 0)
        base_point_canonical = self._space.regularize(base_point)
        point = base_point_canonical + tangent_vec
        point_canonical = self._space.regularize(point)
        return point_canonical

    def log(self, point, base_point, **kwargs):
        """Logarithm map.

        Computed by finding the representative of point closest to base_point and
        returning their difference.

        Parameters
        ----------
        point : array-like, shape=[..., 2]
            Point on the manifold.
        base_point : array-like, shape=[..., 2]
            Point on the manifold.

        Returns
        -------
        tangent_vec : array-like, shape=[..., dim]
            Tangent vector at the base point.
        """
        if base_point.ndim == 1 and point.ndim > 1:
            while base_point.ndim < point.ndim:
                base_point = gs.expand_dims(base_point, 0)
        base_point_canonical, point_minimal = self._closest_representative(
            base_point, point
        )
        return point_minimal - base_point_canonical

    def _closest_representative(self, point1, point2):
        """Find the representative of point2 which is closest to point1.

        Only representatives in the 8 surrounding
        squares have to be considered.

        Parameters
        ----------
        point1: array-like, shape [..., 2]
            Point on the manifold.
        point2: array-like, shape [..., 2]
            Point on the manifold.

        Returns
        -------
        point1: array-like, shape [...,2]
            Canonical representation of point1 in unit square.
        minimizers: array-like, shape [...,2]
            Representation of point2 with smallest distance to point1.
        """
        point1, point2 = gs.broadcast_arrays(point1, point2)
        shape = point1.shape
        p1 = self._space.regularize(point1)
        p1 = gs.reshape(p1, (-1, 2))
        p2 = self._space.regularize(point2)
        p2 = gs.reshape(p2, (-1, 2))
        p2_2 = gs.stack([p2[:, 0], p2[:, 1] - 1], axis=-1)
        p2_3 = gs.stack([p2[:, 0], p2[:, 1] + 1], axis=-1)
        p2_4 = gs.stack([p2[:, 0] + 1, 1 - p2[:, 1]], axis=-1)
        p2_5 = gs.stack([p2[:, 0] + 1, 2 - p2[:, 1]], axis=-1)
        p2_6 = gs.stack([p2[:, 0] + 1, 0 - p2[:, 1]], axis=-1)
        p2_7 = gs.stack([p2[:, 0] - 1, 1 - p2[:, 1]], axis=-1)
        p2_8 = gs.stack([p2[:, 0] - 1, 2 - p2[:, 1]], axis=-1)
        p2_9 = gs.stack([p2[:, 0] - 1, 0 - p2[:, 1]], axis=-1)
        p2_total = gs.stack(
            [p2, p2_2, p2_3, p2_4, p2_5, p2_6, p2_7, p2_8, p2_9], axis=0
        )
        indices = gs.argmin(
            gs.sum((p2_total - gs.expand_dims(p1, 0)) ** 2, axis=-1), axis=0
        )
        minimizers = gs.empty_like(p1)
        for i in range(len(indices)):
            minimizers[i, :] = p2_total[indices[i], i, :]
        p1 = gs.reshape(p1, shape)
        minimizers = gs.reshape(minimizers, shape)
        return p1, minimizers


class KleinBottle(Manifold):
    r"""Class for the Klein Bottle, a two dimensional manifold which is not orientable.

    Points are understood to be on the Klein Bottle if they are in the interval
    :math:`[0,1]^2`.
    Each point in :math:`\mathbb R^2` can be understood as a point on the Klein Bottle
    by considering the equivalence relation

    .. math::
       :nowrap:

       \begin{align}
         &  (x_1,y_1) \sim (x_2, y_2) \\
         \Leftrightarrow \quad &  y_1-y_2 \in \mathbb Z
                                 \text{ and } x_1-x_2 \in 2\mathbb Z \\
         \text{ or } \quad &
        y_1 + y_2 \in \mathbb Z \text{ and } x_1-x_2 \in \mathbb Z\setminus 2\mathbb Z.
       \end{align}
    """

    def __init__(self, dim=2, shape=2):
        super().__init__(dim=2, shape=(2,), metric=None)
        self.metric = None

    def equip_metric(self, metric=None):
        """Equip the manifold with the specified metric.

        Parameters
        ----------
        metric: Metric
            A metric compatible with the Klein Bottle.
        """
        self.metric = KleinBottleMetric(self)

    def random_point(self, n_samples=1, bound=None):
        """Uniformly sample points on the manifold.

        Parameters
        ----------
        n_samples : int
            Number of samples.
            Optional, default: 1.
        bound : unused

        Returns
        -------
        samples : array-like, shape=[n_samples, 2]
            Points sampled on the manifold.
        """
        samples = gs.random.uniform(size=(n_samples, 2))
        if n_samples == 1:
            samples = gs.squeeze(samples, axis=0)
        return samples

    def to_tangent(self, vector, base_point=None):
        """Project a vector to a tangent space of the manifold.

        In this case returns the vector itself.

        Parameters
        ----------
        vector : array-like, shape=[..., dim]
            Vector.
        base_point : unused

        Returns
        -------
        tangent_vec : array-like, shape=[..., dim]
            Tangent vector at base point.
        """
        if gs.all(self.is_tangent(vector)):
            return vector
        raise ValueError("Vector has the wrong shape.")

    def is_tangent(self, vector, base_point=None, atol=gs.atol):
        r"""Evaluate if the point belongs to :math:`\mathbb R^2`.

        This method checks the shape and of the input point.

        Parameters
        ----------
        vector : array-like, shape=[...]
            Point to test.
        base_point: unused here
        atol : float
            Unused here.

        Returns
        -------
        belongs : array-like, shape=[...,]
            Boolean evaluating if point belongs to the tangent space.
        """
        # copied from VectorSpace
        vector = gs.array(vector)
        minimal_ndim = len(self.shape)
        if self.shape[0] == 1 and len(vector.shape) <= 1:
            vector = gs.transpose(gs.to_ndarray(gs.to_ndarray(vector, 1), 2))
        belongs = vector.shape[-minimal_ndim:] == self.shape
        if vector.ndim <= minimal_ndim:
            return belongs
        return gs.tile(gs.array([belongs]), [vector.shape[0]])

    def belongs(self, point, atol=gs.atol):
        """Evaluate if the point belongs to the set [0,1]^2.

        This method checks the shape and values of the input point.

        Parameters
        ----------
        point : array-like, shape=[...]
            Point to test.
        atol : float
            Unused here.

        Returns
        -------
        belongs : array-like, shape=[...,]
            Boolean evaluating if point belongs to the space.
        """
        point = gs.array(point)
        minimal_ndim = len(self.shape)
        correct_shape = point.shape[-minimal_ndim:] == self.shape
        if correct_shape:
            correct_values = gs.all(gs.logical_and(point >= 0, point <= 1), axis=-1)
            return correct_values
        if point.ndim > minimal_ndim:
            return gs.tile(gs.array([correct_shape]), [point.shape[0]])

    @staticmethod
    def equivalent(point1, point2, atol=gs.atol):
        r"""Evaluate whether two points represent equivalent points on the Klein Bottle.

        This method uses the equivalence stated in the class description.

        This means points are equivalent if one walks an even number of squares in
        x-direction and any number of squares in y-direction or an uneven number of
        squares in x-direction and any number of squares in y-direction while
        "mirroring" the y coordinate.

        Parameters
        ----------
        point1: array-like, shape=[..., 2]
            Representation of point on Klein Bottle
        point2: array-like, shape=[..., 2]
            Representation of point on Klein Bottle
        atol: Absolute tolerance to test for belonging to \mathbb Z.

        Returns
        -------
        is_equivalent : array-like, shape=[..., 2]
            Boolean evaluating if points are equivalent
        """
        x_diff = point1[..., 0] - point2[..., 0]
        y_diff = point1[..., 1] - point2[..., 1]
        y_sum = point1[..., 1] + point2[..., 1]
        un_mirrored = gs.logical_and(
            is_close_mod(gs.mod(x_diff, 2.0), 2.0, atol=atol),
            is_close_mod(gs.mod(y_diff, 1.0), 1.0, atol=atol),
        )
        mirrored = gs.logical_and(
            is_close_mod(gs.mod(x_diff - 1, 2.0), 2.0, atol=atol),
            is_close_mod(gs.mod(y_sum, 1.0), 1.0, atol=atol),
        )
        return gs.logical_or(un_mirrored, mirrored)

    def regularize(self, point):
        r"""Regularize arbitrary point to canonical equivalent in unit square.

        Regularize any point in :math:`\mathbb R^2` to its canonical equivalent
        representation in the square :math:`[0,1]^2`.

        Parameters
        ----------
        point : array-like, shape=[..., 2]
            Point.

        Returns
        -------
        regularized_point : array-like, shape=[..., 2]
            Regularized point.
        """
        # determine number of steps to take in x direction
        num_steps = gs.cast(gs.abs(gs.floor(point[..., [0]])), gs.int64)
        x_canonical = gs.remainder(point[..., 0], 1)
        y_canonical_even = gs.remainder(point[..., 1], 1)
        y_canonical_odd = gs.remainder(1 - y_canonical_even, 1)
        point_even = gs.stack([x_canonical, y_canonical_even], axis=-1)
        point_odd = gs.stack([x_canonical, y_canonical_odd], axis=-1)
        return gs.where(gs.remainder(num_steps, 2) == 0, point_even, point_odd)


def is_close_mod(array, divisor, atol):
    """Determine if values in array are elementwise close to zero modulo divisor.

    Evaluate elementwise to true if the absolute value is close to 0 or divisor.

    Parameters
    ----------
    array: array-like, shape [...]
        Array who values will be considered.
    divisor: int
        Divisor in the modulo operation.
    atol: float
        Absolute tolerance threshold.

    Return
    ------
    is_close_mod_bool: boolean array-like, shape [...]
        Elementwise result.
    """
    return gs.logical_or(
        gs.isclose(gs.abs(array), 0.0, atol), gs.isclose(gs.abs(array), divisor, atol)
    )
