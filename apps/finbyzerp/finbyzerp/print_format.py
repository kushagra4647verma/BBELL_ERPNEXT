from __future__ import unicode_literals

import pdfkit, os, frappe, io
from frappe.utils import scrub_urls
from frappe import _
from PyPDF2 import PdfReader, PdfWriter
from frappe.utils.pdf import get_wkhtmltopdf_version,get_file_data_from_writer,get_cookie_options,cleanup, read_options_from_html


PDF_CONTENT_ERRORS = ["ContentNotFoundError", "ContentOperationNotPermittedError",
	"UnknownContentError", "RemoteHostClosedError"]

@frappe.whitelist()
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0):
	html = frappe.get_print(doctype, name, format, doc=doc, no_letterhead=no_letterhead)
	frappe.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = get_pdf(html)
	frappe.local.response.type = "pdf"

def get_pdf(html, options=None, output=None):
	html = scrub_urls(html)
	html, options = prepare_options(html, options)

	options.update({
		"disable-javascript": "",
		"disable-local-file-access": ""
	})

	filedata = ''
	if get_wkhtmltopdf_version() > '0.12.3':
		options.update({"disable-smart-shrinking": ""})

	try:
		filedata = pdfkit.from_string(html, False, options=options or {})
		reader = PdfReader(io.BytesIO(filedata))
	except OSError as e:
		if any([error in str(e) for error in PDF_CONTENT_ERRORS]):
			if not filedata:
				frappe.throw(_("PDF generation failed because of broken image links"))

			if output:
				output.append(reader)
		else:
			raise
	finally:
		cleanup(options)

	if "password" in options:
		password = options["password"]

	if output:
		output.append(reader)
		return output

	writer = PdfWriter()
	writer.append(reader)

	if "password" in options:
		writer.encrypt(password)

	filedata = get_file_data_from_writer(writer)

	return filedata

def prepare_options(html, options):
	if not options:
		options = {}

	options.update({
		'print-media-type': None,
		'background': None,
		'images': None,
		'quiet': None,
		# 'no-outline': None,
		'encoding': "UTF-8",
		#'load-error-handling': 'ignore'
	})

	if not options.get("margin-right"):
		options['margin-right'] = '8mm'

	if not options.get("margin-left"):
		options['margin-left'] = '8mm'

	html, html_options = read_options_from_html(html)
	options.update(html_options or {})

	# # cookies
	# if frappe.session and frappe.session.sid:
	# 	options['cookie'] = [('sid', '{0}'.format(frappe.session.sid))]

	options.update(get_cookie_options())

	# page size
	if not options.get("page-size"):
		options['page-size'] = frappe.db.get_single_value("Print Settings", "pdf_page_size") or "A4"

	return html, options