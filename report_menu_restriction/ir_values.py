from openerp.osv import osv

class ir_values(osv.osv):
    _inherit = "ir.values"
    
    #Overriding method
    def get_actions(self, cr, uid, action_slot, model, res_id=False, context=None):
        result=super(ir_values,self).get_actions(cr, uid, action_slot, model, res_id, context)
        
        if result and action_slot=='client_print_multi':
            tmp_result = []
            for ls in result:
                if ls[2]:
                    ls2 = ls[2]
                    if ls2.get('type',False)=='ir.actions.report.xml' and ls2.get('invisible',False):
                        if  not eval(ls2.get('invisible')):
                            tmp_result.append(ls)
#                         mod_obj = self.pool.get(ls2.get('model'))
#                         ids = mod_obj.search(cr, uid,eval('list('+ls2.get('domain')+')'))
#                         if ids:
#                             tmp_result.append(ls)
                    else:
                        tmp_result.append(ls)
                else:
                    tmp_result.append(ls)
                    
            result=tmp_result
        return result