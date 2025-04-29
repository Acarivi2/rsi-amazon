API_KEY = "bg_a878bdf1b9f00c81780d15e8ae22d121"
SECRET_KEY = "193159f95eb78f667e4d0ba84644ac55ad69909090e82958bde93df3aca9419b"
PASSWORD = '3948Bgy406'
TIMEFRAME = '1m'    # 3m, 5m
SOURCE = 'close'  # close

RSI_PERIOD = 7
RSI_UPPER = 75
RSI_LOWER = 25
ACTIVATE_LONG = True   # True: activa la apertura de ordenes LONG, False: desactiva la apertura de posiciones LONG
ACTIVATE_SHORT = True   # True: activa la apertura de ordenesSHORT, False: desactiva la apertura de posiciones SHORT
CLOSE_LONG = True   # True: activa el cierre de posiciones LONG, False: desactiva el cierre de posiciones LONG
CLOSE_SHORT = True   # True: activa el cierre de posiciones LONG, False: desactiva el cierre de posiciones SHORT


SYMBOLS = ['ADA/USDT:USDT']    # BTC/USDT:USDT, LTC/USDT:USDT
COST = [8] # Precio de compra de la primera orden
TRADE_COUNT_LIMIT = [0] #Cantidad de recompras, en 0 significa sin limite de recompras
STOPLOSS_PERCENT = [10]  # 2% == 2/100 ej 1 = 100% cuenta
INCREMENTAL_ORDER = True  # True/False means to not use incremental order
INCREMENTAL_PRICE_PERCENT_LONG = [0.05]     # 0.2%  set % value distancia entre recompras
INCREMENTAL_PRICE_PERCENT_SHORT = [0.05]     # 0.2%  set % value distancia entre recompras
INCREMENTAL_AMT_PERCENT_LONG = [2]     # 0.2%  set % value, va a sumar la recompra el monto minimo AMMOUNTS x INCREMENTAL_AMT_PERCENT
INCREMENTAL_AMT_PERCENT_SHORT = [2]     # 0.2%  set % value, va a sumar la recompra el monto minimo AMMOUNTS x INCREMENTAL_AMT_PERCENT
TAKEPROFIT_PERCENT = [0.005] # ej. 0.01 = 1% distancia activa trailing stop, barrera de activacion
BREAKEVEN_CLOSE = [0.003] # ej. 0.005 = 0.5% distancia a la que cierra la posicion luego de alcanzar el TP (distancia en % de retrocesos)
