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
        Renders the SurgeryFlow report using the provided missing bundles list and screenshot path.

        Args:
            missing_bundles (dict): List of missing bundles to be included in the report.
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


class EpinsightReport(Report):
    def __init__(self, patient_name, patient_id, date):
        super().__init__(patient_name, patient_id, date)

    def render(
        self,
        asymmetry_index,
        asymmetry_figure,
        map18_figures,
        brain_screenshot,
    ):
        """
        Renders the Epinsight report using the provided asymmetry index data and screenshot path.

        Args:
            asymmetry_index (dict): The asymmetry index data to be included in the report.
            asymmetry_figure (str): The file path to the asymmetryfigure.
            map18_figures (list): List of file paths to the map18 figures.
            brain_screenshot (str): The file path to the brain screenshot image.

        Returns:
            None
        """
        template = self.env.get_template("epinsight_report.html")
        data = {
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "date": self.date,
            "asymmetry_figure": asymmetry_figure,
            "asymmetry_index": asymmetry_index,
            "map18_figures": map18_figures,
            "brain_screenshot": brain_screenshot,
        }
        self.html_content = template.render(data)
