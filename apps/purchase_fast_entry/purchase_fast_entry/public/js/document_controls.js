// purchase_fast_entry/public/js/document_controls.js
//
// PURPOSE
// -------
// Implements three visible document modes for Purchase Invoice and
// Sales Invoice:
//
//   CREATE  — docstatus 0 (Draft).  Standard Frappe form, fully editable.
//             No changes needed here.
//
//   DISPLAY — docstatus 1 (Submitted).  Standard Frappe read-only view.
//             We add:
//               • A clear "SUBMITTED — Read Only" mode indicator banner.
//               • An "Edit Document" button (Accounts Manager only) that
//                 opens the amendment dialog.
//               • A "Lock GST Period" button (System Manager only).
//               • If an open amendment draft already exists, a button
//                 "Open Existing Amendment" instead.
//
//   EDIT    — The amendment draft (docstatus 0, amended_from set).
//             We add:
//               • A yellow "AMENDMENT DRAFT" banner showing what is
//                 being amended.
//               • The amendment_reason is shown prominently.
//               • Standard Save / Submit workflow applies.
//
// NO in-place editing of GL-posted data is ever done.  All accounting
// corrections go through the amendment → cancel → re-post flow.

// ─── Constants ───────────────────────────────────────────────────────────────

const AMENDMENT_DOCTYPES = ["Purchase Invoice", "Sales Invoice"];

// ─── Mode banner ─────────────────────────────────────────────────────────────

function _remove_banner(frm) {
  frm.layout.$wrapper.find("#doc-mode-banner").remove();
}

function _show_banner(frm, html) {
  _remove_banner(frm);
  frm.layout.$wrapper
    .find(".form-page")
    .prepend(`<div id="doc-mode-banner">${html}</div>`);
}

function show_display_banner(frm) {
  _show_banner(
    frm,
    `
        <div style="
            padding: 8px 16px;
            background: #e8f4fd;
            border-bottom: 2px solid #2e75b6;
            display: flex; align-items: center; gap: 10px;
            font-size: 13px; color: #1f4e79; font-weight: 600;">
            <i class="fa fa-lock"></i>
            ${__(
              "DISPLAY MODE — This document is submitted and read-only. " +
                'Use "Edit Document" in the Actions menu to create an amendment.',
            )}
        </div>`,
  );
}

function show_amendment_banner(frm) {
  const amended_from = frm.doc.amended_from;
  const reason = frm.doc.amendment_reason || __("No reason recorded");
  _show_banner(
    frm,
    `
        <div style="
            padding: 10px 16px;
            background: #fff8e1;
            border-bottom: 2px solid #ff8c00;
            font-size: 13px; color: #5d4037;">
            <div style="font-weight:700; margin-bottom:4px;">
                <i class="fa fa-pencil-square-o" style="color:#ff8c00;"></i>
                &nbsp;${__("EDIT MODE — Amendment Draft")}
            </div>
            <div>
                ${__("Amending")}: <a href="/app/${_doctype_slug(frm.doc.doctype)}/${encodeURIComponent(amended_from)}"
                    style="font-weight:600;">${frappe.utils.escape_html(amended_from)}</a>
            </div>
            <div style="margin-top:4px; color:#795548;">
                ${__("Reason")}: ${frappe.utils.escape_html(reason)}
            </div>
        </div>`,
  );
}

function _doctype_slug(doctype) {
  // "Purchase Invoice" → "purchase-invoice"
  return doctype.toLowerCase().replace(/ /g, "-");
}

// ─── Amendment dialog ─────────────────────────────────────────────────────────

/**
 * Show the "Edit Document" dialog asking for a reason, then call the
 * backend to cancel + create amendment.
 */
function open_amendment_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Edit Document — Create Amendment"),
    fields: [
      {
        fieldtype: "HTML",
        fieldname: "info_html",
        options: `
                    <div style="
                        padding: 10px 14px; margin-bottom: 10px;
                        background: #fff3cd; border-radius: 4px;
                        font-size: 13px; color: #856404;">
                        <i class="fa fa-exclamation-triangle"></i>
                        <b>${__("How this works:")}</b><br>
                        ${__(
                          "The current submitted document will be <b>cancelled</b>. " +
                            "A new editable draft (amendment) will be created. " +
                            "GL entries will be reversed and re-posted when you submit the amendment.",
                        )}
                    </div>`,
      },
      {
        fieldtype: "Small Text",
        fieldname: "reason",
        label: __("Reason for Amendment"),
        reqd: 1,
        description: __(
          "This will be recorded on the document for audit purposes.",
        ),
      },
    ],
    primary_action_label: __("Create Amendment"),
    primary_action(values) {
      if (!values.reason || !values.reason.trim()) {
        frappe.msgprint(__("Please enter a reason for the amendment."));
        return;
      }

      dialog.hide();
      frappe.show_progress(__("Creating amendment…"), 50, 100);

      frappe.call({
        method: "purchase_fast_entry.amendment_utils.request_amendment",
        args: {
          doctype: frm.doc.doctype,
          docname: frm.doc.name,
          reason: values.reason.trim(),
        },
        always() {
          frappe.hide_progress();
        },
        callback(r) {
          if (r.exc) return;
          const amendment_name = r.message.amendment_name;

          frappe.show_alert({
            message: __("Amendment created: {0}", [amendment_name]),
            indicator: "green",
          });

          // Navigate to the new amendment draft
          frappe.set_route("Form", frm.doc.doctype, amendment_name);
        },
      });
    },
    secondary_action_label: __("Cancel"),
    secondary_action() {
      dialog.hide();
    },
  });

  dialog.show();
}

