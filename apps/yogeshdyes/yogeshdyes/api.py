from __future__ import unicode_literals

import frappe
import frappe.defaults
from frappe import _
from frappe import msgprint, _
from frappe.utils import nowdate, flt, cint, cstr,now_datetime,getdate, add_days, add_months, get_last_day
from email.utils import formataddr

def validate_user_permission(self,method):
	if self.user == frappe.session.user:
		frappe.throw("You cannot change permission for your own user id")
	

def execute_fun():
	frappe.get_doc("Purchase Receipt","PREBIL20-2100044").submit()

def pi_on_submit(self,method):
	validate_gst_state_code(self)

def validate_gst_state_code(self):
	gst_accounts = frappe.get_all("GST Account",
		filters={"company":self.company,"is_reverse_charge_account":1 if self.get('reverse_charge') == "Y" else 0 },
		fields=["cgst_account", "sgst_account", "igst_account"])

	if self.taxes:
		account_heads = [t.account_head for t in self.taxes]
		if self.supplier_gstin and self.company_gstin:
			if self.supplier_gstin[0:2] == self.company_gstin[0:2]:
				if gst_accounts[0].cgst_account not in account_heads:
					frappe.msgprint("CGST Account doesn't exists in taxes")
				if gst_accounts[0].sgst_account not in account_heads:
					frappe.msgprint("SGST Account doesn't exists in taxes")
			elif self.supplier_gstin[0:2] != self.company_gstin[0:2]:
				if gst_accounts[0].igst_account not in account_heads:
					frappe.msgprint("IGST Account doesn't exists in taxes")				

def pi_validate(self,method):
	validate_company_gstin(self)

def validate_company_gstin(self):
	if self.billing_address:
		billing_gstin = frappe.db.get_value("Address",{"name":self.billing_address,"is_your_company_address":1},"gstin")
		if billing_gstin and self.company_gstin != billing_gstin:
			self.company_gstin = billing_gstin


def si_before_save(self,method):
	fob_calculation(self)

def si_on_update(self,method):
	total_pallets = 0

	for d in self.items:
		total_pallets += flt(d.total_pallets)
	
	self.pallet_weight=total_pallets
	self.total_net_weight = self.total_qty

def fob_calculation(self):
	for d in self.items:
		d.freight_inr = flt(d.freight * self.conversion_rate)
		d.insurance_inr = flt(d.insurance * self.conversion_rate)
		d.fob_value  = flt(d.base_amount - d.freight_inr - d.insurance_inr )

@frappe.whitelist()
def sales_invoice_mails():
	if getdate().weekday() == 6:
		enqueue(send_sales_invoice_mails, queue='long', timeout=5000, job_name='Payment Reminder Mails')
		return "Payment Reminder Mails Send"

