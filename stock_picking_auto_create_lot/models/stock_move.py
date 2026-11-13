# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, Command
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends(
        "has_tracking",
        "picking_type_id.auto_create_lot",
        "product_id.auto_create_lot",
        "picking_type_id.use_existing_lots",
        "state",
    )
    def _compute_display_assign_serial(self):
        super()._compute_display_assign_serial()
        moves_not_display = self.filtered(
            lambda m: m.picking_type_id.auto_create_lot
            and (m.product_id.auto_create_lot or m.product_id.categ_id.auto_create_lot)
        )
        for move in moves_not_display:
            move.display_assign_serial = False
        return

    def _set_quantity_done_prepare_vals(self, qty):
        res = super()._set_quantity_done_prepare_vals(qty)
        if (
            self.state in ("partially_available", "assigned")
            and self.product_id.tracking != "none"
            and self.picking_type_id.auto_create_lot
            and (
                self.product_id.auto_create_lot
                or self.product_id.categ_id.auto_create_lot
            )
        ):
            total_qty = self.product_uom._compute_quantity(qty, self.product_id.uom_id, round=False)
            if float_compare(total_qty, 0, precision_rounding=self.product_id.uom_id.rounding) > 0:
                existing_mls = self.move_line_ids
                if existing_mls:
                    first_ml = existing_mls[0]
                    first_ml_qty = self.product_id.uom_id._compute_quantity(total_qty, first_ml.product_uom_id, round=False)
                    new_res = [Command.update(first_ml.id, {'quantity': first_ml_qty})]
                    for ml in existing_mls[1:]:
                        new_res.append(Command.delete(ml.id))
                    res = new_res
        return res
