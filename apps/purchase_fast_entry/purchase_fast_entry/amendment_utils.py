# purchase_fast_entry/amendment_utils.py
#
# PURPOSE
# -------
# Implements the three-mode document lifecycle for Purchase Invoice
# and Sales Invoice:
#
#   CREATE  → docstatus = 0 (Draft)     — normal Frappe behaviour
#   EDIT    → controlled amendment      — this module
#   DISPLAY → docstatus = 1 (Submitted) — normal Frappe behaviour
#
# DESIGN
# ------
# Frappe does not support in-place editing of submitted documents because
# GL Entries, Stock Ledger Entries, and Payment Ledger Entries are already
# posted.  Allowing raw field edits would silently corrupt accounting data.
#
# The correct approach — used here — is:
#   1. User clicks "Edit" on a submitted invoice.
#   2. System cancels the original and creates an amendment (docstatus=0)
#      linked via `amended_from`.
#   3. User edits the amendment draft freely.
#   4. User submits the amendment.  GL entries are re-posted correctly.
#
# SAFE-FIELD FAST-EDIT (no amendment needed)
# ------------------------------------------
# Some fields do not affect accounting and can be changed on a submitted
# document directly via `allow_on_submit`.  These are handled by
# Custom Fields (created in setup.py) and do NOT go through this module.
# Examples: bill_no, bill_date, remarks, letter_head.
#
# GUARDS
# ------
# - Only Accounts Manager / System Manager may initiate an amendment.
# - Amendment is blocked if the GST period is already filed
#   (custom field `gst_period_locked = 1` on the invoice).
# - The reason for amendment is mandatory and stored on the new draft.

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import nowdate


# ---------------------------------------------------------------------------
# Roles allowed to trigger amendments
# ---------------------------------------------------------------------------

ALLOWED_ROLES = {"Accounts Manager", "System Manager"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def request_amendment(doctype, docname, reason):
    """
    Cancel the submitted document and create an amendment draft.

    Parameters
    ----------
    doctype : str   "Purchase Invoice" or "Sales Invoice"
    docname : str   Name of the submitted document
    reason  : str   Mandatory reason recorded on the new draft

    Returns
    -------
    dict  { "amendment_name": str }   Name of the newly created draft
    """
    _assert_role()
    _validate_doctype(doctype)

    doc = frappe.get_doc(doctype, docname)

    if doc.docstatus != 1:
        frappe.throw(_("Only submitted documents can be amended."))

    if doc.get("gst_period_locked"):
        frappe.throw(
            _("Cannot amend {0} {1}: the GST period for this document has been locked.").format(
                doctype, docname
            )
        )

    if not reason or not str(reason).strip():
        frappe.throw(_("Amendment reason is mandatory."))

    # ── Cancel original ──────────────────────────────────────────────────────
    doc.cancel()
    frappe.db.commit()        # commit cancel before creating amendment

    # ── Create amendment ─────────────────────────────────────────────────────
    amendment = _make_amendment(doc, reason.strip())
    amendment.insert(ignore_permissions=False)
    frappe.db.commit()

    # ── Log comment on the original (now cancelled) document ─────────────────
    original = frappe.get_doc(doctype, docname)
    original.add_comment(
        "Comment",
        _("Document cancelled and amended by {user} on {date}. "
          "Amendment: {amend}. Reason: {reason}").format(
            user   = frappe.session.user,
            date   = nowdate(),
            amend  = amendment.name,
            reason = reason.strip(),
        ),
    )

    return {"amendment_name": amendment.name}


@frappe.whitelist()
def get_amendment_status(doctype, docname):
    """
    Return information the JS needs to decide which buttons to show.

    Returns
    -------
    dict  {
        "can_amend"        : bool,   # user has role + period not locked
        "gst_period_locked": bool,
        "has_open_amendment": bool,  # an amendment draft already exists
        "open_amendment"   : str | None,
    }
    """
    _validate_doctype(doctype)
    frappe.has_permission(doctype, doc=docname, throw=True)

    doc = frappe.get_doc(doctype, docname)

    user_roles         = set(frappe.get_roles(frappe.session.user))
    has_role           = bool(ALLOWED_ROLES & user_roles)
    gst_locked         = bool(doc.get("gst_period_locked"))

    # Check whether an amendment draft already exists for this document
    open_amendment = frappe.db.get_value(
        doctype,
        {"amended_from": docname, "docstatus": 0},
        "name",
    )

    return {
        "can_amend":          has_role and not gst_locked,
        "gst_period_locked":  gst_locked,
        "has_open_amendment": bool(open_amendment),
        "open_amendment":     open_amendment,
    }


@frappe.whitelist()
def lock_gst_period(doctype, docname):
    """
    Mark a document's GST period as locked so it can no longer be amended.
    Only System Manager can do this.

    Used after GSTR3B is filed for the period.
    """
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Only System Manager can lock the GST period."), frappe.PermissionError)

    _validate_doctype(doctype)
    frappe.db.set_value(doctype, docname, "gst_period_locked", 1)
    frappe.get_doc(doctype, docname).add_comment(
        "Comment",
        _("GST period locked by {user} on {date}. Document can no longer be amended.").format(
            user=frappe.session.user, date=nowdate()
        ),
    )
    return {"success": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assert_role():
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not (ALLOWED_ROLES & user_roles):
        frappe.throw(
            _("Only Accounts Manager or System Manager can amend submitted documents."),
            frappe.PermissionError,
        )


def _validate_doctype(doctype):
    if doctype not in ("Purchase Invoice", "Sales Invoice"):
        frappe.throw(_("Amendment is only supported for Purchase Invoice and Sales Invoice."))


def _make_amendment(original_doc, reason):
    """
    Build a new draft document that is a copy of the original with:
      - docstatus = 0
      - amended_from = original name
      - name         = auto (new naming series)
      - amendment_reason = reason
      - gst_period_locked = 0
    """
    amendment = frappe.copy_doc(original_doc)
    amendment.docstatus       = 0
    amendment.amended_from    = original_doc.name
    amendment.amendment_reason = reason
    amendment.gst_period_locked = 0

    # Clear fields that must not be copied
    for f in ("irn", "ewaybill", "irn_cancelled", "ack_no", "ack_date"):
        if amendment.meta.has_field(f):
            amendment.set(f, None)

    # Reset status to Draft
    amendment.status = "Draft"

    return amendment