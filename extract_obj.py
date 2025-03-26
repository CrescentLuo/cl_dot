import sys
import io
import pathlib
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx import Presentation
import zipfile
import binwalk
import json
import pandas as pd
import altair as alt
import logging
import re
import argparse
import olefile
import requests


def process_text(text):
    """Process experimental text data using an API call.

    Args:
        text (str): Raw experimental text to process

    Returns:
        dict: Parsed response from the API with extracted information
    """
    # Load API token from the JSON file
    try:
        with open(pathlib.Path(__file__).parent / "dify_api_token.json") as f:
            token_data = json.load(f)
            api_token = token_data.get("api_token")
            if not api_token:
                logging.error("API token not found in token file")
                return None
    except Exception as e:
        logging.error(f"Failed to load API token: {e}")
        return None

    api_url = "http://10.10.1.29/v1/chat-messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": {},
        "query": text,
        "response_mode": "blocking",
        "user": "zheng.luo",
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        # Extract information from the answer
        extracted_info = {}
        if "answer" in response_data:
            # Split the answer by <br/> or newlines
            answer_lines = re.split(r"<br/>|\n", response_data["answer"])

            # Process each line to extract key-value pairs
            for line in answer_lines:
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    extracted_info[key.strip()] = value.strip()

            # Add the extracted info to the response
            response_data["extracted_info"] = extracted_info
        print(response_data["extracted_info"])
        return response_data
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None


def binwalk_scan(file_in, quiet=True):
    try:
        # Set a custom extraction directory relative to the input file's directory
        destination_path = (
            pathlib.Path(file_in).parent / f"{pathlib.Path(file_in).stem}"
        )
        destination_path.mkdir(exist_ok=False)
        print(f"Extracting {file_in}")
        results = binwalk.scan(
            file_in,
            signature=True,
            # exclude=["misc"],
            quiet=quiet,
            extract=True,
            directory=str(destination_path),
        )
        for module in results:
            for result in module.results:
                # print(f"Offset {result.offset}: {result.description}")
                if result.file:
                    logging.info(f"  Extracted to: {result.file.name}")
                # print("---------------")
    except Exception as e:
        print(f"Error: {e}")


def extract_prism_files(filepath, single_slide=None):
    prs = Presentation(filepath)
    input_file_directory = pathlib.Path(filepath).parent
    extracted_files = []

    for slide in prs.slides:
        slide_number = prs.slides.index(slide) + 1
        if single_slide:
            if slide_number != single_slide:
                continue
        print(
            f"Slide {slide_number} shape types:",
            [shape.shape_type for shape in slide.shapes],
        )
        # Extract text from all text shapes on the slide
        slide_text = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    slide_text.append(paragraph.text)
        if slide_text:
            print(f"Slide {slide_number} text elements:", slide_text)
            process_text("\t".join(slide_text))
        for shape in slide.shapes:
            if shape.shape_type in [
                MSO_SHAPE_TYPE.LINKED_OLE_OBJECT,
                MSO_SHAPE_TYPE.EMBEDDED_OLE_OBJECT,
            ]:

                shape_id = shape.shape_id
                ole = shape.ole_format
                print(slide_number, ole.prog_id, ole.show_as_icon)

                blob = ole.blob

                bytes_io = io.BytesIO(blob)

                is_zip = zipfile.is_zipfile(bytes_io)
                if is_zip:
                    with olefile.OleFileIO(bytes_io) as ole_stream:
                        # Check for the stream name - often it's named "CONTENTS" or similar.
                        stream_name = "CONTENTS"  # Change as needed if the stream name is different
                        if ole_stream.exists(stream_name):
                            blob = ole_stream.openstream(stream_name).read()
                        else:
                            print(
                                f"Stream '{stream_name}' not found in the OLE object."
                            )

                filename = f"slide_{slide_number}_id_{shape_id}.bin"
                filename = input_file_directory / filename
                with open(filename, "wb") as f:
                    f.write(blob)
                print(filename)
                binwalk_scan(str(filename), quiet=True)
                extracted_files.append(str(filename))

    return extracted_files


