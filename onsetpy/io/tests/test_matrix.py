import unittest
import numpy as np
import os
from onsetpy.io.matrix import load_matrix, save_matrix


class TestMatrixFunctions(unittest.TestCase):

    def setUp(self):
        # Create temporary files for testing
        self.test_matrix = np.array([[1, 2], [3, 4]])
        self.single_file = "test_single.npy"
        self.multiple_files = ["test1.npy", "test2.npy"]

        np.save(self.single_file, self.test_matrix)
        for file in self.multiple_files:
            np.save(file, self.test_matrix)

    def tearDown(self):
        # Remove temporary files after testing
        os.remove(self.single_file)
        for file in self.multiple_files:
            os.remove(file)

    def test_load_single_matrix(self):
        loaded_matrix = load_matrix(self.single_file)
        np.testing.assert_array_equal(loaded_matrix, self.test_matrix)

    def test_load_multiple_matrices(self):
        loaded_matrices = load_matrix(self.multiple_files)
        for loaded_matrix in loaded_matrices:
            np.testing.assert_array_equal(loaded_matrix, self.test_matrix)

    def test_save_matrix(self):
        output_file = "test_output.npy"
        save_matrix(self.test_matrix, output_file)
        loaded_matrix = np.load(output_file)
        np.testing.assert_array_equal(loaded_matrix, self.test_matrix)
        os.remove(output_file)


if __name__ == "__main__":
    unittest.main()
