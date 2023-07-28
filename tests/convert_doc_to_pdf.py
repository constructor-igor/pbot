# import os
# import win32com.client as win32

# #
# # doc2pdf
# #

# def convert_doc_to_pdf(doc_file_path, pdf_file_path):
#     word_app = win32.gencache.EnsureDispatch("Word.Application")
#     doc = word_app.Documents.Open(doc_file_path)
#     doc.SaveAs(pdf_file_path, FileFormat=17)  # FileFormat=17 specifies PDF format
#     doc.Close()
#     word_app.Quit()

# from docx2pdf import convert

# def doc_to_pdf(doc_path, pdf_path):
#     convert(doc_path, pdf_path)

import os
import subprocess

def doc_to_pdf(doc_path, pdf_path):
    soffice_path = os.path.join(r"C:\Program Files\LibreOffice\program", "soffice.exe")
    subprocess.run([soffice_path, "--headless", "--convert-to", "pdf", "--outdir", pdf_path, doc_path])

# Usage example
doc_file_path = ".\data\\test4.docx"
pdf_file_path = ".\data\\test.pdf"
# convert_doc_to_pdf(doc_file_path, pdf_file_path)
doc_to_pdf(doc_file_path, pdf_file_path)