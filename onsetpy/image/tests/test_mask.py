import unittest
import numpy as np
from onsetpy.image.mask import create_sphere_mask


class TestCreateSphereMask(unittest.TestCase):
    def test_create_sphere_mask_center(self):
        shape = (10, 10, 10)
        center = (5, 5, 5)
        radius = 2
        mask = create_sphere_mask(shape, center, radius)

        self.assertEqual(mask[5, 5, 5], 1)
        self.assertEqual(mask.sum(), 25)  # Volume of a sphere with radius 2

    def test_create_sphere_mask_edge(self):
        shape = (10, 10, 10)
        center = (1, 1, 1)
        radius = 2
        mask = create_sphere_mask(shape, center, radius)

        self.assertEqual(mask[2, 2, 2], 1)
        self.assertEqual(mask.sum(), 25)  # Volume of a sphere with radius 2

    def test_create_sphere_mask_out_of_bounds(self):
        shape = (10, 10, 10)
        center = (15, 15, 15)
        radius = 2
        mask = create_sphere_mask(shape, center, radius)

        self.assertEqual(
            mask.sum(), 25
        )  # Center is out of bounds, no mask should be created

    def test_create_sphere_mask_large_radius(self):
        shape = (10, 10, 10)
        center = (5, 5, 5)
        radius = 5
        mask = create_sphere_mask(shape, center, radius)

        self.assertEqual(mask[5, 5, 5], 1)
        self.assertGreater(mask.sum(), 0)  # Ensure some mask is created


if __name__ == "__main__":
    unittest.main()
