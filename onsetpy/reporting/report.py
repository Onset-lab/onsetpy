from os.path import abspath, dirname, join
import shutil
import tempfile


from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


class Report:
    def __init__(self, patient_name, patient_id, date):
        """
        Initializes the Report object with patient details and sets up the environment for template
        rendering.

        Args:
            patient_name (str): The name of the patient.
            patient_id (str): The unique identifier for the patient.
            date (str): The date associated with the report.

        Attributes:
            env (Environment): The Jinja2 environment for loading templates.
            patient_name (str): The name of the patient.
            patient_id (str): The unique identifier for the patient.
            date (str): The date associated with the report.
            html_content (str or None): The HTML content of the report, initially set to None.
            temp_dir (str): The path to a temporary directory for storing files.
        """
        self.env = Environment(
            loader=FileSystemLoader(abspath(join(dirname(__file__), "../templates")))
        )
        self.patient_name = patient_name
        self.patient_id = patient_id
        self.date = date
        self.html_content = None
        self.temp_dir = tempfile.mkdtemp()

    def render(self):
        """
        Render the report.

        This method is intended to be overridden by subclasses to provide
        specific rendering functionality.
        """
        pass

    def to_pdf(self, output_path):
        """
        Converts the HTML content to a PDF file and saves it to the specified output path.

        Args:
            output_path (str): The file path where the PDF will be saved.

        Raises:
            OSError: If there is an issue removing the temporary directory.
        """
        HTML(string=self.html_content).write_pdf(output_path)
        shutil.rmtree(self.temp_dir)


class SurgeryflowReport(Report):
    def __init__(self, patient_name, patient_id, date):
        super().__init__(patient_name, patient_id, date)

    def render(self, missing_bundles, screenshot_path):
        """
        Renders the stroke report using the provided volumetry data and screenshot path.

        Args:
            volumetry_data (dict): The volumetry data to be included in the report.
            screenshot_path (str): The file path to the screenshot image.

        Returns:
            None
        """
        template = self.env.get_template("surgeryflow_report.html")
        data = {
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "date": self.date,
            "screenshot": screenshot_path,
            "missing_bundles": missing_bundles,
        }
        self.html_content = template.render(data)
