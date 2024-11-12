from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from lxml import etree
import sys
from io import StringIO


def get_linked_objects(filepath):

    prs = Presentation(filepath)
    linked_objects = []

    for slide in prs.slides:
        for shape_id, shape in enumerate(slide.shapes):
            # print(prs.slides.index(slide) + 1, shape_id)
            # if prs.slides.index(slide) + 1 != 6:
            #    continue
            if shape.shape_type in [
                MSO_SHAPE_TYPE.LINKED_OLE_OBJECT,
                MSO_SHAPE_TYPE.EMBEDDED_OLE_OBJECT,
            ]:
                ole = shape.ole_format
                blob = ole.blob
                for i in dir(ole):
                    print(i, getattr(ole, i))
                slide_number = prs.slides.index(slide) + 1
                shape_id = shape.shape_id
                filename = f"slide_{slide_number}_id_{shape_id}.pzf"
                f = open(filename, "wb")
                f.write(blob)
                f.close()
    return linked_objects


if __name__ == "__main__":
    filepath = sys.argv[1]
    linked_objects = get_linked_objects(filepath)
