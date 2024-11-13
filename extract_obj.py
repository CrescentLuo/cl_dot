import sys
import io
import pathlib
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx import Presentation
import zipfile


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
                ole = shape.ole_format
                blob = ole.blob
                bytes_io = io.BytesIO(blob)
                slide_number = prs.slides.index(slide) + 1
                shape_id = shape.shape_id

                is_zip = zipfile.is_zipfile(bytes_io)

                if is_zip:
                    filename = f"slide_{slide_number}_id_{shape_id}.pzf"
                    filename = input_file_directory / filename
                else:
                    filename = f"slide_{slide_number}_id_{shape_id}.prism"
                    filename = input_file_directory / filename
                    start_pos = blob.find(b"PK")
                    end_sequence = b"PK"
                    end_pos = blob.rfind(end_sequence)
                    blob = blob[start_pos : end_pos + 22]

                with open(filename, "wb") as f:
                    f.write(blob)
                extracted_files.append(str(filename))

    return extracted_files


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_obj <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    extract_prism_files(file_path)
