from request_interface import get_private_result_or_none


def get_balance():
    return get_private_result_or_none('Balance')


def get_trade_balance(req={}):
    if not req.__contains__('asset'):
        req['asset']='ZEUR'
    bal = get_private_result_or_none('TradeBalance',req=req)
    if bal is not None:
        bal['ccy']=req['asset']
        return bal
    return None


def get_open_orders(req={}):
    return get_private_result_or_none('OpenOrders',req=req)


def get_closed_orders(req={}):
    return get_private_result_or_none('ClosedOrders',req=req)


def get_trades_history(req={}):
    return get_private_result_or_none('TradesHistory',req=req)


def add_market_order(pair,type,volume):
    req={'pair':pair,
         'type':type,
         'volume':volume,
         'ordertype':'market'
    }
    return add_order(req)


#handle errors for add order
def add_limit_order(pair,type,volume,price):
    req={'pair':pair,
         'type':type,
         'volume':volume,
         'ordertype':'limit',
         'price':price
    }
    return add_order(req)


def add_order(req={}):
    return get_private_result_or_none('AddOrder',req=req)


def cancel_order(txid):
    return get_private_result_or_none('CancelOrder', req={'txid':txid})


def get_total_pnl(bal):
    if not bal:
        return None
    else:
        return {'amount':bal['eb'],'ccy':bal['ccy']}