// ─── Lock GST Period dialog ───────────────────────────────────────────────────

function open_lock_dialog(frm) {
  frappe.confirm(
    __(
      "Lock the GST period for <b>{0}</b>? " +
        "This will prevent any further amendments to this document. " +
        "This action cannot be undone.",
      [frm.doc.name],
    ),
    () => {
      frappe.call({
        method: "purchase_fast_entry.amendment_utils.lock_gst_period",
        args: { doctype: frm.doc.doctype, docname: frm.doc.name },
        callback(r) {
          if (r.exc) return;
          frappe.show_alert({
            message: __("GST period locked."),
            indicator: "orange",
          });
          frm.reload_doc();
        },
      });
    },
  );
}

// ─── Button builder ───────────────────────────────────────────────────────────

/**
 * Query the server for amendment status and render the correct buttons.
 * Called on every refresh of a submitted document.
 */
function setup_submitted_doc_buttons(frm) {
  frappe.call({
    method: "purchase_fast_entry.amendment_utils.get_amendment_status",
    args: { doctype: frm.doc.doctype, docname: frm.doc.name },
    callback(r) {
      if (!r.message) return;
      const s = r.message;

      // ── Open Amendment (if one already exists) ──────────────────────
      if (s.has_open_amendment) {
        frm.add_custom_button(
          __("Open Existing Amendment"),
          () => frappe.set_route("Form", frm.doc.doctype, s.open_amendment),
          __("Actions"),
        );
        // Show a banner explaining situation
        _show_banner(
          frm,
          `
                    <div style="
                        padding: 8px 16px; background: #fff3cd;
                        border-bottom: 2px solid #ff8c00;
                        font-size: 13px; color: #856404;">
                        <i class="fa fa-exclamation-triangle"></i>
                        ${__("An amendment draft already exists for this document.")}&nbsp;
                        <a href="/app/${_doctype_slug(frm.doc.doctype)}/${encodeURIComponent(s.open_amendment)}"
                           style="font-weight:600;">${frappe.utils.escape_html(s.open_amendment)}</a>
                    </div>`,
        );
        return;
      }

      // ── Normal display mode ─────────────────────────────────────────
      show_display_banner(frm);

      if (s.gst_period_locked) {
        // Show a locked indicator — no edit button
        _show_banner(
          frm,
          `
                    <div style="
                        padding: 8px 16px; background: #f8d7da;
                        border-bottom: 2px solid #c00000;
                        font-size: 13px; color: #721c24; font-weight: 600;">
                        <i class="fa fa-ban"></i>
                        ${__("GST PERIOD LOCKED — This document cannot be amended.")}
                    </div>`,
        );
        return;
      }

      if (s.can_amend) {
        frm.add_custom_button(
          __("Edit Document"),
          () => open_amendment_dialog(frm),
          __("Actions"),
        );
      }

      // System Manager gets the lock button
      if (frappe.user_roles.includes("System Manager")) {
        frm.add_custom_button(
          __("Lock GST Period"),
          () => open_lock_dialog(frm),
          __("Actions"),
        );
      }
    },
  });
}

// ─── Form hooks ───────────────────────────────────────────────────────────────

/**
 * Shared refresh logic applied to both Purchase Invoice and Sales Invoice.
 */
function on_invoice_refresh(frm) {
  if (!AMENDMENT_DOCTYPES.includes(frm.doc.doctype)) return;

  _remove_banner(frm);

  if (frm.doc.docstatus === 0 && frm.doc.amended_from) {
    // ── EDIT mode (amendment draft) ─────────────────────────────────────
    show_amendment_banner(frm);
    return;
  }

  if (frm.doc.docstatus === 0 && !frm.doc.amended_from) {
    // ── CREATE mode (new draft) ─────────────────────────────────────────
    // No banner needed — standard Frappe form is already correct
    return;
  }

  if (frm.doc.docstatus === 1) {
    // ── DISPLAY mode (submitted) ────────────────────────────────────────
    setup_submitted_doc_buttons(frm);
    return;
  }

  if (frm.doc.docstatus === 2) {
    // Cancelled — show minimal info only
    _show_banner(
      frm,
      `
            <div style="
                padding: 8px 16px; background: #f8d7da;
                border-bottom: 2px solid #c00000;
                font-size: 13px; color: #721c24; font-weight: 600;">
                <i class="fa fa-times-circle"></i>
                ${__("CANCELLED")}
                ${
                  frm.doc.amended_from
                    ? " — " + __("Replaced by amendment")
                    : ""
                }
            </div>`,
    );
  }
}

// ─── Register on both doctypes ────────────────────────────────────────────────

frappe.ui.form.on("Purchase Invoice", {
  refresh(frm) {
    on_invoice_refresh(frm);
  },
});

frappe.ui.form.on("Sales Invoice", {
  refresh(frm) {
    on_invoice_refresh(frm);
  },
});
