import random

import geomstats.backend as gs
from geomstats.information_geometry.exponential import ExponentialDistributions
from tests.data_generation import _OpenSetTestData


class ExponentialTestData(_OpenSetTestData):
    space = ExponentialDistributions
    n_list = random.sample((2, 5), 1)
    n_samples_list = random.sample(range(10), 3)
    space_args_list = []
    shape_list = [(1,)]
    n_points_list = random.sample(range(5), 2)
    n_vecs_list = random.sample(range(2, 5), 1)

    def belongs_test_data(self):
        smoke_data = [
            dict(vec=0.1, expected=True),
            dict(vec=-0.8, expected=False),
            dict(vec=0.1, expected=True),
            dict(vec=-1.0, expected=False),
        ]
        return self.generate_tests(smoke_data)

    def random_point_test_data(self):
        random_data = [
            dict(point=self.space().random_point(3), expected=(3,)),
            dict(point=self.space().random_point(2), expected=(2,)),
            dict(point=self.space().random_point(1), expected=()),
        ]
        return self.generate_tests([], random_data)

    def random_point_belongs_test_data(self):
        smoke_space_args_list = []
        smoke_n_points_list = [1, 2, 5]
        return self._random_point_belongs_test_data(
            smoke_space_args_list,
            smoke_n_points_list,
            self.space_args_list,
            self.n_points_list,
        )

    def projection_belongs_test_data(self):
        return self._projection_belongs_test_data(
            self.space_args_list, self.shape_list, self.n_samples_list
        )

    def to_tangent_is_tangent_test_data(self):
        return self._to_tangent_is_tangent_test_data(
            self.space,
            self.space_args_list,
            self.shape_list,
            self.n_vecs_list,
        )

    def to_tangent_is_tangent_in_ambient_space_test_data(self):
        return self._to_tangent_is_tangent_in_ambient_space_test_data(
            self.space,
            self.space_args_list,
            self.shape_list,
        )

    def random_tangent_vec_is_tangent_test_data(self):
        return self._random_tangent_vec_is_tangent_test_data(
            self.space,
            self.space_args_list,
            self.n_vecs_list,
            is_tangent_atol=gs.atol,
        )

    def sample_test_data(self):
        smoke_data = [
            dict(point=gs.array([0.2, 0.3]), n_samples=2, expected=(2, 2)),
            dict(
                point=gs.array([0.1, 0.2, 0.3]),
                n_samples=1,
                expected=(3,),
            ),
        ]
        return self.generate_tests(smoke_data)

    def sample_belongs_test_data(self):
        random_data = [
            dict(
                point=self.space().random_point(3),
                n_samples=4,
                expected=gs.ones((3, 4)),
            ),
            dict(
                point=self.space().random_point(1),
                n_samples=2,
                expected=gs.ones(2),
            ),
            dict(
                point=self.space().random_point(2),
                n_samples=3,
                expected=gs.ones((2, 3)),
            ),
        ]
        return self.generate_tests([], random_data)

    def point_to_pdf_test_data(self):
        random_data = [
            dict(
                point=self.space().random_point(2),
                n_samples=3,
            ),
            dict(
                point=self.space().random_point(1),
                n_samples=4,
            ),
            dict(
                point=self.space().random_point(1),
                n_samples=1,
            ),
            dict(
                point=self.space().random_point(4),
                n_samples=1,
            ),
        ]
        return self.generate_tests([], random_data)

    def squared_dist_test_data(self):
        smoke_data = [
            dict(
                point_a=gs.array([1, 0.5, 10]),
                point_b=gs.array([2, 3.5, 70]),
                expected=gs.array([0.48045301, 3.78656631, 3.78656631]),
            ),
            dict(
                point_a=gs.array(0.1),
                point_b=gs.array(0.99),
                expected=gs.array(5.255715612697455),
            ),
        ]
        return self.generate_tests(smoke_data)
