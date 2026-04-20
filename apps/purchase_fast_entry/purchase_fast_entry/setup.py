# purchase_fast_entry/setup.py
#
# Run after app install OR manually:
#   bench --site <site> execute purchase_fast_entry.setup.create_custom_fields
#
# Creates all Custom Fields required by the amendment workflow and
# safe-field fast-edit feature on Purchase Invoice and Sales Invoice.
#
# Fields added
# ─────────────
# Both Purchase Invoice and Sales Invoice:
#   amendment_reason    Small Text   allow_on_submit=1  (stores amendment reason)
#   gst_period_locked   Check        allow_on_submit=1  (blocks further amendments)
#
# Purchase Invoice only (safe fields editable directly on submitted doc):
#   bill_no             already exists in standard — no change needed
#   bill_date           already exists in standard — no change needed
#   remarks             already exists in standard — no change needed
#
# These two new fields are the only schema changes needed.  All other
# "safe field" editing (bill_no, bill_date, remarks) is handled by setting
# allow_on_submit via Custom Field property override.

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_custom_fields_on_install():
    """Called from after_install hook in hooks.py (optional)."""
    create_custom_fields_now()


def create_custom_fields_now():
    """
    Idempotent — safe to run multiple times.
    Uses frappe's create_custom_fields utility which skips existing fields.
    """
    fields = {
        # ── Applies to both doctypes ────────────────────────────────────────
        "Purchase Invoice": _amendment_fields(),
        "Sales Invoice":    _amendment_fields(),
    }

    create_custom_fields(fields, ignore_validate=True)

    # ── Make standard fields allow_on_submit for Purchase Invoice ───────────
    # bill_no, bill_date, remarks already exist — just flip the flag.
    _set_allow_on_submit("Purchase Invoice", [
        "bill_no",
        "bill_date",
        "remarks",
        "letter_head",
    ])

    # ── Same for Sales Invoice ───────────────────────────────────────────────
    _set_allow_on_submit("Sales Invoice", [
        "po_no",
        "po_date",
        "remarks",
        "letter_head",
    ])

    frappe.db.commit()
    print("Custom fields created / verified successfully.")


def _amendment_fields():
    return [
        {
            "fieldname":    "amendment_section",
            "label":        "Amendment Details",
            "fieldtype":    "Section Break",
            "insert_after": "remarks",
            "collapsible":  1,
            "collapsible_depends_on": "amendment_reason",
        },
        {
            "fieldname":      "amendment_reason",
            "label":          "Amendment Reason",
            "fieldtype":      "Small Text",
            "insert_after":   "amendment_section",
            "allow_on_submit": 1,
            "read_only":      1,      # set by system, not editable by user
            "description":    "Automatically recorded when a document is amended.",
        },
        {
            "fieldname":      "gst_period_locked",
            "label":          "GST Period Locked",
            "fieldtype":      "Check",
            "insert_after":   "amendment_reason",
            "default":        "0",
            "allow_on_submit": 1,
            "read_only":      1,
            "description":    "When checked, this document cannot be amended. Set after GSTR3B filing.",
            "print_hide":     1,
        },
    ]


def _set_allow_on_submit(doctype, fieldnames):
    """
    For standard (non-custom) fields, update the allow_on_submit property
    via Property Setter so we don't touch ERPNext core files.
    """
    for fieldname in fieldnames:
        # Check field actually exists on the doctype
        if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
            continue

        setter_name = f"{doctype}-{fieldname}-allow_on_submit"

        if frappe.db.exists("Property Setter", setter_name):
            # Already set — update value in case it was changed
            frappe.db.set_value("Property Setter", setter_name, "value", "1")
        else:
            ps = frappe.get_doc({
                "doctype":       "Property Setter",
                "name":          setter_name,
                "doctype_or_field": "DocField",
                "doc_type":      doctype,
                "field_name":    fieldname,
                "property":      "allow_on_submit",
                "property_type": "Check",
                "value":         "1",
            })
            ps.insert(ignore_permissions=True)