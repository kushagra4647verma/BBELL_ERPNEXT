# purchase_fast_entry/overrides/purchase_invoice.py
#
# PURPOSE
# -------
# ERPNext standard behaviour credits the Supplier (credit_to) account with the
# full base_grand_total even when TDS deduction rows exist in the Taxes table.
# At the same time make_tax_gl_entries() posts a *credit* to the TDS Payable
# account for every "Deduct" row.  The result is that both the supplier ledger
# AND the TDS payable account are credited, overstating the total liability.
#
# CORRECT ACCOUNTING
# ------------------
# Suppose Invoice = 10 000, TDS = 1 000
#
#   Dr  Expense Account          10 000
#   Cr  Supplier (credit_to)      9 000   ← Grand Total MINUS TDS
#   Cr  TDS Payable               1 000
#   ─────────────────────────────────────
#       Debits == Credits        10 000
#
# This override adjusts ONLY make_supplier_gl_entry() so that the supplier
# credit is reduced by the sum of all "Deduct" tax rows whose category
# is "Total" or "Valuation and Total".
#
# Everything else (make_tax_gl_entries, make_item_gl_entries, etc.) is
# inherited unchanged from the standard PurchaseInvoice class.

import frappe
from frappe.utils import flt

from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


class CustomPurchaseInvoice(PurchaseInvoice):
    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _get_total_deductible_tax(self):
        """
        Return the sum of base_tax_amount_after_discount_amount for every
        tax row that:
          - has add_deduct_tax == "Deduct"
          - has category in ("Total", "Valuation and Total")

        These are the rows that create a credit on the TDS / deduction
        account in make_tax_gl_entries(), so we must reduce the supplier
        credit by the same amount to keep the entry balanced.

        Rows with category "Valuation" only affect stock valuation and do
        NOT produce a "Total" side GL entry, so they are intentionally
        excluded here.
        """
        total = 0.0
        for tax in self.get("taxes") or []:
            if (
                tax.add_deduct_tax == "Deduct"
                and tax.category in ("Total", "Valuation and Total")
            ):
                total += flt(
                    tax.base_tax_amount_after_discount_amount,
                    self.precision("base_grand_total"),
                )
        return total

    # ------------------------------------------------------------------
    # Core override
    # ------------------------------------------------------------------

    def make_supplier_gl_entry(self, gl_entries):
        """
        Identical to the standard implementation except that the credit
        amount posted to the Supplier account (credit_to) is reduced by
        the sum of all deductible tax rows (e.g. TDS).

        We temporarily patch self.grand_total / self.base_grand_total,
        call super(), then restore them so that nothing else in the
        document lifecycle is affected.
        """

        deductible_amount = self._get_total_deductible_tax()

        if not deductible_amount:
            # No deductions — behave exactly like standard ERPNext.
            super().make_supplier_gl_entry(gl_entries)
            return

        # ── Stash originals ──────────────────────────────────────────
        original_grand_total       = self.grand_total
        original_base_grand_total  = self.base_grand_total
        original_rounded_total     = self.rounded_total
        original_base_rounded_total = self.base_rounded_total
        original_rounding_adjustment      = self.rounding_adjustment
        original_base_rounding_adjustment = self.base_rounding_adjustment

        try:
            # ── Reduce totals by the deductible amount ───────────────
            # base_grand_total is used directly by super() for the credit
            # amount.  We also patch grand_total (foreign currency) by
            # the converted equivalent so the account-currency credit
            # remains consistent.
            precision = self.precision("base_grand_total")

            self.base_grand_total = flt(
                original_base_grand_total - deductible_amount, precision
            )

            # Convert deductible amount back to transaction currency for
            # the grand_total field.  conversion_rate is always >= 1 and
            # guaranteed to be set by the time GL entries are made.
            conversion_rate = flt(self.conversion_rate) or 1.0
            deductible_in_doc_currency = flt(
                deductible_amount / conversion_rate,
                self.precision("grand_total"),
            )
            self.grand_total = flt(
                original_grand_total - deductible_in_doc_currency,
                self.precision("grand_total"),
            )

            # rounded_total is used by super() when rounding_adjustment is
            # present.  Reduce it consistently; if the field was 0 / None
            # before, leave it alone so the condition inside super() still
            # picks base_grand_total.
            if original_rounded_total:
                self.rounded_total = flt(
                    original_rounded_total - deductible_in_doc_currency,
                    self.precision("rounded_total"),
                )
            if original_base_rounded_total:
                self.base_rounded_total = flt(
                    original_base_rounded_total - deductible_amount,
                    self.precision("base_rounded_total"),
                )

            # Rounding adjustment is cosmetic only — zero it so super()
            # doesn't try to add it back on top of the already-adjusted
            # figures.
            self.rounding_adjustment      = 0
            self.base_rounding_adjustment = 0

            # ── Delegate to standard logic ───────────────────────────
            super().make_supplier_gl_entry(gl_entries)

        finally:
            # ── Always restore originals ─────────────────────────────
            # This guarantees that totals shown on the document, used in
            # payment entries, and stored in the database are never
            # permanently altered by this override.
            self.grand_total                  = original_grand_total
            self.base_grand_total             = original_base_grand_total
            self.rounded_total                = original_rounded_total
            self.base_rounded_total           = original_base_rounded_total
            self.rounding_adjustment          = original_rounding_adjustment
            self.base_rounding_adjustment     = original_base_rounding_adjustment