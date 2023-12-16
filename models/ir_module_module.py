from odoo import models, _
from odoo.exceptions import UserError
from odoo.addons.base.models.ir_module import assert_log_admin_access, ACTION_DICT


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @assert_log_admin_access
    def button_upgrade(self):
        """
        OVERRIDE
        Added skipping of dependent modules if there is a skip_dependent_modules in the context.
        """
        Dependency = self.env['ir.module.module.dependency']
        self.update_list()

        todo = list(self)
        i = 0
        while i < len(todo):
            module = todo[i]
            i += 1
            if module.state not in ('installed', 'to upgrade'):
                raise UserError(_("Can not upgrade module '%s'. It is not installed.") % (module.name,))
            self.check_external_dependencies(module.name, 'to upgrade')
            # Original code end
            if self.env.context.get("skip_dependent_modules"):
                continue
            # Original code start
            for dep in Dependency.search([('name', '=', module.name)]):
                if dep.module_id.state == 'installed' and dep.module_id not in todo:
                    todo.append(dep.module_id)

        self.browse(module.id for module in todo).write({'state': 'to upgrade'})

        to_install = []
        for module in todo:
            for dep in module.dependencies_id:
                if dep.state == 'unknown':
                    raise UserError(_('You try to upgrade the module %s that depends on the module: %s.\nBut this module is not available in your system.') % (module.name, dep.name,))
                if dep.state == 'uninstalled':
                    to_install += self.search([('name', '=', dep.name)]).ids

        self.browse(to_install).button_install()
        return dict(ACTION_DICT, name=_('Apply Schedule Upgrade'))