@frappe.whitelist()
def send_sales_invoice_mails():
	from frappe.utils import fmt_money

	# def show_progress(status, customer, invoice):
	# 	frappe.publish_realtime(event="cities_progress", message={'status': status, 'customer': customer, 'invoice': invoice}, user=frappe.session.user)

	def header(customer):
		return """<strong>""" + customer + """</strong><br><br>Dear Sir,<br><br>
		Kind attention from account department.<br>
		We wish to invite your kind immediate attention to our following bill/s which have remained unpaid till date and are overdue for payment.<br>
		<div align="center">
			<table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead>
					<tr>
						<th width="20%" valign="top">Invoice No</th>
						<th width="20%" valign="top">Invoice Date</th>
						<th width="20%" valign="top">Net Total</th>
						<th width="20%" valign="top">Total Amount</th>
						<th width="20%" valign="top">Outstanding Amount</th>
					</tr></thead><tbody>"""

	def table_content(name, posting_date, net_total, rounded_total, outstanding_amount):
		posting_date = posting_date.strftime("%d-%m-%Y") if bool(posting_date) else '-'

		rounded_total = fmt_money(rounded_total, 2, 'INR')
		net_total = fmt_money(net_total, 2, 'INR')
		outstanding_amount = fmt_money(outstanding_amount, 2, 'INR')

		return """<tr>
				<td width="20%" valign="top" align="center"> {0} </td>
				<td width="20%" valign="top" align="center"> {1} </td>
				<td width="20%" valign="top" align="right"> {2} </td>
				<td width="20%" valign="top" align="right"> {3} </td>
				<td width="20%" valign="top" align="right"> {4} </td>
			</tr>""".format(name, posting_date, net_total, rounded_total,outstanding_amount)
	
	def footer(net_amount,actual_amount, outstanding_amount):
		net_amt = fmt_money(sum(net_amount), 2, 'INR')
		actual_amt = fmt_money(sum(actual_amount), 2, 'INR')
		outstanding_amt = fmt_money(sum(outstanding_amount), 2, 'INR')
		return """<tr>
					<td width="40%" colspan="2" valign="top" align="right">
						<strong>Net Receivable &nbsp; </strong>
					</td>
					<td align="right" width="20%" valign="top">
						<strong> {} </strong>
					</td>
					<td align="right" width="20%" valign="top">
						<strong> {} </strong>
					</td>
					<td align="right" width="20%" valign="top">
						<strong> {} </strong>
					</td>
				</tr></tbody></table></div><br>
				Request you to release the payment at earliest. <br><br>
				If you need any clarifications for any of above invoices, please reach out to our Accounts Team by sending email to admin@bbell.in <br><br>
				We will appreciate your immediate response in this regard.<br><br>
				If payment already made from your end, kindly provide details of the payment/s made to enable us to reconcile and credit your account.<br><br>

				""".format(net_amt,actual_amt, outstanding_amt)

	non_customers = ()
	data = frappe.get_list("Sales Invoice", filters={
			'status': ['in', ('Overdue')],
			'due_date': ("<=", nowdate()),
			'currency': 'INR',
			# 'docstatus': 1,
			# 'dont_send_email': 0,
			'customer': ['not in', non_customers],
			'company': 'BBELL INDUSTRY LLP'},
			order_by='posting_date',
			fields=["name", "customer", "posting_date","net_total", "rounded_total", "total_advance", "contact_email", "naming_series"])

	def get_customers():
		customers_list = list(set([d.customer for d in data if d.customer]))
		customers_list.sort()

		for customer in customers_list:
			yield customer

	def get_customer_si(customer):
		for d in data:
			if d.customer == customer:
				yield d

	cnt = 0
	customers = get_customers()

	sender = formataddr(("BBELL INDUSTRY LLP", "admin@bbell.in"))
	for customer in customers:
		attachments, outstanding, actual_amount, net_amount, recipients = [], [], [], [], []
		table = ''

		# customer_si = [d for d in data if d.customer == customer]
		customer_si = get_customer_si(customer)

		for si in customer_si:
			# show_progress('In Progress', customer, si.name)
			name = "Previous Year Outstanding"
			if si.naming_series != "OSINV-":
				name = si.name
				try:
					attachments.append(frappe.attach_print('Sales Invoice', si.name, print_format="", print_letterhead=True))
				except:
					pass

			table += table_content(name, si.posting_date, si.net_total,
						si.rounded_total, (si.rounded_total-si.total_advance))

			outstanding.append((si.rounded_total-si.total_advance))
			actual_amount.append(si.rounded_total or 0.0)
			net_amount.append(si.net_total or 0.0)

			# if bool(si.contact_email) and si.contact_email not in recipients:
			# 	recipients.append(si.contact_email)

			if bool(si.store_person_email_id) and si.store_person_email_id not in recipients:
				recipients.append(si.store_person_email_id)

			if bool(si.user_email_id) and si.user_email_id not in recipients:
				recipients.append(si.user_email_id)

		message = header(customer) + '' + table + '' + footer(net_amount,actual_amount, outstanding)
		# message += "<br><br>Recipients: " + ','.join(recipients)
		# recipients = ['kushal.chokshi@finbyz.tech','ravin.ramoliya@finbyz.tech']
		try:
			# frappe.sendmail(recipients='harshdeep.mehta@finbyz.tech',
			frappe.sendmail(
				recipients="admin@bbell.in",
				cc = 'admin@bbell.in',
				subject = 'Overdue Invoices: ' + customer,
				sender = sender,
				message = message,
				# attachments = attachments
			)
			
			cnt += 1
			show_progress('Mail Sent', customer, "All")
		except:
			frappe.log_error("Mail Sending Issue", frappe.get_traceback())
			continue
	# show_progress('Success', "All Mails Sent", str(cnt))
	# frappe.db.set_value("Cities", "CITY0001", "total", cnt)

def before_naming(self,method):
	if self.link_to =='Supplier':
		aliass = frappe.db.get_value('Supplier',self.party,'alias')
		if aliass:
			self.party_alias = aliass
		else: self.party_alias = self.party
	if self.link_to =='Customer':
		aliass = frappe.db.get_value('Customer',self.party,'alias')
		if aliass:
			self.party_alias = aliass
		else: self.party_alias = self.party