import os
import tempfile
from unittest import TestCase
from unittest.mock import patch, MagicMock
from onsetpy.reporting.report import Report, SurgeryflowReport


class TestReport(TestCase):
    def setUp(self):
        self.patient_name = "John Doe"
        self.patient_id = "12345"
        self.date = "2023-01-01"
        self.report = Report(self.patient_name, self.patient_id, self.date)

    def test_report_initialization(self):
        self.assertEqual(self.report.patient_name, self.patient_name)
        self.assertEqual(self.report.patient_id, self.patient_id)
        self.assertEqual(self.report.date, self.date)
        self.assertIsNone(self.report.html_content)
        self.assertTrue(os.path.exists(self.report.temp_dir))

    @patch("onsetpy.reporting.report.HTML.write_pdf")
    @patch("shutil.rmtree")
    def test_to_pdf(self, mock_rmtree, mock_write_pdf):
        self.report.html_content = "<html><body>Test</body></html>"
        output_path = os.path.join(tempfile.gettempdir(), "test_report.pdf")
        self.report.to_pdf(output_path)

        mock_write_pdf.assert_called_once_with(output_path)
        mock_rmtree.assert_called_once_with(self.report.temp_dir)


class TestSurgeryflowReport(TestCase):
    def setUp(self):
        self.patient_name = "Jane Doe"
        self.patient_id = "67890"
        self.date = "2023-01-02"
        self.surgery_report = SurgeryflowReport(
            self.patient_name, self.patient_id, self.date
        )

    @patch("onsetpy.reporting.report.Environment.get_template")
    def test_render(self, mock_get_template):
        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        missing_bundles = ["Bundle A", "Bundle B"]
        screenshot_path = "/path/to/screenshot.png"
        self.surgery_report.render(missing_bundles, screenshot_path)

        mock_get_template.assert_called_once_with("surgeryflow_report.html")
        mock_template.render.assert_called_once_with(
            {
                "patient_name": self.patient_name,
                "patient_id": self.patient_id,
                "date": self.date,
                "screenshot": screenshot_path,
                "missing_bundles": missing_bundles,
            }
        )
        self.assertIsNotNone(self.surgery_report.html_content)
