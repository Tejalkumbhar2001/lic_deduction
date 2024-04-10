# Copyright (c) 2024, quantbit.erpdata.in and contributors
# For license information, please see license.txt
import frappe
from frappe import _, throw
from datetime import datetime
from frappe.utils import add_days, cint, cstr, date_diff, formatdate, getdate
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.utils import get_valid_serial_nos
from frappe.model.document import Document


class LICDeduction(Document):

	@frappe.whitelist()
	def generate_schedule(self):
		if self.docstatus != 0:
			return
		self.set("schedules", [])
		count = 1
		for d in self.get("items"):
			self.validate_maintenance_detail()
			s_list = []
			s_list = self.create_schedule_list(d.start_date, d.end_date, d.no_of_visits, d.sales_person)
			for i in range(d.no_of_visits):
				child = self.append("schedules")
				child.item_code = d.item_code
				child.item_name = d.item_name
				child.scheduled_date = s_list[i].strftime("%Y-%m-%d")
				if d.serial_no:
					child.serial_no = "Sales Team"
				child.idx = count
				count = count + 1
				# child.sales_person = d.sales_person
				child.completion_status = "Pending"
				child.item_reference = d.name

	@frappe.whitelist()
	def validate_end_date_visits(self):
		days_in_period = {"Weekly": 7, "Monthly": 30, "Quarterly": 91, "Half Yearly": 182, "Yearly": 365}
		for item in self.items:
			if item.periodicity and item.periodicity != "Random" and item.start_date:
				if not item.end_date:
					if item.no_of_visits:
						item.end_date = add_days(
							item.start_date, item.no_of_visits * days_in_period[item.periodicity]
						)
					else:
						item.end_date = add_days(item.start_date, days_in_period[item.periodicity])

				diff = date_diff(item.end_date, item.start_date) + 1
				no_of_visits = cint(diff / days_in_period[item.periodicity])

				if not item.no_of_visits or item.no_of_visits == 0:
					item.end_date = add_days(item.start_date, days_in_period[item.periodicity])
					diff = date_diff(item.end_date, item.start_date) + 1
					item.no_of_visits = cint(diff / days_in_period[item.periodicity])

				elif item.no_of_visits > no_of_visits:
					item.end_date = add_days(
						item.start_date, item.no_of_visits * days_in_period[item.periodicity]
					)

				elif item.no_of_visits < no_of_visits:
					item.end_date = add_days(
						item.start_date, item.no_of_visits * days_in_period[item.periodicity]
					)

	def on_submit(self):
		if not self.get("schedules"):
			throw(_("Please click on 'Generate Schedule' to get schedule"))
		self.check_serial_no_added()
		self.validate_schedule()
		# self.create_maintanance_orders()

		email_map = {}
		for d in self.get("items"):
			if d.serial_no:
				serial_nos = get_valid_serial_nos(d.serial_no)
				self.validate_serial_no(d.item_code, serial_nos, d.start_date)
				self.update_amc_date(serial_nos, d.end_date)

			# no_email_sp = []
			# if d.sales_person not in email_map:
			# 	sp = frappe.get_doc("Sales Person", d.sales_person)
			# 	try:
			# 		email_map[d.sales_person] = sp.get_email_id()
			# 	except frappe.ValidationError:
			# 		no_email_sp.append(d.sales_person)

			# if no_email_sp:
			# 	frappe.msgprint(
			# 		_(
			# 			"Setting Events to {0}, since the Employee attached to the below Sales Persons does not have a User ID{1}"
			# 		).format(self.owner, "<br>" + "<br>".join(no_email_sp))
			# 	)


	def create_schedule_list(self, start_date, end_date, no_of_visit, sales_person):
		schedule_list = []
		start_date_copy = start_date
		date_diff = (getdate(end_date) - getdate(start_date)).days
		add_by = date_diff / no_of_visit

		for visit in range(cint(no_of_visit)):
			if getdate(start_date_copy) < getdate(end_date):
				start_date_copy = add_days(start_date_copy, add_by)
				if len(schedule_list) < no_of_visit:
					schedule_date = self.validate_schedule_date_for_holiday_list(
						getdate(start_date_copy), sales_person
					)
					if schedule_date > getdate(end_date):
						schedule_date = getdate(end_date)
					schedule_list.append(schedule_date)

		return schedule_list

	def validate_schedule_date_for_holiday_list(self, schedule_date, sales_person):
		validated = False

		employee = frappe.db.get_value("Sales Person", sales_person, "employee")
		if employee:
			holiday_list = get_holiday_list_for_employee(employee)
		else:
			holiday_list = frappe.get_cached_value("Company", self.company, "default_holiday_list")

		holidays = frappe.db.sql_list(
			"""select holiday_date from `tabHoliday` where parent=%s""", holiday_list
		)

		if not validated and holidays:

			# max iterations = len(holidays)
			for i in range(len(holidays)):
				if schedule_date in holidays:
					schedule_date = add_days(schedule_date, -1)
				else:
					validated = True
					break

		return schedule_date

	def validate_dates_with_periodicity(self):
		for d in self.get("items"):
			if d.start_date and d.end_date and d.periodicity and d.periodicity != "Random":
				date_diff = (getdate(d.end_date) - getdate(d.start_date)).days + 1
				days_in_period = {
					"Weekly": 7,
					"Monthly": 30,
					"Quarterly": 90,
					"Half Yearly": 180,
					"Yearly": 365,
				}

				if date_diff < days_in_period[d.periodicity]:
					throw(
						_(
							"Row {0}: To set {1} periodicity, difference between from and to date must be greater than or equal to {2}"
						).format(d.idx, d.periodicity, days_in_period[d.periodicity])
					)

	def validate_maintenance_detail(self):
		if not self.get("items"):
			throw(_("Please enter Maintaince Details first"))

		for d in self.get("items"):
			if not d.item_code:
				throw(_("Please select item code"))
			elif not d.start_date or not d.end_date:
				throw(_("Please select Start Date and End Date for Item {0}").format(d.item_code))
			elif not d.no_of_visits:
				throw(_("Please mention no of visits required"))
			elif not d.sales_person:
				throw(_("Please select a Sales Person for item: {0}").format(d.item_name))

			if getdate(d.start_date) >= getdate(d.end_date):
				throw(_("Start date should be less than end date for Item {0}").format(d.item_code))

	def validate_sales_order(self):
		for d in self.get("items"):
			if d.sales_order:
				chk = frappe.db.sql(
					"""select ms.name from `tabLIC Deduction` ms,
					`tabInstallation` msi where msi.parent=ms.name and
					msi.sales_order=%s and ms.docstatus=1""",
					d.sales_order,
				)
				if chk:
					throw(_("Maintenance Schedule {0} exists against {1}").format(chk[0][0], d.sales_order))

	def validate_items_table_change(self):
		doc_before_save = self.get_doc_before_save()
		if not doc_before_save:
			return
		for prev_item, item in zip(doc_before_save.items, self.items):
			fields = [
				"item_code",
				"start_date",
				"end_date",
				"periodicity",
				"sales_person",
				"no_of_visits",
				"serial_no",
			]
			for field in fields:
				b_doc = prev_item.as_dict()
				doc = item.as_dict()
				if cstr(b_doc[field]) != cstr(doc[field]):
					return True

	def validate_no_of_visits(self):
		return len(self.schedules) != sum(d.no_of_visits for d in self.items)

	def validate(self):
		self.validate_end_date_visits()
		self.validate_maintenance_detail()
		self.validate_dates_with_periodicity()
		self.validate_sales_order()
		if not self.schedules or self.validate_items_table_change() or self.validate_no_of_visits():
			self.generate_schedule()

	# def on_update(self):
	# 	self.db_set("status", "Draft")

	def update_amc_date(self, serial_nos, amc_expiry_date=None):
		for serial_no in serial_nos:
			serial_no_doc = frappe.get_doc("Serial No", serial_no)
			serial_no_doc.amc_expiry_date = amc_expiry_date
			serial_no_doc.save()


	def validate_schedule(self):
		item_lst1 = []
		item_lst2 = []
		for d in self.get("items"):
			if d.item_code not in item_lst1:
				item_lst1.append(d.item_code)

		for m in self.get("schedules"):
			if m.item_code not in item_lst2:
				item_lst2.append(m.item_code)

		if len(item_lst1) != len(item_lst2):
			throw(
				_(
					"Maintenance Schedule is not generated for all the items. Please click on 'Generate Schedule'"
				)
			)
		else:
			for x in item_lst1:
				if x not in item_lst2:
					throw(_("Please click on 'Generate Schedule'"))

	def check_serial_no_added(self):
		serial_present = []
		for d in self.get("items"):
			if d.serial_no:
				serial_present.append(d.item_code)

		for m in self.get("schedules"):
			if serial_present:
				if m.item_code in serial_present and not m.serial_no:
					throw(
						_("Please click on 'Generate Schedule' to fetch Serial No added for Item {0}").format(
							m.item_code
						)
					)

	@frappe.whitelist()
	def get_pending_data(self, data_type, s_date=None, item_name=None):
		if data_type == "date":
			dates = ""
			for schedule in self.schedules:
				if schedule.item_name == item_name and schedule.completion_status == "Pending":
					dates = dates + "\n" + formatdate(schedule.scheduled_date, "dd-MM-yyyy")
			return dates
		elif data_type == "items":
			items = ""
			for item in self.items:
				for schedule in self.schedules:
					if item.item_name == schedule.item_name and schedule.completion_status == "Pending":
						items = items + "\n" + item.item_name
						break
			return items
		elif data_type == "id":
			for schedule in self.schedules:
				if schedule.item_name == item_name and s_date == formatdate(
					schedule.scheduled_date, "dd-mm-yyyy"
				):
					return schedule.name

	@frappe.whitelist()
	def set_reference(self):
		for i in self.get("items"):
			i.reference_id = i.name

	@frappe.whitelist()
	def checkall(self):
		for i in self.get("items"):
			children = self.get('schedules',{'reference_id':i.reference_id})
			if not children:
				return
			all_selected = all([child.disabled for child in children])  
			value = 0 if all_selected else 1 
			for child in children:
				child.disabled = value

	@frappe.whitelist()
	def cal_total_installment(self):
		for item in self.get("items"):
			if item.periodicity and item.start_date and item.end_date:
				start_date = frappe.utils.data.getdate(item.start_date)
				end_date = frappe.utils.data.getdate(item.end_date)
				total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
				if item.periodicity == "Monthly":
					total_installments = total_months / 1
				elif item.periodicity == "Quarterly":
					total_installments = total_months / 3
				elif item.periodicity == "Half Yearly":
					total_installments = total_months / 6
				elif item.periodicity == "Yearly":
					total_installments = total_months / 12
				else:
					total_installments = None
				
				item.no_of_visits = total_installments



@frappe.whitelist()
def cm():
	current_date = datetime.today().date()
	child_data = frappe.get_all("Policy Info Details",filters = {"disabled":0},fields=["name","disabled","end_date"],)
	if(child_data):
		for i in child_data:					
			end_date = frappe.utils.data.getdate(i.end_date)
			if (end_date - current_date).days == 0:
				frappe.db.set_value('Policy Info Details', i.name, 'disabled', 1)