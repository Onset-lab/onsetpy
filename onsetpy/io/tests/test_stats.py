import unittest
import numpy as np
from onsetpy.stats import calculate_z_scores


class TestZScoreFunctions(unittest.TestCase):
    def setUp(self):
        # Create sample matrices for testing
        self.mean_matrix = np.array([[1.0, 2.0], [2.0, 3.0]])
        self.std_matrix = np.array([[0.5, 1.0], [1.0, 0.5]])
        self.base_matrix1 = np.array([[2.0, 4.0], [4.0, 4.0]])
        self.base_matrix2 = np.array([[0.0, 0.0], [0.0, 2.0]])
        
        # Expected z-scores for the test cases
        self.expected_z1 = np.array([[2.0, 2.0], [2.0, 2.0]])
        self.expected_z2 = np.array([[-2.0, -2.0], [-2.0, -2.0]])

    def test_calculate_z_scores_single_matrix(self):
        result = calculate_z_scores(self.mean_matrix, self.std_matrix, [self.base_matrix1])
        np.testing.assert_array_almost_equal(result[0], self.expected_z1)

    def test_calculate_z_scores_multiple_matrices(self):
        result = calculate_z_scores(
            self.mean_matrix,
            self.std_matrix,
            [self.base_matrix1, self.base_matrix2]
        )
        np.testing.assert_array_almost_equal(result[0], self.expected_z1)
        np.testing.assert_array_almost_equal(result[1], self.expected_z2)

    def test_incompatible_shapes(self):
        wrong_shape_matrix = np.array([[1.0]])
        with self.assertRaises(ValueError):
            calculate_z_scores(
                self.mean_matrix,
                self.std_matrix,
                [wrong_shape_matrix]
            )

    def test_zero_std(self):
        zero_std = np.zeros_like(self.std_matrix)
        with self.assertRaises(ValueError):
            calculate_z_scores(
                self.mean_matrix,
                zero_std,
                [self.base_matrix1]
            )

    def test_wrong_type_input(self):
        wrong_type = [[1, 2], [3, 4]]  # List instead of numpy array
        with self.assertRaises(TypeError):
            calculate_z_scores(
                self.mean_matrix,
                self.std_matrix,
                [wrong_type]
            )


if __name__ == "__main__":
    unittest.main()
