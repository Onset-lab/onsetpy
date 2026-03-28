import pytest
from unittest.mock import patch
from argparse import ArgumentParser, Namespace

import numpy as np

from onsetpy.io.utils import (
    add_verbose_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_overwrite_arg,
    assert_matrices_compatible,
    add_version_arg,
    __version__,
)


@pytest.fixture
def parser():
    return ArgumentParser()


# Test Add Verbose Arg
def test_default_verbose_level(parser):
    add_verbose_arg(parser)
    args = parser.parse_args([])
    assert args.verbose == "WARNING"


def test_verbose_level_info(parser):
    add_verbose_arg(parser)
    args = parser.parse_args(["-v"])
    assert args.verbose == "INFO"


def test_verbose_level_debug(parser):
    add_verbose_arg(parser)
    args = parser.parse_args(["-v", "DEBUG"])
    assert args.verbose == "DEBUG"

    @patch("os.path.isdir", return_value=True)
    def test_output_directory_exists_without_overwrite(self, mock_isdir):
        with self.assertRaises(SystemExit):
            assert_outputs_exist(
                self.parser, self.args, "output_dir/", output_is_dir=True
            )

    @patch("os.path.isdir", return_value=True)
    def test_output_directory_exists_with_overwrite(self, mock_isdir):
        self.args.overwrite = True
        assert_outputs_exist(self.parser, self.args, "output_dir/", output_is_dir=True)
        # No exception should be raised

    @patch("os.path.isfile", return_value=True)
    def test_required_file_exists_with_overwrite(self, mock_isfile):
        self.args.overwrite = True
        assert_outputs_exist(self.parser, self.args, "file1.txt")
        # No exception should be raised

    @patch("os.path.isfile", side_effect=[True, False])
    def test_mixed_files_exist_with_overwrite(self, mock_isfile):
        self.args.overwrite = True
        assert_outputs_exist(self.parser, self.args, ["file1.txt"], ["file2.txt"])
        # No exception should be raised


def test_verbose_level_warning(parser):
    add_verbose_arg(parser)
    args = parser.parse_args(["-v", "WARNING"])
    assert args.verbose == "WARNING"


def test_invalid_verbose_level(parser):
    add_verbose_arg(parser)
    with pytest.raises(SystemExit):
        parser.parse_args(["-v", "INVALID"])


# Test Assert Inputs Exist
@patch("os.path.isfile", return_value=True)
def test_all_files_exist(mock_isfile, parser):
    assert_inputs_exist(parser, ["file1.txt", "file2.txt"])


@patch("os.path.isfile", return_value=False)
def test_required_file_does_not_exist(mock_isfile, parser):
    with pytest.raises(SystemExit):
        assert_inputs_exist(parser, ["file1.txt"])


@patch("os.path.isfile", side_effect=[True, False])
def test_optional_file_does_not_exist(mock_isfile, parser):
    with pytest.raises(SystemExit):
        assert_inputs_exist(parser, ["file1.txt"], ["file2.txt"])


@patch("os.path.isfile", side_effect=[True, True])
def test_optional_file_exists(mock_isfile, parser):
    assert_inputs_exist(parser, "file1.txt", "file2.txt")


@patch("os.path.isfile", side_effect=[True, True, False])
def test_mixed_files_exist(mock_isfile, parser):
    with pytest.raises(SystemExit):
        assert_inputs_exist(parser, ["file1.txt"], ["file2.txt", "file3.txt"])


# Test Add Overwrite Arg
def test_default_overwrite(parser):
    add_overwrite_arg(parser)
    args = parser.parse_args([])
    assert not args.overwrite


def test_overwrite_flag(parser):
    add_overwrite_arg(parser)
    args = parser.parse_args(["-f"])
    assert args.overwrite


def test_help_message_without_delete_dirs(parser):
    add_overwrite_arg(parser)
    help_message = parser.format_help()
    assert "Force overwriting of the output files." in help_message
    assert "CAREFUL." not in help_message


def test_help_message_with_delete_dirs(parser):
    add_overwrite_arg(parser, will_delete_dirs=True)
    help_message = parser.format_help()
    assert "Force overwriting of the output files." in help_message
    assert "CAREFUL." in help_message


# Test Assert Outputs Exist
@pytest.fixture
def args():
    return Namespace(overwrite=False)


@patch("os.path.isfile", return_value=False)
@patch("os.path.isdir", return_value=True)
def test_all_files_do_not_exist(mock_isdir, mock_isfile, parser, args):
    assert_outputs_exist(parser, args, ["dir1/", "file2.txt"])


@patch("os.path.isfile", return_value=True)
def test_required_file_exists_without_overwrite(mock_isfile, parser, args):
    with pytest.raises(SystemExit):
        assert_outputs_exist(parser, args, "file1.txt")


@patch("os.path.isfile", side_effect=[False, True])
def test_optional_file_exists_without_overwrite(mock_isfile, parser, args):
    with pytest.raises(SystemExit):
        assert_outputs_exist(parser, args, "file1.txt", "file2.txt")


@patch("os.path.isfile", side_effect=[False, False])
@patch("os.path.isdir", return_value=True)
def test_optional_file_does_not_exist(mock_isdir, mock_isfile, parser, args):
    assert_outputs_exist(parser, args, ["file1.txt"], ["file2.txt"])


@patch("os.path.isfile", side_effect=[False, False])
@patch("os.path.isdir", return_value=False)
def test_directory_does_not_exist_with_check_dir_exists_false(
    mock_isdir, mock_isfile, parser, args
):
    assert_outputs_exist(
        parser,
        args,
        ["file1.txt"],
        ["file2.txt"],
        check_dir_exists=False,
    )


# Test Assert Matrices Compatible
def test_matrices_same_shape(parser):
    matrices = [np.ones((2, 2)), np.ones((2, 2))]
    assert_matrices_compatible(parser, matrices)


def test_matrices_different_shape(parser):
    matrices = [np.ones((2, 2)), np.ones((3, 3))]
    with pytest.raises(SystemExit):
        assert_matrices_compatible(parser, matrices)


def test_single_matrix(parser):
    matrices = [np.ones((2, 2))]
    assert_matrices_compatible(parser, matrices)


def test_empty_matrices_list(parser):
    matrices = []
    with pytest.raises(IndexError):
        assert_matrices_compatible(parser, matrices)


def test_version_arg(parser, capsys):
    add_version_arg(parser)
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--version"])
    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert __version__ == captured.out.strip()