class ExtractedBin:
    def __init__(self, file_path):
        self.file_path = pathlib.Path(file_path)

        self.sheets = list()
        self.tables = list()
        self.extract_name()

    def extract_name(self):
        # Extract slide number and shape ID from filename like "slide_2_id_5.bin"
        match = re.search(r"slide_(\d+)_id_(\d+)\.bin", str(self.file_path.name))
        if match:
            self.slide_number = match.group(1)
            self.shape_id = match.group(2)
        else:
            self.slide_number = "unknown"
            self.shape_id = "unknown"
        self.file_path = (
            self.file_path.parent
            / f"{self.file_path.stem}"
            / f"_slide_{self.slide_number}_id_{self.shape_id}.bin.extracted"
        )
        # print(f"processing {self.slide_number}, {self.shape_id}")

    def extract_sheets(self):
        data_folder = pathlib.Path(self.file_path) / "data"
        sheets = data_folder / "sheets"
        for sub_dir in sheets.iterdir():
            sheet_json = sub_dir / "sheet.json"
            if sheet_json.exists():
                with open(sheet_json) as json_file:
                    self.sheets.append(json.load(json_file))

    def extact_table_dataSets(self, uid):
        sets_folder = self.file_path / "data" / "sets"
        sets_json_path = sets_folder / "{}.json".format(uid)
        with open(sets_json_path) as json_file:
            sets_meta = json.load(json_file)
            return {
                uid: {
                    "fenID": sets_meta["fenID"],
                    "setName": (
                        sets_meta["title"]["string"]
                        if isinstance(sets_meta["title"], dict)
                        else sets_meta["title"]
                    ),
                }
            }

    def extract_table(self):
        if not self.sheets:
            self.extract_sheets()
        for sheet_meta in self.sheets:
            sheet_id = sheet_meta["$id"]
            sheet_uid = sheet_meta["uid"]
            table = sheet_meta["table"]
            table_uid = sheet_meta["table"]["uid"]
            dataSets = sheet_meta["table"]["dataSets"]
            repCnt = sheet_meta["table"]["replicatesCount"]
            header_row = []
            for set_uid in dataSets:
                set_meta = self.extact_table_dataSets(set_uid)
                for i in range(repCnt):
                    header_row.append(set_meta[set_uid]["setName"] + f"_rep{i}")
            table_file_path = (
                self.file_path / "data" / "tables" / table_uid / "data.csv"
            )
            csv_table = pd.read_csv(
                table_file_path,
                header=None,
                index_col=0,
                names=["LNP"] + header_row,
                usecols=range(len(header_row) + 1),
            )
            csv_table = csv_table.reset_index().melt(
                id_vars="LNP", var_name="Tissue", value_name="value"
            )
            csv_table[["Tissue", "rep"]] = csv_table["Tissue"].str.split(
                pat="_", expand=True
            )
            self.tables.append(csv_table)

    def save_tables(self):
        for idx, sheet_meta in enumerate(self.sheets):
            self.tables[idx].to_csv(
                f"{self.file_path.parent}/Page_{self.slide_number}_Shape_{self.shape_id}_{idx}.csv"
            )
        bar_plot = self.plot_table(self.tables[idx])
        bar_plot.save(
            f"{self.file_path.parent}/Page_{self.slide_number}_Shape_{self.shape_id}_{idx}.svg"
        )

    def plot_table(self, table):
        bar_chart = (
            alt.Chart(table)
            .mark_bar()
            .encode(
                x="LNP:O",
                xOffset="Tissue:N",
                y=alt.Y("mean(value):Q", scale=alt.Scale(type="log")).title(
                    "Mean value"
                ),
                color="Tissue:N",
            )
        )
        point_chart = (
            alt.Chart(table)
            .mark_circle()
            .encode(
                x="LNP:O",
                xOffset="Tissue:N",
                y=alt.Y("value:Q", scale=alt.Scale(type="log")),
                color=alt.value("black"),
            )
        )
        alt_chart = alt.layer(bar_chart, point_chart)
        return alt_chart


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_obj <file_path>")
        sys.exit(1)

    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Extract and process objects from PowerPoint files."
    )
    parser.add_argument(
        "-f", "--file_path", type=str, help="Path to the input file", required=True
    )
    parser.add_argument(
        "-s", "--slide_num", type=int, help="Specific slide number to process"
    )
    args = parser.parse_args()

    file_path = pathlib.Path(args.file_path)
    if file_path.suffix == ".pptx":
        if args.slide_num:
            bin_file_path = extract_prism_files(file_path, single_slide=args.slide_num)
        else:
            bin_file_path = extract_prism_files(file_path)

    # print(bin_file_path)
    for extracted_files_dir in bin_file_path:
        print(extracted_files_dir)
        extracted_set = ExtractedBin(extracted_files_dir)
        extracted_set.extract_table()
        extracted_set.save_tables()
    # print(extracted_set.tables[0])
    # plot_table(extracted_set.tables[0], "./test.svg")
