import sys
import io
import pathlib
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx import Presentation
import zipfile
import binwalk
import json


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


def extract_data(file_path):
    data_folder = pathlib.Path(file_path) / "data"
    sheets = data_folder / "sheets"
    sheet_meta = {}
    for sub_dir in sheets.iterdir():
        sheet_json = sub_dir / "sheet.json"
        if sheet_json.exists():
            with open(sheet_json) as json_file:
                sheet_meta[sub_dir.name] = json.load(json_file)

    return sheet_meta


def extact_table_dataSets(file_path, uid):
    sets_folder = file_path / "data" / "sets"
    sets_json_path = sets_folder / "{}".format(uid)
    with open(sets_json_path) as json_file:
        sets_meta = json.load(json_file)
        return 


def extract_table(file_path, meta):
    sheet_id = meta["$id"]
    sheet_uid = meta["uid"]
    table = meta["table"]
    table_uid = meta["table"]["uid"]
    dataSets = meta["table"]["dataSets"]
    repCnt = meta["table"]["replicatesCount"]
    header_row = []
    for set_uid in dataSets:
        


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_obj <file_path>")
        sys.exit(1)

    # file_path = sys.argv[1]
    # extract_prism_files(file_path)
    meta = extract_data(sys.argv[1])
    print(meta)
