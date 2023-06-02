import os
import win32com.client as win32

def convert_doc_to_pdf(doc_file_path, pdf_file_path):
    word_app = win32.gencache.EnsureDispatch("Word.Application")
    doc = word_app.Documents.Open(doc_file_path)
    doc.SaveAs(pdf_file_path, FileFormat=17)  # FileFormat=17 specifies PDF format
    doc.Close()
    word_app.Quit()

# Usage example
doc_file_path = ".\data\\סיכום מצגת 4.docx"
pdf_file_path = ".\@experimtnes\סיכום מצגת 4.docx.pdf"
convert_doc_to_pdf(doc_file_path, pdf_file_path)