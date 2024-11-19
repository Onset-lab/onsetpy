import unittest
from unittest.mock import patch, mock_open
from onsetpy.utils.gridview import parse_gridview_file, transform_gridview_coordinates


class TestGridviewUtils(unittest.TestCase):

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="Image cube size: 256\t256\t256\nImage cube resolution: 1.0\t1.0\t1.0\nGroup: A\nA1: 10\t20\t30\tannotation1\nA2: 40\t50\t60\tannotation2\nA3:              \n",
    )
    def test_parse_gridview_file(self, mock_file):
        expected_electrodes = {
            "A": [
                {
                    "name": "A1",
                    "coordinates": [10, 20, 30],
                    "annotation": "annotation1",
                },
                {
                    "name": "A2",
                    "coordinates": [40, 50, 60],
                    "annotation": "annotation2",
                },
            ]
        }
        expected_shape = [256, 256, 256]
        expected_voxel_size = [1.0, 1.0, 1.0]

        electrodes, shape, voxel_size = parse_gridview_file("dummy_path.txt")

        self.assertEqual(electrodes, expected_electrodes)
        self.assertEqual(shape, expected_shape)
        self.assertEqual(voxel_size, expected_voxel_size)

    def test_transform_gridview_coordinates(self):
        coords = [10, 20, 30]
        scaling_factors = [2.0, 2.0, 2.0]
        vox_factors = [1.0, 1.0, 1.0]
        ref_dims = [100, 100, 100]

        expected_transformed_coords = [79, 59, 61]

        transformed_coords = transform_gridview_coordinates(
            coords, scaling_factors, vox_factors, ref_dims
        )

        self.assertEqual(transformed_coords, expected_transformed_coords)


if __name__ == "__main__":
    unittest.main()
