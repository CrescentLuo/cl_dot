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


def binwalk_scan(file_in, quiet=True):
    try:
        # Set a custom extraction directory relative to the input file's directory
        destination_path = pathlib.Path(file_in).parent / "extracted_files"
        destination_path.mkdir(exist_ok=True)
        print("Yes")
        results = binwalk.scan(
            file_in,
            signature=True,
            quiet=quiet,
            extract=True,
            directory=str(destination_path),
        )
        for module in results:
            for result in module.results:
                print(f"Offset {result.offset}: {result.description}")
                if result.file:
                    print(f"  Extracted to: {result.file.name}")
                print("---------------")
    except Exception as e:
        print(f"Error: {e}")


def extract_prism_files(filepath):
    prs = Presentation(filepath)
    input_file_directory = pathlib.Path(filepath).parent
    extracted_files = []

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.shape_type in [
                MSO_SHAPE_TYPE.LINKED_OLE_OBJECT,
                MSO_SHAPE_TYPE.EMBEDDED_OLE_OBJECT,
            ]:
                slide_number = prs.slides.index(slide) + 1
                shape_id = shape.shape_id
                ole = shape.ole_format
                print(slide_number, ole.prog_id, ole.show_as_icon)

                blob = ole.blob

                bytes_io = io.BytesIO(blob)

                is_zip = zipfile.is_zipfile(bytes_io)
                filename = f"slide_{slide_number}_id_{shape_id}.bin"
                filename = input_file_directory / filename
                # start_pos = blob.find(b"PK")
                # end_sequence = b"PK\x05\x06"
                # end_pos = blob.rfind(end_sequence)
                # blob = blob[start_pos : end_pos + 22]
                with open(filename, "wb") as f:
                    f.write(blob)
                print(filename)
                binwalk_scan(str(filename), quiet=False)
                extracted_files.append(str(filename))

    return extracted_files


class ExtractedBin:
    def __init__(self, file_path):
        self.file_path = pathlib.Path(file_path)
        self.sheets = list()
        self.tables = list()

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
                    "setName": sets_meta["title"]["string"],
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
            csv_table = pd.read_csv(table_file_path, header=None, names=header_row)
            csv_table.dropna(how="all", inplace=True)
            csv_table = (
                csv_table.rename_axis("LNP")
                .reset_index()
                .melt(id_vars="LNP", var_name="Tissue", value_name="value")
            )
            csv_table[["Tissue", "rep"]] = csv_table["Tissue"].str.split(
                pat="_", expand=True
            )
            self.tables.append(csv_table)


def plot_table(table, file_path=None):
    bar_chart = (
        alt.Chart(table)
        .mark_bar()
        .encode(
            x="Tissue:O",
            y=alt.Y("mean(value):Q", scale=alt.Scale(type="log")).title("Mean value"),
            color="Tissue:N",
        )
    )
    point_chart = (
        alt.Chart(table)
        .mark_circle()
        .encode(
            x="Tissue:O",
            y=alt.Y("value:Q", scale=alt.Scale(type="log")),
            color="Tissue:N",
        )
    )
    alt_chart = alt.layer(bar_chart, point_chart).facet(column="LNP:N")
    if file_path:
        alt_chart.save(file_path)
    return alt_chart


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_obj <file_path>")
        sys.exit(1)

    # file_path = sys.argv[1]
    # extract_prism_files(file_path)
    extracted_set = ExtractedBin(sys.argv[1])
    extracted_set.extract_table()
    print(extracted_set.tables[0])
    plot_table(extracted_set.tables[0], "./test.svg")
